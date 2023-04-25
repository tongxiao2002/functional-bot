'''
@Author: tongxiao
@FileName: config.py
@CreateTime: 2023-04-20 00:51:13
@Description:
Email configs
'''

import pytz
from pydantic import BaseModel, validator
from dataclasses import dataclass


class Config(BaseModel):
    zhouxunwang_key: str = r"U%2B%2FG%2FIYyT9j%2BhpKN94ozRG7FPgTgsJeZ%2Fpxz7%2Fo"
    dinivation_data_dir: str = "data/divination"


@dataclass
class TimeZoneConfig:
    local_time_zone = pytz.timezone('UTC')
    dest_time_zone = pytz.timezone('Etc/GMT-8')
    datetime_format = "%Y-%m-%d %H:%M:%S"
