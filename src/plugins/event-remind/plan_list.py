'''
@Author: tongxiao
@FileName: plan_list.py
@CreateTime: 2023-04-25 01:31:20
@Description:

'''

import os
import json
from datetime import datetime
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, MessageSegment, Event
from . import event_remind_config, plan_cmd_group
from .config import TimeZoneConfig


plan_base_matcher = plan_cmd_group.command(tuple())
plan_lister = plan_cmd_group.command("list", aliases={'计划'})

@plan_lister.handle()
async def list_plans(event: Event, args: Message = CommandArg()):
    user_id = event.get_user_id()
    plan_file = os.path.join(event_remind_config.plans_data_dir, user_id, "plans.json")
    if not os.path.isfile(plan_file):
        # 没有事件
        reply_msgs = [
            MessageSegment.text("暂时还没有待完成的计划哦.")
        ]
        await plan_lister.finish(Message(reply_msgs))

    plans = json.load(open(plan_file, "r"))
    if len(plans) == 0:
        # 没有事件
        reply_msgs = [
            MessageSegment.text("暂时还没有待完成的计划哦.")
        ]
        await plan_lister.finish(Message(reply_msgs))

    reply_msgs = []
    for idx, (uuid, plan) in enumerate(plans.items()):
        plan_time = plan['plan_time'] or "无"
        mention_times = "，".join(plan['mention_times']) or "无"
        msg_for_event = [
            MessageSegment.text(f"{idx + 1}.\n"),
            MessageSegment.text(f"计划内容：{plan['plan_content']}\n"),
            MessageSegment.text(f"计划完成时间：{plan_time}\n"),
            MessageSegment.text(f"每天提醒时间点：{mention_times}\n"),
        ]
        reply_msgs.extend(msg_for_event)

    # get rid of '\n'
    if reply_msgs:
        reply_msgs[-1] = MessageSegment.text(f"每天提醒时间点：{mention_times}")
    await plan_lister.finish(Message(reply_msgs))

plan_base_matcher.append_handler(list_plans)
