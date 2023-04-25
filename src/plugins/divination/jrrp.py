'''
@Author: tongxiao
@FileName: jrrp.py
@CreateTime: 2023-04-24 00:39:23
@Description:
占卜 --- 今日人品
'''

import pytz
import random
from datetime import datetime
from nonebot import on_command
# from nonebot.adapters.console import Message, MessageSegment, Event
from nonebot.adapters.onebot.v11 import Message, MessageSegment, Event
from .config import TimeZoneConfig
from . import divination_rules


divination_jrrp = on_command("jrrp", aliases={'今日人品'}, priority=10, rule=divination_rules)

rp_to_str = {
    0: "大凶",
    1: "凶",
    2: "一般",
    3: "吉",
    4: "大吉",
    5: "大吉"
}

@divination_jrrp.handle()
async def send_jrrp(event: Event):
    now = datetime.now(tz=TimeZoneConfig.local_time_zone)
    now = now.astimezone(tz=TimeZoneConfig.dest_time_zone)
    now = now.replace(hour=0, minute=0, second=0, microsecond=0)
    now = int(now.timestamp())
    user_id = event.get_user_id()
    random.seed(now + int(user_id))
    rp = random.randint(0, 100)
    reply_msgs = Message([
        MessageSegment.text(f"今日人品：{rp}，{rp_to_str[rp // 20]}")
    ])
    await divination_jrrp.finish(reply_msgs)
