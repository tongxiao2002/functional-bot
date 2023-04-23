'''
@Author: tongxiao
@FileName: help.py
@CreateTime: 2023-04-23 15:26:16
@Description:

'''

from nonebot import on_command
from nonebot.log import logger
from nonebot.rule import to_me, Rule
from nonebot.typing import T_State
from nonebot.params import CommandArg
# from nonebot.adapters.console import Message, MessageSegment, Event
from nonebot.adapters.onebot.v11 import Message, MessageSegment, Event


rules = to_me()
helper = on_command("help", aliases={'帮助'}, priority=10, rule=rules)

@helper.handle()
async def send_help_msgs(args: Message = CommandArg()):
    help_msgs = Message([
        MessageSegment.text("以下指令都需要 私聊机器人 或在 群聊中@机器人 输入：\n"),
        MessageSegment.text("/help 获取机器人使用指南\n\n"),
        MessageSegment.text("/weather 查询当天某地天气\n\n"),
        MessageSegment.text("/event 查询已注册的事件\n"),
        MessageSegment.text("/event.list 查询已注册的事件\n"),
        MessageSegment.text("/event.register 注册待提醒的事件"),
    ])
    await helper.finish(help_msgs)
