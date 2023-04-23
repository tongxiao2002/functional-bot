'''
@Author: tongxiao
@FileName: event_list.py
@CreateTime: 2023-04-23 14:52:46
@Description:

'''

import os
import json
from nonebot.params import CommandArg
# from nonebot.adapters.console import Message, MessageSegment, Event
from nonebot.adapters.onebot.v11 import Message, MessageSegment, Event
from . import event_remind_config, event_cmd_group


event_base_matcher = event_cmd_group.command(tuple())
event_lister = event_cmd_group.command("list", aliases={'事件'})

@event_lister.handle()
async def list_events(event: Event, args: Message = CommandArg()):
    user_id = event.get_user_id()
    event_file = os.path.join(event_remind_config.events_data_dir, user_id, "events.json")
    if not os.path.isfile(event_file):
        # 没有事件
        reply_msgs = [
            MessageSegment.text("暂时还没有待提醒的事件哦.")
        ]
        await event_lister.finish(Message(reply_msgs))

    events = json.load(open(event_file, "r"))
    reply_msgs = []
    for idx, (uuid, event) in enumerate(events.items()):
        msg_for_event = [
            MessageSegment.text(f"{idx + 1}.\n"),
            MessageSegment.text(f"事件内容：{event['event_content']}\n"),
            MessageSegment.text(f"事件发生时间：{event['event_time']}\n"),
            MessageSegment.text(f"提醒时间：{event['lead_time']}\n"),
        ]
        reply_msgs.extend(msg_for_event)
    # get rid of '\n'
    if reply_msgs:
        reply_msgs[-1] = MessageSegment.text(f"提醒时间：{event['lead_time']}")
    else:
        # 没有事件
        reply_msgs = [
            MessageSegment.text("暂时还没有待提醒的事件哦.")
        ]
    await event_lister.finish(Message(reply_msgs))

event_base_matcher.append_handler(list_events)
