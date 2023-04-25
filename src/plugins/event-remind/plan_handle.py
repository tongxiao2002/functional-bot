'''
@Author: tongxiao
@FileName: plan_register.py
@CreateTime: 2023-04-25 00:23:19
@Description:

'''

import os
import re
import uuid
import json
import jionlp
from datetime import datetime, timedelta
from nonebot import get_bot
from nonebot.log import logger
from nonebot.typing import T_State
from nonebot.params import CommandArg, ArgPlainText
from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11 import Message, MessageSegment, Event
from . import event_remind_config, plan_cmd_group
from .config import TimeZoneConfig
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.combining import OrTrigger

from nonebot import require
require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler


plan_rgst = plan_cmd_group.command("register", aliases={'注册计划'})
plan_del = plan_cmd_group.command("delete", aliases={'删除计划'})
datetime_format = TimeZoneConfig.datetime_format


def get_all_trigger_time(user_id: str):
    plans_data_dir = event_remind_config.plans_data_dir
    plan_file = os.path.join(plans_data_dir, user_id, "plans.json")
    plans = json.load(open(plan_file, "r"))
    now = datetime.now().replace(tzinfo=TimeZoneConfig.dest_time_zone)
    triggers = []
    for uuid, plan in plans.items():
        mention_times_str = plan['mention_times']
        for time_str in mention_times_str:
            hour, minute = time_str.split(":")
            tmp = now.replace(hour=int(hour), minute=int(minute)).astimezone(tz=TimeZoneConfig.local_time_zone)
            triggers.append(CronTrigger(hour=tmp.hour, minute=tmp.minute))
    return OrTrigger(triggers) if len(triggers) != 0 else None


def save_new_plan(plan_file: str, new_plan: dict):
    curr_plans = {}
    if os.path.isfile(plan_file):
        try:
            curr_plans = json.load(open(plan_file, "r"))
        except Exception as e:
            logger.error(e)
            # error handler, ask user to confirm fix by himself or delete all events have been registered.
    curr_plans.update(new_plan)
    json.dump(curr_plans, open(plan_file, "w"), ensure_ascii=False, indent=4)


def timestr_preprocess(timestr: str):
    """
    时间字符串预处理
    """
    # 删除空白
    ptn = re.compile(r'\s+')
    timestr = re.sub(ptn, '', timestr)
    # 允许 "每天8点" 这种输入
    if timestr.startswith('每天'):
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
        dt = datetime.strptime(time['time'][0], "%Y-%m-%d %H:%M:%S").replace(tzinfo=TimeZoneConfig.dest_time_zone)
        return dt
    elif time_type == 'time_delta':
        new_time = {k + 's': v for k, v in time['time'].items()}
        delta_time = timedelta(**new_time)
        return delta_time
    else:
        raise NotImplementedError


async def plan_mention(user_id: str):
    bot = get_bot()
    now = datetime.now(tz=TimeZoneConfig.local_time_zone)
    now = now.astimezone(tz=TimeZoneConfig.dest_time_zone)
    plans_data_dir = event_remind_config.plans_data_dir
    plan_file = os.path.join(plans_data_dir, user_id, "plans.json")
    plans = json.load(open(plan_file, "r"))
    for uuid, plan in plans.items():
        mention_times = []
        mention_times_str = plan['mention_times']
        for time_str in mention_times_str:
            hour, minute = time_str.split(":")
            mention_time = now.replace(hour=int(hour), minute=int(minute), tzinfo=TimeZoneConfig.dest_time_zone)
            mention_times.append(mention_time)
        diff_times = [now - t for t in mention_times]

        for diff_time in diff_times:
            interval = timedelta(minutes=event_remind_config.interval)
            if diff_time.days >= 0 and diff_time < interval:
                if plan['plan_time'] is not None:
                    reply_msgs = Message([
                        MessageSegment.text(f"您计划将于 {plan['plan_time']} 之前完成 {plan['plan_content']}，现在完成多少了呢？")
                    ])
                else:
                    reply_msgs = Message([
                        MessageSegment.text(f"您的计划 {plan['plan_content']}，现在完成多少了呢？")
                    ])
                logger.info(f"sending plan message to user {user_id} successfully")
                await bot.send_msg(
                    message_type='private',
                    user_id=int(user_id),
                    message=reply_msgs
                )


def add_jobs_init():
    """
    每次在机器人启动时向 scheduler 增加任务
    """
    plans_data_dir = event_remind_config.plans_data_dir
    for user_id in os.listdir(plans_data_dir):
        triggers = get_all_trigger_time(user_id)
        scheduler.add_job(plan_mention, args=[user_id], trigger=triggers, id=f"plan_{user_id}")
    logger.info("init plan scheduler succeeded.")

add_jobs_init()


# handlers
@plan_rgst.handle()
async def register_event(matcher: Matcher, args: Message = CommandArg()):
    if args.extract_plain_text():
        matcher.set_arg('plan_content', args)
    else:
        reply_msg = Message([
            MessageSegment.text("请问您想要注册什么计划呢？"),
        ])
        await plan_rgst.send(reply_msg)


@plan_rgst.got('plan_content')
async def get_plan_content(state: T_State, plan_content: str = ArgPlainText()):
    state['plan_content'] = plan_content
    reply_msg = Message([
        MessageSegment.text(f"收到！计划为 {plan_content}."),
    ])
    await plan_rgst.send(reply_msg)


@plan_rgst.got('plan_time_str', prompt="请问您打算什么时间点之前完成计划呢？（描述太过模糊可能会解析失败哦）\n输入“无”则没有时间限制。")
async def get_plan_time(state: T_State, plan_time_str: str = ArgPlainText()):
    if plan_time_str == "无":
        state['plan_time'] = None
        return

    state['try_count'] = state.get('try_count', 0)
    try:
        plan_time = timestr_to_datetime(plan_time_str)
    except Exception as e:
        logger.warning(e)
        state['try_count'] += 1
        if state['try_count'] < event_remind_config.max_try_count:
            chances = event_remind_config.max_try_count - state['try_count']
            reject_msg = Message([
                MessageSegment.text(f"时间 '{plan_time_str}' 解析失败！请重新输入时间。\n"),
                MessageSegment.text(f"示例：明天下午5点，2小时后，9号上午10点。\n"),
                MessageSegment.text(f"您还有 {chances} 次输入机会。"),
            ])
            await plan_rgst.reject(reject_msg)
        else:
            reject_msg = Message([
                MessageSegment.text("时间输入错误次数过多，已终止会话。")
            ])
            await plan_rgst.finish(reject_msg)

    plan_time = plan_time.replace(second=0, microsecond=0)
    plan_time_str = datetime.strftime(plan_time, datetime_format)
    state['plan_time'] = plan_time_str

    state['try_count'] = 0
    reply_msg = Message([
        MessageSegment.text(f"好的，您计划将于 {plan_time_str} 之前完成 {state['plan_content']}."),
    ])
    await plan_rgst.send(reply_msg)


@plan_rgst.got('mention_times_str', prompt=f"那么您需要我每天哪些时间点提醒您呢？（若有多个时间点需提醒则用“，”分开，描述太过模糊可能会解析失败哦）\n输入“不需要”则我不会提醒您")
async def get_lead_time_and_finish(event: Event, state: T_State, mention_times_str: str = ArgPlainText()):
    new_plan = {
        "plan_content": state['plan_content'],
        "plan_time": state['plan_time'],
        "mention_times": []
    }
    user_id = event.get_user_id()
    data_dir = event_remind_config.plans_data_dir
    user_data_dir = os.path.join(data_dir, user_id)
    if not os.path.isdir(user_data_dir):
        os.mkdir(user_data_dir)
    plan_file = os.path.join(user_data_dir, "plans.json")

    if mention_times_str == "不需要":
        if state['plan_time'] == None:
            reply_msg = Message([
                MessageSegment.text(f"计划 {state['plan_content']} 注册成功！"),
                MessageSegment.text(f"您的计划为长期计划，"),
                MessageSegment.text(f"且我不会提醒您。")
            ])
        else:
            reply_msg = Message([
                MessageSegment.text(f"计划 {state['plan_content']} 注册成功！"),
                MessageSegment.text(f"您计划将于 {state['plan_time']} 前完成，"),
                MessageSegment.text(f"且我不会提醒您。")
            ])
        save_new_plan(plan_file, {str(uuid.uuid4()): new_plan})
        await plan_rgst.finish(reply_msg)

    state['try_count'] = state.get('try_count', 0)
    try:
        mention_times = []
        mention_times_str = mention_times_str.replace("，", ",").split(",")
        for mention_time in mention_times_str:
            mention_time = timestr_to_datetime(mention_time, time_type='time_point')
            mention_times.append(mention_time)
    except Exception as e:
        logger.warning(e)
        state['try_count'] += 1
        if state['try_count'] < event_remind_config.max_try_count:
            chances = event_remind_config.max_try_count - state['try_count']
            reject_msg = Message([
                MessageSegment.text(f"时间 '{mention_time}' 解析失败！请重新输入时间。\n"),
                MessageSegment.text(f"示例：每天上午9点，晚上10点20分\n"),
                MessageSegment.text(f"您还有 {chances} 次输入机会。"),
            ])
            await plan_rgst.reject(reject_msg)
        else:
            reject_msg = Message([
                MessageSegment.text("时间输入错误次数过多，已终止会话。")
            ])
            await plan_rgst.finish(reject_msg)

    # save plan to disk
    # load current plans if exists.
    # json is not very suitable continuous data, consider use another type of storage.
    new_plan['mention_times'] = [t.strftime("%H:%M") for t in mention_times]
    save_new_plan(plan_file, {str(uuid.uuid4()): new_plan})

    triggers = get_all_trigger_time(user_id)
    try:
        scheduler.reschedule_job(job_id=f"plan_{user_id}", trigger=triggers)
    except Exception as e:
        logger.warning(f"{e}, adding new job plan_{user_id}")
        scheduler.add_job(plan_mention, args=[user_id], trigger=triggers, id=f"plan_{user_id}")

    if new_plan['plan_time'] is None:
        plan_time_msg = f"您的计划为长期计划。\n"
    else:
        plan_time_msg = f"您计划将于 {new_plan['plan_time']} 前完成。\n"

    reply_msg = Message([
        MessageSegment.text(f"计划 {state['plan_content']} 注册成功！"),
        MessageSegment.text(plan_time_msg),
        MessageSegment.text(f"我将在每天的以下时间点提醒您：{'，'.join(new_plan['mention_times'])}")
    ])
    await plan_rgst.finish(reply_msg)


@plan_del.handle()
async def list_plans(event: Event, state: T_State, args: Message = CommandArg()):
    user_id = event.get_user_id()
    plan_file = os.path.join(event_remind_config.plans_data_dir, user_id, "plans.json")
    if not os.path.isfile(plan_file):
        # 没有事件
        reply_msgs = [
            MessageSegment.text("暂时还没有待完成的计划哦.")
        ]
        await plan_del.finish(Message(reply_msgs))

    events = json.load(open(plan_file, "r"))
    if len(events) == 0:
        reply_msgs = [
            MessageSegment.text("暂时还没有待完成的计划哦.")
        ]
        await plan_del.finish(Message(reply_msgs))

    plan_idx_to_uuid = {}
    reply_msgs = [
        MessageSegment.text("以下为您已注册的计划：\n")
    ]
    for idx, (uuid, plan) in enumerate(events.items()):
        plan_time = plan['plan_time'] or "无"
        mention_times = "，".join(plan['mention_times']) or "无"
        msg_for_plan = [
            MessageSegment.text(f"{idx + 1}.\n"),
            MessageSegment.text(f"计划内容：{plan['plan_content']}\n"),
            MessageSegment.text(f"计划完成时间：{plan_time}\n"),
            MessageSegment.text(f"每天提醒时间点：{mention_times}\n"),
        ]
        plan_idx_to_uuid[idx + 1] = uuid
        reply_msgs.extend(msg_for_plan)
    state['plan_idx_to_uuid'] = plan_idx_to_uuid

    reply_msgs.append(MessageSegment.text(f"\n请输入序号删除相应的计划。(一次仅能删除一条计划)"))
    await plan_del.send(Message(reply_msgs))


@plan_del.got("index", prompt=None)
async def delete_plan(event: Event, state: T_State, index: str = ArgPlainText()):
    state['try_count'] = state.get('try_count', 0)
    try:
        if index.endswith('.'):
            index = index[:-1]
        index = int(index)
    except Exception as e:
        logger.warning(e)
        state['try_count'] += 1
        if state['try_count'] < event_remind_config.max_try_count:
            chances = event_remind_config.max_try_count - state['try_count']
            reject_msg = Message([
                MessageSegment.text(f"序号 '{index}' 解析失败！请重新输入序号。\n"),
                MessageSegment.text(f"您还有 {chances} 次输入机会。")
            ])
            await plan_del.reject(reject_msg)
        else:
            reject_msg = Message([
                MessageSegment.text("序号输入错误次数过多，已终止会话。")
            ])
            await plan_del.finish(reject_msg)
    plan_uuid = state['plan_idx_to_uuid'][index]
    user_id = event.get_user_id()

    plan_file = os.path.join(event_remind_config.plans_data_dir, str(user_id), "plans.json")
    plans = json.load(open(plan_file, "r"))
    try:
        poped_plan = plans.pop(plan_uuid)
    except Exception as e:
        logger.error(e)
        reply_msgs = Message([
            MessageSegment.text(f"删除计划 {index} 失败.")
        ])
        await plan_del.finish(reply_msgs)

    json.dump(plans, open(plan_file, "w"), ensure_ascii=False, indent=4)
    triggers = get_all_trigger_time(user_id)
    if triggers:
        scheduler.reschedule_job(job_id=f"plan_{user_id}", trigger=triggers)
    else:
        scheduler.remove_job(job_id=f"plan_{user_id}")
    reply_msgs = Message([
        MessageSegment.text(f"已删除计划 {poped_plan['plan_content']}.")
    ])
    await plan_del.finish(reply_msgs)
