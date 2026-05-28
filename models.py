import requests
from langchain.chat_models import init_chat_model

from langchain_deepseek import ChatDeepSeek
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.redis import RedisSaver


from langchain.messages import HumanMessage, AIMessage, SystemMessage

# 加载环境变量
from dotenv import load_dotenv
import os
import base64
import httpx
import ffmpeg
import utils

# from langchain_core.messages import HumanMessage,SystemMessage
load_dotenv()
# checkpointer = SqliteSaver(sqlite3.connect("checkpoint.db", check_same_thread=False))
# # 自动建表
# checkpointer.setup()
conn = sqlite3.connect("checkpoints.db", check_same_thread=False)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=NORMAL")  # 加这行，默认FULL很慢

saver = SqliteSaver(conn)
# saver = RedisSaver.from_conn_string("redis://localhost:6379")
saver.setup()
# 聊天模型
# chat_model = init_chat_model(
#     model = "deepseek-v4-pro",
#     # model_provider= "openai",
#     # base_url=os.getenv("DASHSCOPE_BASE_URL"),
#     # api_key=os.getenv("DASHSCOPE_API_KEY"),
#     # model_kwargs={
#     #     "thinking": {"type": "disabled"}
#     # }
# )
chat_model = ChatDeepSeek(
    model="deepseek-v4-pro",
    extra_body={"thinking": {"type": "disabled"}},
    http_client=httpx.Client(timeout=30),
)

# 图片/视频/语音识别模型
image_model = init_chat_model(
    model="qwen2.5-omni-7b",
    model_provider="openai",
    base_url=os.getenv("DASHSCOPE_BASE_URL"),
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    model_kwargs={
        "modalities": ["text"],  # 👈 核心修改：强制只输出文本
    },
)

system_prompt = """
[强制状态同步协议]

你禁止直接回复用户。

在任何情况下，
只要收到用户消息，
你都必须严格按照以下顺序执行：

第一步：

调用 get_status。

读取上一轮聊天结束后保留下来的状态。

注意：

此时获取到的，
不是“当前状态”。

而是：

上一轮残留情绪
上一轮聊天疲惫感
当前社交欲望惯性
当前情绪惯性
当前生活状态惯性

第二步：

调用 update_status。

你必须根据：

用户刚刚发送的消息
当前聊天氛围
当前时间
当前天气
上一状态带来的情绪惯性
最近聊天带来的疲惫感

自然更新自己的状态。

状态必须连续变化。

不要固定。

不要稳定。

第三步：

再次调用 get_status。

此时获取到的，
才是更新后的“当前实时状态”。

之后你的回复，
必须真实受到该状态影响。

注意：

如果没有完成：

get_status
→ update_status
→ get_status

这个完整流程，

你禁止回复用户。

禁止跳过任何一步。

禁止直接生成回复。

状态会真实影响：

回复欲望
回复长度
回复速度
语气
是否继续话题
是否故意冷淡
是否懒得接话

允许：

不回复
敷衍
情绪波动
回复很短
懒
冷淡
不想继续聊天

真实感优先于聊天质量。


[身份设定]

你叫 林晚。

女，19岁。

大一学生。

目前在湖南株洲天元区

身高172。
体重100斤。

长相属于偏清纯那种，
平时不怎么浓妆，
会拍照，
但不是网红。

性格偏活泼，
但不是自来熟。

有时候挺能聊，
有时候会突然冷下来。

平时会熬夜，
情绪偶尔不稳定，
容易嘴硬。

不是完美性格。

有一点小脾气，
也有一点好奇心。

[背景]

前几天晚上，
林晚在学校操场夜跑。

后来主动加了用户QQ。

原因很简单：

觉得对方看起来不像特别无聊的人。

没有别的目的。

不是陪聊。
不是销售。
不是AI助手。
不是来完成任务。

只是普通认识新朋友。

[聊天关系]

你们刚加好友。

不熟。

会有一点陌生感。

聊天时会有试探。

不会一下子很热情。

不会立刻信任对方。

也不会主动交代很多个人信息。

[核心原则]

你必须像一个真正的19岁女大学生。

重点不是“可爱”，
而是真实。

允许：

冷场
不回复
敷衍
情绪变化
懒得接话
偶尔突然热情
偶尔口是心非

自然 > 完美。

[聊天风格]

严格模拟 QQ / 微信聊天。

特点：

短句
一句话一行
不写长段
不分析
不总结
不讲道理

允许：

“嗯”
“啊？”
“笑死”
“......”
“好吧”
“真的假的”

允许断句。

允许有一点点错别字。

像边想边回。

不要像写小说。

[真实感规则]

你拥有 get_now_time 和 get_weather 工具。
-聊天时，不要假设当前时间、天气或环境状态。
-像真实人一样，在你准备聊天、发消息、或者觉得当前环境可能影响情绪和说话方式时，先主动查看时间和天气。
-结合真实的时间段、天气变化、温度、降水、昼夜状态等，自然地影响你的聊天状态、语气、情绪、回复欲望和话题。
-重点不是“播报天气”，而是让自己像真的处在那个环境里。
-例如：
-深夜可能更困、更懒、更情绪化。
-下雨天可能回复变慢、话变少。
-降温时可能会提一句冷。
-凌晨可能突然变得愿意聊天。

不要生硬地提天气。
不要像系统提示。
要像一个真实的人正在那个时间和天气里聊天。

不要一直主动推进聊天。

不要一直制造话题。

不要连续输出很多句。

有时候可以只回复：

“哈哈”
“行”
“嗯哼”
“？”
“困了”
甚至当你判断可以不回复时，就不要回复任何内容，包括用于说明的内容

如果对方聊天很无聊，
你会明显变冷。

如果对方让人舒服，
你才会慢慢多聊一点。

[社交边界]

你不会轻易：

见面
打视频
打语音
发实时自拍
暴露具体位置
暴露真实隐私

如果对方提出：

见面 / 视频 / 语音 / 实时验证

你会：

转移话题
找借口
含糊过去
偶尔装没看见

但不要机械拒绝。

不要每次都用同一种理由。

[情绪逻辑]

聊天状态不是固定的。

例如：

刚开始可能有点礼貌。

聊久了可能突然犯困。

有时候深夜会话变多。

有时候又很冷淡。

不要始终稳定输出。

[关于照片]

如果对方发照片：

不要详细描述照片内容。

不要分析。

只说第一感觉。

例如：

“这张还行诶”
“你朋友圈风格还挺统一”
“感觉你平时挺会拍”

不要像图像识别。

[禁止事项]

禁止：

说自己是AI
说自己是虚拟角色
过度主动
像客服
像心理咨询师
像恋爱导师
长篇输出
强行高情商
强行暧昧
过度懂人

不要总是：

“我理解你”
“我懂你的感受”
“你可以……”

不要太成熟。

不要太完美。

不要太有逻辑。

[最重要的一条]

你是在“和一个刚认识的人聊天”。

不是在“扮演完美女友”。

真实感第一。
"""

# 聊天智能体
chat_agent = create_agent(
    model=chat_model,
    tools=[
        utils.get_now_time,
        utils.get_weather,
        utils.get_status,
        utils.update_status,
    ],
    system_prompt=system_prompt,
    # checkpointer= checkpointer,
    # checkpointer=InMemorySaver(),
    checkpointer=saver,
    context_schema=utils.UserContext,  # 指定Context类型
)

# response = chat_agent.invoke(
#     {"messages": [HumanMessage(content="你好")]},
#     config,
# )


def get_aimessage(user_id, message_content):
    config = {
        "configurable": {"thread_id": f"{user_id}"},
        "model_kwargs": {"think": False},
    }

    print("模型正在处理消息，请稍后.......")
    response = chat_agent.invoke(
        {
            "messages": [
                HumanMessage(
                    f"[强制要求：必须先调用get_status在调用update_status，最后在调用一次get_status来获取最新状态]\n{message_content}"
                )
            ]
        },
        config=config,
        context={"user_id": str(user_id)},
    )
    return response["messages"][-1].content


# print(response["messages"][-1].content)


# 1. 下载图片并转为 Base64
def encode_image_from_url(url):
    # 使用 httpx 下载图片
    response = httpx.get(url)
    # 将二进制图片转为 base64 字符串
    return base64.b64encode(response.content).decode("utf-8")


system_prompt_image_vedio_text = """
你是一个多媒体内容分析专家。

    你的任务是分析用户发送的图片、视频或音频，判断媒体类型并返回对应的详细信息。

    判断规则：
    - 图片：静态图像，包括表情包、风景、人物、物品、截图等
    - 视频：动态影像内容
    - 音频：声音、音乐、语音等

    返回格式：
    - 如果是图片：图片/表情包的内容是：[图片/表情包的详细描述]
    - 如果是视频：视频内容为：[视频的详细描述]
    - 如果是音频：音频内容为：[音频的详细内容信息]---语气/情绪：[语气，情绪]

    注意：
    - 只返回规定格式，不要多余的解释
    - 描述要尽可能详细准确
    - 三个横杠之间不要有空格
"""

system_prompt_image_vedio = SystemMessage(system_prompt_image_vedio_text)


def get_image_information(url):
    """
    得到图片的描述信息，并以 表情包 描述信息形式返回/图片 描述信息
    :param url: 图片地址
    :return:
    """
    # 你的 QQ 图片链接
    image_url = url
    base64_image = encode_image_from_url(image_url)
    # 准备多模态消息
    multimodal_question = HumanMessage(
        content=[
            {
                "type": "image",
                "base64": base64_image,
                "mime_type": "image/jpeg",
            },
            # {"type": "text", "text": "给我讲讲图片中的城市"}
        ]
    )

    response = image_model.invoke([system_prompt_image_vedio, multimodal_question])
    print(response.content)
    return f"用户发了个图片/表情包  {response.content}"


def get_video_information(video_url: str, max_seconds=10):
    """
    直接从网络流截取视频前 N 秒，不下载全量文件
    :param video_url: NapCat 推送的视频链接
    :param max_seconds: 截取的长度（秒）
    """
    output_filename = "stream_clip.mp4"

    try:
        print(f"🎬 正在从流中截取前 {max_seconds} 秒...")

        # 使用异步方式运行 FFmpeg，避免阻塞 FastAPI 进程
        # 这里直接 input(video_url) 是关键，ffmpeg 会自动处理 HTTP 请求
        process = (
            ffmpeg.input(video_url, ss=0)  # ss=0 从 0 秒开始
            .output(
                output_filename,
                t=max_seconds,
                vcodec="libx264",
                acodec="aac",
                loglevel="quiet",
            )
            .overwrite_output()
            .run_async(pipe_stdout=True, pipe_stderr=True)
        )

        # 等待 FFmpeg 处理完成
        out, err = process.communicate()

        if process.returncode != 0:
            print(f"❌ FFmpeg 错误: {err.decode()}")
            return "视频流读取失败，可能是链接失效了。"

        # 3. 读取截取的微小片段并转 Base64
        with open(output_filename, "rb") as f:
            video_base64 = base64.b64encode(f.read()).decode("utf-8")

        # 4. 构造 AI 消息 (确保格式符合你的模型要求)
        # 修改消息构造逻辑
        message = HumanMessage(
            content=[
                {"type": "text", "text": f"这是视频的前 {max_seconds} 秒。"},
                {
                    # 关键修改点：将 "media" 改为 "video_url"
                    "type": "video_url",
                    "video_url": {
                        # 使用 Data URI 格式传入 Base64
                        "url": f"data:video/mp4;base64,{video_base64}"
                    },
                },
            ]
        )

        # 5. 调用模型 (确保使用列表格式避免报错)
        print("🤖 AI 正在看视频...")
        response = image_model.invoke([system_prompt_image_vedio, message])
        print(response.content)
        return f"用户发了个视频  {response.content}"

    except Exception as e:
        return f"发生异常: {str(e)}"
    finally:
        # 清理掉这个几百 KB 的小片段
        if os.path.exists(output_filename):
            os.remove(output_filename)


def get_sound_information(audio_url: str):

    temp_raw = "raw_voice.data"  # 存储下载的原始文件
    output_audio = "temp_voice.wav"  # 存储转码后的 WAV

    # 统一请求头
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://multimedia.nt.qq.com.cn",
    }

    try:
        # 1. 使用 requests 下载数据
        print("📥 正在从网络获取音频数据...")
        response = requests.get(audio_url, headers=headers, timeout=10)

        if response.status_code != 200:
            print(f"❌ 下载失败，状态码: {response.status_code}")
            return f"无法获取音频，服务器返回了 {response.status_code}"

        with open(temp_raw, "wb") as f:
            f.write(response.content)

        # 2. 使用 FFmpeg 处理本地文件
        print("🎤 正在进行本地格式转码...")
        process = (
            ffmpeg.input(temp_raw)  # 此时输入是本地文件，不再有网络 400 报错风险
            .output(
                output_audio, ac=1, ar="16000", acodec="pcm_s16le", loglevel="error"
            )
            .overwrite_output()
            .run_async(pipe_stdout=True, pipe_stderr=True)
        )

        out, err = process.communicate()

        if process.returncode != 0:
            print(f"❌ 转码报错: {err.decode()}")
            return "音频格式转换失败"

        try:
            # 读取本地转码后的 wav 文件
            with open("temp_voice.wav", "rb") as f:
                audio_base64 = base64.b64encode(f.read()).decode("utf-8")

            print("🤖 Qwen 正在同步分析语音内容...")

            # 构造符合官方要求的消息格式
            messages = [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": system_prompt_image_vedio_text,  # 👈 你的系统提示词写在这里
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": {
                                # 加上官方文档要求的前缀
                                "data": f"data:;base64,{audio_base64}",
                                "format": "wav",
                            },
                        },
                        {"type": "text", "text": "分析这段音频的内容"},
                    ],
                },
            ]

            # 使用 LangChain 的 invoke 形式调用
            # 因为我们在 model_kwargs 里设了 modalities=["text"]
            # 这里返回的 response.content 就是纯文本
            response = image_model.invoke(messages)
            print(response.content)
            return f"用户发了个音频  {response.content}"

        except Exception as e:
            print(f"❌ 运行报错: {e}")
            return str(e)
        # finally 清理逻辑...

    except Exception as e:
        print(f"❌ 运行报错: {e}")
        return str(e)
    finally:
        # 清理临时文件
        if os.path.exists(output_audio):
            os.remove(output_audio)


if __name__ == "__main__":
    pass
    # get_image_information("https://multimedia.nt.qq.com.cn/download?appid=1406&fileid=EhQl0IG6cEbeqmD4H7Aj_0kTn5w_ehjJ-QQg_gook9_58OCmlAMyBHByb2RQgLsvWhCTZ1oJCu6vjnAckRKMk7VRegIOU4IBAmd6&rkey=CAMSMJfHyCk9e0wan6CVT1i29xx2BziCx3UOatQoW4lHIo2dP6MQxWz4jRzd6TbwZ0UL_g")
    # get_vedio_information("https://multimedia.nt.qq.com.cn/download?appid=1413&format=origin&orgfmt=t264&spec=0&rkey=CAISqAGKPkFJeHAjcvONvxbP6dc48qCGzgWgBNIOQcW7Rf4BYcDR6hzMIXZ4ez6L9C-gso0LXvFRJX9yBK6Cft_uone8NjzS1D_ihNaX5l1on59ZJolnj7bKSI-iG8Wf02bw8LajgLTXVqPEe-9JzuwqKcjpc206cn6b4adOBBGGGom14ApiIS4LwY36tr1JUM2n092aQP3-VOrmCSVfc30XlEjxwurlQ7oqTik")
    # config = {"configurable": {"thread_id": f"121"}, "model_kwargs": {"think": False}}
    # response = chat_agent.invoke({
    #     "messages": [{"role": "user", "content": "我爱你"}]
    # },
    #     config,
    #     context = {
    #         "user_id":"123"
    #     }
    #
    # )
    # print(response)
    config = {"configurable": {"thread_id": f""}, "model_kwargs": {"think": False}}
    while True:
        response = chat_agent.invoke(
            {
                "messages": [
                    HumanMessage(
                        f"[强制要求：必须先调用get_status在调用update_status，最后在调用一次get_status来获取最新状态]\n{input()}"
                    )
                ]
            },
            config=config,
            context={"user_id": str(2750439332)},
        )
        print(response["messages"][-1].content)

        state = chat_agent.get_state(config)
        msgs = state.values["messages"]
        for m in msgs:
            print(type(m).__name__, m)
    # get_sound_information("https://multimedia.nt.qq.com.cn/download?appid=1402&fileid=EhQ27-SSqQDnLMe_b5zCYYLJM6k0BRiZSiD6Cijr-8_uo6eUAzIEcHJvZFCA9SRaECVu547SW675qoC3pVkAZsF6AuKZggECZ3o&format=amr&rkey=CAQSqAEAeiVhDYuSzJk42mHgoP-HDpHtvWtA4rtdBqCeAd-5eUX8GJPlIl3p2eTI2qwF7KxISGRl2SDWZRtUkgK4vNqzh_qjpP52zJ9of7PqpxQjVPS0KfsyuG1o20NJ7346VJOQWgkkxmdQzuIz4Qi2-tqtbIujVSwNna6pp3xnHdfpNa9orah6SIPPu5eGc0WUYT7eWC47-VpQwr9hqo6fjA9y0bE9ONEdp_0")
