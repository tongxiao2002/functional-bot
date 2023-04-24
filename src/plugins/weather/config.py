'''
@Author: tongxiao
@FileName: config.py
@CreateTime: 2023-04-24 02:02:12
@Description:

'''

import pytz
from pydantic import BaseModel, validator
from dataclasses import dataclass


class Config(BaseModel):
    zhouxunwang_key: str = r"123456"
    weather_data_dir: str = "data/weather"


@dataclass
class TimeZoneConfig:
    local_time_zone = pytz.timezone('UTC')
    dest_time_zone = pytz.timezone('Etc/GMT-8')
    datetime_format = "%Y-%m-%d %H:%M:%S"
