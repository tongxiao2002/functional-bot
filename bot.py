'''
@Author: tongxiao
@FileName: bot.py
@CreateTime: 2023-04-20 00:41:00
@Description:

'''

import nonebot
import asyncio
from datetime import datetime, timedelta
from nonebot.log import logger_id, logger

from nonebot.adapters.console import Adapter as ConsoleAdapter
from nonebot.adapters.onebot.v11 import Adapter as OnebotAdapter

bot_config = {
    "superusers": {773540317},
    "command_start": {'/'},
    "host": '127.0.0.1',
    "port": 11451
}

apscheduler_config = {
    "apscheduler.timezone": "UTC",
    "apscheduler.executors.processpool": {
        "type": "processpool",
        "max_workers": "61"
    },
    # "apscheduler.executors.default": {
    #     "class": "apscheduler.executors.pool:ThreadPoolExecutor",
    #     "max_workers": "8"
    # },
    "apscheduler.job_defaults.coalesce": "false",
    "apscheduler.job_defaults.misfire_grace_time": "30",
    "apscheduler.job_defaults.max_instances": "61"
}

# 初始化 NoneBot
nonebot.init(**bot_config, apscheduler_config=apscheduler_config)

# config logger
logger_format: str = (
    "<g>{time:YYYY-MM-DD HH:mm:ss}</g> "
    "[<lvl>{level}</lvl>] "
    "<c><u>{name}</u></c> | "
    # "<c>{function}:{line}</c>| "
    "{message}"
)

# 服务器落后北京时间 8h
now = datetime.now() + timedelta(hours=8)
now = datetime.strftime(now, "%Y-%m-%d_%H:%M:%S")
logger.remove(logger_id)
logger.add(
    sink=f"logs/{now}.log",
    level="INFO",
    format=logger_format,
    rotation="1 week",
)

# 注册适配器
driver = nonebot.get_driver()
# driver.register_adapter(ConsoleAdapter)
driver.register_adapter(OnebotAdapter)

# 在这里加载插件
nonebot.load_builtin_plugins("echo")  # 内置插件
nonebot.load_plugin("nonebot_plugin_apscheduler")  # 第三方插件
nonebot.load_plugins("src/plugins")  # 本地插件


if __name__ == "__main__":
    nonebot.run()
