from nonebot.rule import to_me
from nonebot.adapters import Message, MessageSegment
from nonebot.params import CommandArg
from nonebot.plugin import on_command


weather = on_command("天气", aliases={'weather'}, rule=to_me(), priority=10, block=True)

@weather.handle()
async def handle_weather(message: Message = CommandArg()):
    await weather.finish(message='问勾吧天气！')
