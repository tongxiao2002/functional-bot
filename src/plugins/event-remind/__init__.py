'''
@Author: tongxiao
@FileName: __init__.py
@CreateTime: 2023-04-21 00:55:37
@Description:

'''

from nonebot import get_driver, CommandGroup
from .config import Config
from nonebot.rule import to_me, Rule


event_rules = to_me()

event_cmd_group = CommandGroup("event", rule=event_rules, priority=10)

event_remind_config = Config.parse_obj(get_driver().config)


from .event_list import event_base_matcher, event_lister
from .event_register import event_rgst
from .event_reminder import scheduler
