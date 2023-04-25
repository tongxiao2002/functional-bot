'''
@Author: tongxiao
@FileName: event_handler.py
@CreateTime: 2023-04-21 00:21:09
@Description:

'''

import os
import re
import uuid
import json
import jionlp
from datetime import datetime, timedelta
from nonebot.log import logger
from nonebot.typing import T_State
from nonebot.params import CommandArg, ArgPlainText
from nonebot.matcher import Matcher
# from nonebot.adapters.console import Message, MessageSegment, Event
from nonebot.adapters.onebot.v11 import Message, MessageSegment, Event
from . import event_remind_config, event_cmd_group
from .config import TimeZoneConfig


event_rgst = event_cmd_group.command("register", aliases={'注册事件'})
datetime_format = TimeZoneConfig.datetime_format


def timestr_preprocess(timestr: str):
    """
    时间字符串预处理
    """
    # 删除空白
    ptn = re.compile(r'\s+')
    timestr = re.sub(ptn, '', timestr)
    # 允许 "提前5分钟" 这种输入
    if timestr.startswith('提前'):
        timestr = timestr[2:]
    return timestr


def timestr_to_datetime(timestr: str, time_type: str = "time_point"):
    # 服务器时间落后北京时间 8 小时
    now = datetime.now(tz=TimeZoneConfig.local_time_zone)
    now = now.astimezone(tz=TimeZoneConfig.dest_time_zone)
    try:
        timestr = timestr_preprocess(timestr)
        time = jionlp.parse_time(timestr, time_base=now, time_type=time_type)
    except Exception as e:
        logger.error(e)
        raise

    if time_type == 'time_point':
        assert time['definition'] == 'accurate'
        dt = datetime.strptime(time['time'][0], "%Y-%m-%d %H:%M:%S")
        return dt
    elif time_type == 'time_delta':
        new_time = {k + 's': v for k, v in time['time'].items()}
        delta_time = timedelta(**new_time)
        return delta_time
    else:
        raise NotImplementedError


# handlers
@event_rgst.handle()
async def register_event(matcher: Matcher, args: Message = CommandArg()):
    if args.extract_plain_text():
        matcher.set_arg('event_content', args)
    else:
        reply_msg = Message([
            MessageSegment.text("请问您需要我提醒您的事件是什么呢？"),
        ])
        await event_rgst.send(reply_msg)


@event_rgst.got('event_content')
async def get_event_content(state: T_State, event_content: str = ArgPlainText()):
    state['event_content'] = event_content
    reply_msg = Message([
        MessageSegment.text(f"收到！事件为 {event_content}."),
    ])
    await event_rgst.send(reply_msg)


@event_rgst.got('event_time_str', prompt="请问事件什么时候发生呢？（描述太过模糊可能会解析失败哦）")
async def get_timing_and_finish(state: T_State, event_time_str: str = ArgPlainText()):
    state['try_count'] = state.get('try_count', 0)
    try:
        event_time = timestr_to_datetime(event_time_str)
    except Exception as e:
        logger.warning(e)
        state['try_count'] += 1
        if state['try_count'] < event_remind_config.max_try_count:
            chances = event_remind_config.max_try_count - state['try_count']
            reject_msg = Message([
                MessageSegment.text(f"时间 '{event_time_str}' 解析失败！请重新输入时间。\n"),
                MessageSegment.text(f"示例：明天下午5点，2小时后，9号上午10点。\n"),
                MessageSegment.text(f"您还有 {chances} 次输入机会。"),
            ])
            await event_rgst.reject(reject_msg)
        else:
            reject_msg = Message([
                MessageSegment.text("时间输入错误次数过多，已终止会话。")
            ])
            await event_rgst.finish(reject_msg)

    event_time = event_time.replace(second=0, microsecond=0)
    state['event_time'] = event_time
    event_time_str = datetime.strftime(event_time, datetime_format)

    state['try_count'] = 0
    reply_msg = Message([
        MessageSegment.text(f"好的，事件 {state['event_content']} 将于 {event_time_str} 时发生."),
    ])
    await event_rgst.send(reply_msg)


@event_rgst.got('lead_time_str', prompt=f"您需要我提前多久提醒您呢？（描述太过模糊可能会解析失败哦）")
async def get_lead_time_and_finish(event: Event, state: T_State, lead_time_str: str = ArgPlainText()):
    state['try_count'] = state.get('try_count', 0)
    try:
        lead_time = timestr_to_datetime(lead_time_str, time_type='time_delta')
    except Exception as e:
        logger.warning(e)
        state['try_count'] += 1
        if state['try_count'] < event_remind_config.max_try_count:
            chances = event_remind_config.max_try_count - state['try_count']
            reject_msg = Message([
                MessageSegment.text(f"时间 '{lead_time_str}' 解析失败！请重新输入时间。\n"),
                MessageSegment.text(f"示例：1天，2小时，1个半小时，15分钟。\n"),
                MessageSegment.text(f"您还有 {chances} 次输入机会。"),
            ])
            await event_rgst.reject(reject_msg)
        else:
            reject_msg = Message([
                MessageSegment.text("时间输入错误次数过多，已终止会话。")
            ])
            await event_rgst.finish(reject_msg)

    lead_time = state['event_time'] - lead_time
    lead_time = lead_time.replace(second=0, microsecond=0)
    state['lead_time'] = lead_time

    event_time_str = datetime.strftime(state['event_time'], datetime_format)
    lead_time_str = datetime.strftime(lead_time, datetime_format)
    new_event = {
        str(uuid.uuid4()): {
            "event_content": state['event_content'],
            "event_time": datetime.strftime(state['event_time'], datetime_format),
            "lead_time": datetime.strftime(lead_time, datetime_format),
            "remind_type": "qq"
        }
    }

    # save event to disk
    # load current events if exists.
    # json is not very suitable continuous data, consider use another type of storage.
    user_id = event.get_user_id()
    data_dir = event_remind_config.events_data_dir

    user_data_dir = os.path.join(data_dir, user_id)
    if not os.path.isdir(user_data_dir):
        os.mkdir(user_data_dir)
    event_file = os.path.join(user_data_dir, "events.json")
    curr_events = {}
    if os.path.isfile(event_file):
        try:
            curr_events = json.load(open(event_file, "r"))
        except Exception as e:
            logger.error(e)
            # error handler, ask user to confirm fix by himself or delete all events have been registered.
    curr_events.update(new_event)
    json.dump(curr_events, open(event_file, "w"), ensure_ascii=False, indent=4)

    reply_msg = Message([
        MessageSegment.text(f"事件 {state['event_content']} 注册成功！\n"),
        MessageSegment.text(f"事件将于 {event_time_str} 发生，\n且我将于 {lead_time_str} 时提醒您."),
    ])
    await event_rgst.finish(reply_msg)
