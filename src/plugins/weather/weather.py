'''
@Author: tongxiao
@FileName: weather.py
@CreateTime: 2023-04-24 02:01:37
@Description:

'''

import os
import json
import requests
from datetime import datetime
from nonebot.log import logger
from nonebot.rule import to_me
from nonebot.typing import T_State
from nonebot.params import CommandArg, ArgPlainText
from nonebot.plugin import on_command
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from .config import TimeZoneConfig
from . import weather_config


weather_matcher = on_command("weather", aliases={'天气'}, rule=to_me(), priority=10)

@weather_matcher.handle()
async def weather_handler(args: Message = CommandArg()):
    reply_msg = Message([
        MessageSegment.text("请问您想要查询哪个城市的天气呢？"),
    ])
    await weather_matcher.send(reply_msg)


@weather_matcher.got("city", prompt=None)
async def query_weather(city: str = ArgPlainText()):
    now = datetime.now(tz=TimeZoneConfig.local_time_zone)
    now = now.astimezone(tz=TimeZoneConfig.dest_time_zone)
    today = now.strftime("%Y-%m-%d")
    weather_file = os.path.join(weather_config.weather_data_dir, f"{today}_{city}.json")
    if os.path.isfile(weather_file):
        weather_data = json.load(open(weather_file, "r"))
    else:
        try:
            api_url = "http://zhouxunwang.cn/data/?id=7"
            api_url += f"&city={city}"
            api_url += f"&key={weather_config.zhouxunwang_key}"
            resp = requests.get(api_url)
            assert resp.status_code == 200
        except Exception as e:
            logger.error(e)
            reply_msgs = Message([
                MessageSegment.text("今天查询不同城市次数已经到达上限。")
            ])
            await weather_matcher.finish(reply_msgs)
        weather_data = json.loads(resp.content)
        if not weather_data['result']:
            # result is None
            reply_msgs = Message([
                MessageSegment.text(weather_data['reason']),
            ])
            await weather_matcher.finish(reply_msgs)

        json.dump(weather_data, open(weather_file, "w"), ensure_ascii=False, indent=4)
    weather_data = weather_data['result']['realtime']
    # replace None with ""
    for k, v in weather_data.items():
        if v is None:
            weather_data[k] = ""

    reply_msgs = Message([
        MessageSegment.text(f"日期：{today}\n"),
        MessageSegment.text(f"城市：{city}\n"),
        MessageSegment.text(f"平均气温：{weather_data['temperature']}℃\n"),
        MessageSegment.text(f"平均湿度：{weather_data['humidity']}%\n"),
        MessageSegment.text(f"天气：{weather_data['info']}\n"),
        MessageSegment.text(f"风力：{weather_data['power']}\n"),
        MessageSegment.text(f"风向：{weather_data['direct']}\n"),
        MessageSegment.text(f"空气质量指数：{weather_data['aqi']}"),
    ])
    await weather_matcher.finish(reply_msgs)

