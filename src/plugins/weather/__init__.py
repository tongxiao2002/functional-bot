'''
@Author: tongxiao
@FileName: __init__.py
@CreateTime: 2023-04-24 01:39:10
@Description:

'''

from nonebot import get_driver, CommandGroup
from .config import Config
from nonebot.rule import to_me, Rule


weather_rules = to_me()

weather_config = Config.parse_obj(get_driver().config)


from .weather import weather_matcher
