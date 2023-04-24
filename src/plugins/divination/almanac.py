'''
@Author: tongxiao
@FileName: almanac.py
@CreateTime: 2023-04-24 01:34:34
@Description:
黄历
'''

import os
import json
import requests
from datetime import datetime
from nonebot import on_command
from nonebot.log import logger
from nonebot.rule import to_me, Rule
# from nonebot.adapters.console import Message, MessageSegment, Event
from nonebot.adapters.onebot.v11 import Message, MessageSegment, Event
from .config import TimeZoneConfig
from . import divination_rules, divination_config

rules = to_me()
divination_almanac = on_command("almanac", aliases={'黄历'}, priority=10, rule=divination_rules)


@divination_almanac.handle()
async def send_almanac_info():
    now = datetime.now(tz=TimeZoneConfig.local_time_zone)
    now = now.astimezone(tz=TimeZoneConfig.dest_time_zone)
    today = now.strftime("%Y-%m-%d")
    almanac_file = os.path.join(divination_config.dinivation_data_dir, "almanac", f"{today}.json")
    if os.path.isfile(almanac_file):
        almanac_data = json.load(open(almanac_file, "r"))
    else:
        try:
            api_url = "http://zhouxunwang.cn/data/?id=127"
            api_url += f"&key={divination_config.zhouxunwang_key}"
            api_url += f"&year={now.year}"
            api_url += f"&month={now.month}"
            api_url += f"&day={now.day}"
            resp = requests.get(api_url)
            assert resp.status_code == 200
        except Exception as e:
            logger.error(e)
            reply_msgs = Message([
                MessageSegment.text("今天查询次数已经到达上限。")
            ])
            await divination_almanac.finish(reply_msgs)
        almanac_data = json.loads(resp.content)
        json.dump(almanac_data, open(almanac_file, "w"), ensure_ascii=False, indent=4)
    if any([len(item) != 0 for item in almanac_data['result']['yi']]):
        yi_events = '，'.join(almanac_data['result']['yi'])
    else:
        yi_events = "无"
    if any([len(item) != 0 for item in almanac_data['result']['ji']]):
        ji_events = '，'.join(almanac_data['result']['ji'])
    else:
        ji_events = "无"
    reply_msgs = Message([
        MessageSegment.text(f"日期：{today}\n"),
        MessageSegment.text(f"宜：{yi_events}\n"),
        MessageSegment.text(f"忌：{ji_events}")
    ])
    await divination_almanac.finish(reply_msgs)
