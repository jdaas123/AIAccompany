import json
import uvicorn
from fastapi import FastAPI, Request
from openai.types.beta.threads import message_content
import random
from napcat import napcat
import config
import asyncio
import models
import time
import copy
import utils

# import datetime
app = FastAPI()

"""
{
    user_id:{
        "start_time":,
        "end_time":,
        "task_id":, 
    }
}
"""
send_task = {}

"""
buffers = {
    user_id: {
        "messages": [
            {
                "type":"",
                "content":""
            },
            {
                "type":"",
                "content":""
            },
            {
                "type":"",
                "content":""
            }
        ],
        "task": asyncio_task
    }
}
"""
message_buffers = {}

last_usercontent = ""

async def cir_send(ai_reply, user_id):
    global send_task
    print("当前状态信息")
    for i, v in utils.status.items():
        print(f"{i}->{v}, ")
    ai_reply = ai_reply.split("\n")
    print("reply--->", ai_reply)

    # 是否不回复
    with open(f"./status/{user_id}.json", "r") as f:
        status = json.load(f)
    print(status)
    if status["is_hidden"] == True:
        # 不需要回复
        print("👍 ai 选择不回复 ")
        send_task[user_id]["end_time"] = 1000
        return
    # 延迟发送
    start_time = time.time()
    end_time = start_time + status["delay_seconds"] + 2
    send_task[user_id]["start_time"] = start_time
    send_task[user_id]["end_time"] = end_time

    print(
        f"发送任务开始时间 ---> {start_time} \n" f"发送任务预计结束时间 ---> {end_time}"
    )
    print("ai 将延迟发送 ---> ", status["delay_seconds"], " s")
    await asyncio.sleep(status["delay_seconds"])
    for con in ai_reply:
        print("正在发送消息 😎")
        time_random = random.uniform(0.5, 2)
        print("此次发送延迟--->", time_random, "  s")
        await asyncio.sleep(time_random)
        napcat.send_text(user_id, con)


async def handle_image_message(message, handled_messages) -> str:

    image_url = message["content"]
    print("收到图片消息 🖼️ url ---> ", image_url)
    # print("image_url ---> ",image_url)
    image_information = models.get_image_information(image_url)
    print("image_information--->", image_information)
    handled_messages.append(image_information)


async def handle_video_message(message, handled_messages) -> str:
    video_url = message["content"]
    print("收到视频消息 📽️ url ---> ", video_url)
    video_information = models.get_video_information(video_url)
    print("video_information--->", video_information)
    handled_messages.append(video_information)


async def handle_sound_message(message, handled_messages) -> str:
    sound_url = message["content"]
    print("收到音频消息 🎶 url ---> ", sound_url)
    sound_information = models.get_sound_information(sound_url)
    print("sound_information--->", sound_information)
    handled_messages.append(sound_information)


async def handle_user_message(user_content) -> list:
    """
    :param user_content:
        [
            {
                "type":"",
                "content":""
            },
            {
                "type":"",
                "content":""
            },
            {
                "type":"",
                "content":""
            }
        ]

    :return:
    """

    handled_messages = []
    tasks = []
    for i in user_content:
        if i["type"] == "image":
            # 2. 创建任务并立即开始（不会阻塞当前循环）
            task = asyncio.create_task(handle_image_message(i, handled_messages))
            tasks.append(task)
        elif i["type"] == "video":
            # 2. 创建任务并立即开始（不会阻塞当前循环）
            task = asyncio.create_task(handle_video_message(i, handled_messages))
            tasks.append(task)
        elif i["type"] == "record":
            # 2. 创建任务并立即开始（不会阻塞当前循环）
            task = asyncio.create_task(handle_sound_message(i, handled_messages))
            tasks.append(task)
        else:
            # type == text or face
            handled_messages.append(i["content"])
    if tasks:
        print(f"--- 准备收网，等待 {len(tasks)} 个后台任务全部完成 ---")
        # 4. 关键点：使用 gather 等待列表里所有的任务完成
        results = await asyncio.gather(*tasks)
        print(f"所有后台任务已结束，结果汇总: {results}")
        return handled_messages
    else:
        print("👍 用户只发了文学消息，没有需要执行的任务。")
        return handled_messages


async def process_user_message(user_id, user_content):
    user_content = await handle_user_message(user_content)
    message_content = "\n".join(user_content)
    print("👌 已处理用户消息，即将发给模型处理--> \n", message_content)
    #记录发给模型前的消息
    global last_usercontent
    last_usercontent = message_content
    ai_reply = models.get_aimessage(user_id, message_content)
    global send_task
    # 判断有无user_id
    if user_id not in send_task:
        send_task[user_id] = {
            "start_time": None,
            "end_time": None,
            "task_id": None,
        }
    task_id = asyncio.create_task(cir_send(ai_reply, user_id))
    print("task_id ---> ", task_id)
    send_task[user_id]["task_id"] = task_id
    print("send_task ---> ", send_task[user_id])


async def delayed_reply(user_id):
    try:
        # 等待用户停止输入
        sleep_time = 3.5
        print(f"继续等待用户发送 ---> {sleep_time} s")
        await asyncio.sleep(sleep_time)

        buffer = message_buffers[user_id]
        user_content = copy.deepcopy(buffer["messages"])
        print(f"不再等待用户发送消息，用户总发 ---> {len(user_content)} 条")
        # user_content = "。 ".join(buffer["messages"])

        # 清空缓冲区
        buffer["messages"] = []

        await process_user_message(user_id, user_content)

    except asyncio.CancelledError:
        # 用户继续发送消息
        print("------process_user_message出错了！")


def add_message_to_buffer(data, buffer):
    """
    {
        "messages": [
            {
                "type":"",
                "content":""
            },
            {
                "type":"",
                "content":""
            },
            {
                "type":"",
                "content":""
            }
        ],
        "task": asyncio_task
    }
    """
    message = data.get("message")
    print(message)
    message_type = message[0]["type"]
    print(message_type)
    if message_type in ["text", "face"]:
        buffer["messages"].append(
            {"type": message_type, "content": data["raw_message"]}
        )
    else:
        buffer["messages"].append(
            {"type": message_type, "content": message[0]["data"]["url"]}
        )


# =========================
# 1️接收 Napcat Webhook
# =========================


@app.post("/webhook")
async def webhook(req: Request):
    data = await req.json()
    if data.get("post_type", "notice") == "notice":
        return
    self_id = data.get("self_id")
    user_id = data.get("user_id")
    # 核心判断：如果是自己发的消息，直接跳过，防止死循环
    if user_id == self_id:
        return {"status": "skipped", "reason": "ignore self message"}
    # if self_id == config.BOT_QQ:
    #     return
    # print("收到消息:", data)
    print("user_id.type --->,", type(user_id))
    # 初始化buffer

    if user_id not in message_buffers:
        message_buffers[user_id] = {"messages": [], "task": None}
    buffer = message_buffers[user_id]
    """
    {
        "messages": [
            {
                "type":"",
                "content":""
            },
            {
                "type":"",
                "content":""
            },
            {
                "type":"",
                "content":""
            }
        ],
        "task": asyncio_task
    }
    """
    add_message_to_buffer(data, buffer)
    print("收到消息 ---> ", buffer["messages"])
    global last_usercontent
    user_send_task = send_task.get(user_id, None)
    print(f"{user_id}已有发送任务 😊---> ", user_send_task)
    if user_send_task:
        now_time = time.time()
        if abs(now_time - send_task[user_id]["end_time"]) > 10:
            print("发送延迟太长，需合并本此消息")
            old_task = send_task[user_id]["task_id"]
            print("取消本次消息发送任务 --- > ", old_task)
            old_task.cancel()
            send_task[user_id] = {}
            buffer["messages"].insert(0, {"type": "old_message", "content": last_usercontent})

    if buffer["task"]:
        # 说明有任务，用户前一刻还在发消息
        buffer["task"].cancel()

    buffer["task"] = asyncio.create_task(delayed_reply(user_id))

    return {"status": "ok"}


# # =========================
# # 2️⃣ 主动发送接口（HTTP调用）
# # =========================


# @app.post("/send/text")
# def send_text(user_id: int, text: str):
#     return napcat.send_text(user_id, text)


# @app.post("/send/image")
# def send_image(user_id: int, url: str):
#     return napcat.send_image(user_id, url)


# @app.post("/send/video")
# def send_video(user_id: int, url: str):
#     return napcat.send_video(user_id, url)


# @app.post("/send/voice")
# def send_voice(user_id: int, url: str):
#     return napcat.send_voice(user_id, url)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=7788)
