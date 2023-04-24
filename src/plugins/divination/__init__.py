'''
@Author: tongxiao
@FileName: __init__.py
@CreateTime: 2023-04-24 00:54:18
@Description:

'''

from nonebot import get_driver, CommandGroup
from .config import Config
from nonebot.rule import to_me, Rule


divination_rules = to_me()

divination_config = Config.parse_obj(get_driver().config)


from .jrrp import divination_jrrp
from .almanac import divination_almanac
