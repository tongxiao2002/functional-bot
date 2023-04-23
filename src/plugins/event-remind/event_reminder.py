'''
@Author: tongxiao
@FileName: event_reminder.py
@CreateTime: 2023-04-22 03:09:45
@Description:

'''

import os
import json
import pytz
import email
from nonebot import require
from nonebot import get_bot
from nonebot.log import logger
from datetime import datetime, timedelta
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.adapters.onebot.v11 import PrivateMessageEvent, Message, MessageSegment
from .config import TimeZoneConfig

require("nonebot_plugin_apscheduler")

from nonebot_plugin_apscheduler import scheduler
from . import event_remind_config


start_date = datetime.now().replace(minute=0, second=0, microsecond=0, tzinfo=TimeZoneConfig.local_time_zone)
datetime_format = TimeZoneConfig.datetime_format

@scheduler.scheduled_job('interval', minutes=event_remind_config.interval, start_date=start_date)
async def send_event_reminder_msgs():
    events_data_dir = event_remind_config.events_data_dir
    bot = get_bot()
    now = datetime.now(tz=TimeZoneConfig.local_time_zone)
    now = now.astimezone(tz=TimeZoneConfig.dest_time_zone)
    # print("now: ", now)
    for user_id in os.listdir(events_data_dir):
        event_file = os.path.join(events_data_dir, user_id, "events.json")
        if not os.path.isfile(event_file):
            return
        events = json.load(open(event_file, "r"))
        if len(events) == 0:
            return
        # new_events is used to save the events after sending msgs
        new_events = {}
        for k, event in events.items():
            lead_time = datetime.strptime(event['lead_time'], datetime_format).replace(tzinfo=TimeZoneConfig.dest_time_zone)
            # print("lead_time: ", lead_time)
            interval = timedelta(minutes=2 * event_remind_config.interval)
            # print("interval: ", interval)
            time_diff = now - lead_time
            # print("time_diff: ", time_diff)
            if time_diff.days < 0:
                # events will remind in the future
                new_events[k] = event
                continue
            if time_diff > interval:
                # events that is too old to remove, just don't add it into new_events
                continue
            # send messages
            msg = Message([
                MessageSegment.text(f"您注册的事件 {event['event_content']} 将于 {event['event_time']} 发生，请不要忘记！")
            ])
            await bot.send_msg(
                message_type='private',
                user_id=int(user_id),
                message=Message(msg)
            )
        # no events to delete
        if len(new_events) != len(events):
            json.dump(new_events, open(event_file, "w"), ensure_ascii=False, indent=4)
