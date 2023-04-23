'''
@Author: tongxiao
@FileName: message_adaptor.py
@CreateTime: 2023-04-22 14:36:41
@Description:
Message & MessageSegment Adaptor
用于统一不同 Adaptor 的 Message & MessageSegment 类的接口
'''

from nonebot.adapters import (
    Message as BaseMessage,
    MessageSegment as BaseMessageSemgent
)
from nonebot.adapters.onebot.v11 import (
    Message as OnebotMessage,
    MessageSegment as OnebotMessageSegment
)
from nonebot.adapters.console import (
    Message as ConsoleMessage,
    MessageSegment as ConsoleMessageSemgent
)


messages = {
    "onebot": OnebotMessage,
    "console": ConsoleMessage,
}

message_segments = {
    "onebot": OnebotMessageSegment,
    "console": ConsoleMessageSemgent,
}

class MessageAdaptor:
    def __init__(self, adaptor: str) -> None:
        self.adapter = adaptor


class MessageSegmentAdaptor:
    adpator: str = "console"

    @classmethod
    def text(cls, str):
        message_segments[cls.adpator].text(str)
