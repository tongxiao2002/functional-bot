'''
@Author: tongxiao
@FileName: event_delete.py
@CreateTime: 2023-04-23 19:42:35
@Description:

'''

import os
import json
from nonebot.log import logger
from nonebot.typing import T_State
from nonebot.params import CommandArg, ArgPlainText
from nonebot.adapters.onebot.v11 import Message, MessageSegment, Event
from . import event_remind_config, event_cmd_group, special_chinese_char_map_dict


event_del = event_cmd_group.command("delete", aliases={'删除事件'})

@event_del.handle()
async def list_events(event: Event, state: T_State, args: Message = CommandArg()):
    user_id = event.get_user_id()
    event_file = os.path.join(event_remind_config.events_data_dir, user_id, "events.json")
    if not os.path.isfile(event_file):
        # 没有事件
        reply_msgs = [
            MessageSegment.text("暂时还没有待提醒的事件哦.")
        ]
        await event_del.finish(Message(reply_msgs))

    events = json.load(open(event_file, "r"))
    if len(events) == 0:
        reply_msgs = [
            MessageSegment.text("暂时还没有待提醒的事件哦.")
        ]
        await event_del.finish(Message(reply_msgs))

    event_idx_to_uuid = {}
    reply_msgs = [
        MessageSegment.text("以下为您已注册的事件：\n")
    ]
    for idx, (uuid, event) in enumerate(events.items()):
        msg_for_event = [
            MessageSegment.text(f"{idx + 1}.\n"),
            MessageSegment.text(f"事件内容：{event['event_content']}\n"),
            MessageSegment.text(f"事件发生时间：{event['event_time']}\n"),
            MessageSegment.text(f"提醒时间：{event['lead_time']}\n"),
        ]
        event_idx_to_uuid[idx + 1] = uuid
        reply_msgs.extend(msg_for_event)
    state['event_idx_to_uuid'] = event_idx_to_uuid

    reply_msgs.append(MessageSegment.text(f"\n请输入序号删除相应的事件。(一次仅能删除一条事件)"))
    await event_del.send(Message(reply_msgs))


@event_del.got("index", prompt=None)
async def delete_event(event: Event, state: T_State, index: str = ArgPlainText()):
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
            await event_del.reject(reject_msg)
        else:
            reject_msg = Message([
                MessageSegment.text("序号输入错误次数过多，已终止会话。")
            ])
            await event_del.finish(reject_msg)
    event_uuid = state['event_idx_to_uuid'][index]
    user_id = event.get_user_id()

    event_file = os.path.join(event_remind_config.events_data_dir, str(user_id), "events.json")
    events = json.load(open(event_file, "r"))
    try:
        poped_event = events.pop(event_uuid)
    except Exception as e:
        logger.error(e)
        return

    json.dump(events, open(event_file, "w"), ensure_ascii=False, indent=4)
    reply_msgs = Message([
        MessageSegment.text(f"已删除事件 {poped_event['event_content']}.")
    ])
    await event_del.finish(reply_msgs)
