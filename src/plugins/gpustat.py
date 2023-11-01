'''
@Author: tongxiao
@FileName: gpustat.py
@CreateTime: 2023-10-11 15:16:45
@Description:

'''

import re
import subprocess
from nonebot import on_command
from nonebot.log import logger
from nonebot.rule import to_me
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, MessageSegment


rules = to_me()
gpustat_matcher = on_command("gpustat", priority=10, rule=rules)

curr_host = 'gakki'
hosts = {
    'TnT': {
        'host': '127.0.0.1',
        'port': 22,
        'username': 'username',
        'password': 'password',
    },
    'gakki': {
        'host': '127.0.0.1',
        'port': 22,
        'username': 'username',
        'password': 'password',
    },
    'tongtong': {
        'host': '127.0.0.1',
        'port': 22,
        'username': 'username',
        'password': 'password',
    },
}


def get_face_by_gram(grams: list):
    """face id: [QQ face](https://github.com/kyubotics/coolq-http-api/wiki/%E8%A1%A8%E6%83%85-CQ-%E7%A0%81-ID-%E8%A1%A8)
    """
    occupied, upper_bound = grams
    occupied = int(occupied)
    upper_bound = int(upper_bound)
    if occupied < upper_bound / 4:
        return 13
    elif occupied < upper_bound / 2:
        return 21
    elif occupied < 3 * upper_bound / 4:
        return 212
    else:
        return 5


def postprocess_message(msg: str):
    msg_segs = msg.split('|')[:3]
    msg_segs = [seg.strip() for seg in msg_segs]
    msg_segs = [
        msg_segs[0],
        f'Temp & Usage: {msg_segs[1]}',
        f'GRAM: {msg_segs[2]}',
    ]
    return msg_segs


@gpustat_matcher.handle()
async def gpustat(args: Message = CommandArg()):
    gpustats = []
    procs = []
    for hostname, host_args in hosts.items():
        if hostname == curr_host:
            args = 'gpustat'
        else:
            args = f"sshpass -p \"{host_args['password']}\" ssh {host_args['username']}@{host_args['host']} -p {host_args['port']} gpustat"
        logger.info(f"[gpustat]: {args}")
        proc = subprocess.Popen(
            args=args,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        procs.append(proc)

    for hostname, proc in zip(hosts.keys(), procs):
        stdout_res, stderr_res = proc.communicate()
        stdout_res = stdout_res.decode().split('\n')
        msg_segs = [hostname]
        for line_msg in stdout_res[1:]:
            if len(line_msg.strip()) == 0:
                continue
            segs = postprocess_message(line_msg)
            msg_segs += segs
        gpustats.append(msg_segs)

    reply_msgs = []
    number_ptn = re.compile(r'\d+')
    for gpu_idx, msg_segs in enumerate(gpustats):
        for idx, seg in enumerate(msg_segs):
            if idx == 0:
                if gpu_idx > 0:
                    reply_msgs.append(MessageSegment.text("\n\n"))
                reply_msgs.append(MessageSegment.face(219))
                reply_msgs.append(MessageSegment.text(seg))
                reply_msgs.append(MessageSegment.face(219))
            else:
                reply_msgs.append(MessageSegment.text('\n' + seg))
                if seg.startswith('GRAM'):
                    gram_numbers = re.findall(number_ptn, seg)
                    face_id = get_face_by_gram(gram_numbers)
                    reply_msgs.append(MessageSegment.face(face_id))
    await gpustat_matcher.finish(Message(reply_msgs))
