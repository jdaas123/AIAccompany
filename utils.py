import requests
from langchain.tools import tool
import datetime
import json
import os
# 方式2：使用TypedDict定义Context
from typing_extensions import TypedDict


from langgraph.prebuilt import ToolRuntime

class UserContext(TypedDict):
    """运行时上下文类型"""
    user_id: str


# =========================
# 全局状态字典
# =========================
status = {}


@tool
def update_status(
        runtime:ToolRuntime[UserContext],
        is_hidden: bool,  # 强制：必须决定是否隐藏
        delay_seconds: int,  # 强制：必须决定延迟秒数
        fav_delta: int,
        mood: str = None,
        energy: str = None,
        reply_style: str = None,
        hunger: str = None,
        current_scene: str = None,
        current_action: str = None

):
    """
    修改机器人的状态（必须决定是否回复以及延迟时长）。

    :param is_hidden: 是否隐藏回复（True/False）。
    :param delay_seconds: 回复延迟的秒数（整数）。
    :param fav_delta: 好感度变动值。
    :param mood: 更新主情绪描述（如 "开心", "委屈", "生气"）
    :param energy: 更新精力状态（如 "很精神", "平常", "想睡觉"）
    :param reply_style: 更新聊天风格（如 "娇羞", "冷淡", "热情"）
    :param hunger: 更新饥饿状态（如 "饱腹", "有点饿", "饿极了"）
    :param current_scene: 更新当前的场景（比如"家"，"宿舍","外面"）
    :param current_action: 更新当前正在做的动作
    """
    # print(f"ai 调用update_status: 延迟={delay_seconds}s, 隐藏={is_hidden},好感度变化={fav_delta}")
    print("=" * 10, f"ai调用 ----> update_status: 延迟={delay_seconds}s, 隐藏={is_hidden},好感度变化={fav_delta} ", "=" * 10)
    global status

    user_id = runtime.context.get("user_id",None)
    if not user_id:
        print("user_id不存在，更新状态失败")
        return

    # 1. 处理数值累加（好感度）
    if fav_delta != 0:
        status["favorability"] = max(0, min(1000, status["favorability"] + fav_delta))

    # 2. 强制覆盖参数
    status["is_hidden"] = is_hidden
    status["delay_seconds"] = delay_seconds

    # 3. 处理可选覆盖参数
    if mood: status["mood"] = mood
    if energy: status["energy"] = energy
    if reply_style: status["reply_style"] = reply_style
    if hunger: status["hunger"] = hunger
    if current_scene: status["current_scene"] = current_scene
    if current_action: status["current_action"] = current_action

    now_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status["last_update"] = now_time

    with open(f"./status/{user_id}.json","w") as f:
        json.dump(status,f,ensure_ascii=True,indent=2)
    return "状态已更新。注意：请务必在回复前调用 get_status 确认你最终的心理状态。"



@tool
def get_status(runtime:ToolRuntime[UserContext]):
    """
    获取机器人当前的所有实时数值状态。
    模型必须在每一轮对话开始时首先调用此工具，以了解当前的各项参数。
    参数:user_id :用户的id
    """
    print("="*10,"ai调用-----> get_status ","="*10)
    # 格式化输出，方便 AI 直接阅读每一个键值对
    # 使用 Markdown 块包裹，增加视觉权重，防止模型忽略
    status_text = "### 当前状态 ###\n"
    user_id = runtime.context.get("user_id",None)
    if not user_id:
        print("user_id不存在！调用工具失败")
        return
    print(f"此次调用工具的user --- > {user_id}")
    global status

    #如果不存在状态文件，就创建
    if not os.path.exists(f"./status/{user_id}.json"):
        print(f"不存在状态信息文件，正在创建状态文件 ---> ./status/{user_id}.json")
        with open(f"./status/{user_id}.json","w") as f:
            data = {
                "favorability": 20,  # 好感度 (0-1000)
                "mood": "normal",  # 当前主情绪
                "energy": "平常",  # 精力
                "reply_style": "natural",  # 当前聊天风格
                "hunger": "有点饿",  # 饥饿度
                "is_hidden": False,  # 是否隐藏/不想聊天
                "delay_seconds": 30,  # 回复延迟 (秒
                "current_scene": "宿舍",  # 当前场景
                "current_action": "玩手机",  # 当前动作
                "last_update": None,  # 上次更新时间
            }
            json.dump(data,f,ensure_ascii=True,indent=2)
        print(f"初始化完毕 ---> ./status/{user_id}.json")


    with open(f"./status/{user_id}.json","r") as f:
        status = json.load(f)

    for key, value in status.items():
        status_text += f"- **{key}**: {value}\n"
    print(status_text)
    # print("=" * 10, "ai调用工具结束-----> get_status ", "=" * 10)
    return status_text.strip()

@tool
def get_now_time() -> str:
    """当你需要知道现在的时间（年-月-日 时:分:秒）时，请调用此工具。"""
    print("=" * 10, "ai调用-----> get_now_time ", "=" * 10)
    now_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("ai 获取当前时间 ---> ",now_time)
    return now_time



@tool
def get_weather(location: str = "113.13195,27.82704") -> str:
    """
    查询实时天气的工具。
    参数 location: 经纬度坐标，格式为 '经度,纬度'（例如上海是 '121.47,31.23'）。
    """
    print("=" * 10, "ai调用-----> get_weather ", "=" * 10)
    # 填入你的彩云天气 API Token
    token = "pUPG1qurCujlGl9j"
    # 构建请求 URL (使用实时天气接口)
    url = f"https://api.caiyunapp.com/v2.6/{token}/{location}/realtime"
    print(url)

    try:
        print("正在查询")
        response = requests.get(url, timeout=10)
        data = response.json()
        print("查询成功")
        if data.get("status") == "ok":
            realtime = data["result"]["realtime"]

            # 提取核心数据
            temp = realtime["temperature"]  # 气温
            apparent_temp = realtime["apparent_temperature"]  # 体感温度
            humidity = realtime["humidity"] * 100  # 湿度转百分比
            skycon = realtime["skycon"]  # 天气现象简码
            wind_speed = realtime["wind"]["speed"]  # 风速
            precipitation = realtime["precipitation"]["local"]["intensity"]  # 降水强度

            # 将天气简码转换为中文（彩云天气标准）
            skycon_dict = {
                "CLEAR_DAY": "晴（白天）", "CLEAR_NIGHT": "晴（夜间）",
                "PARTLY_CLOUDY_DAY": "多云", "PARTLY_CLOUDY_NIGHT": "多云",
                "CLOUDY": "阴", "LIGHT_HAZE": "轻度雾霾", "MODERATE_HAZE": "中度雾霾",
                "HEAVY_HAZE": "重度雾霾", "LIGHT_RAIN": "小雨", "MODERATE_RAIN": "中雨",
                "HEAVY_RAIN": "大雨", "STORM_RAIN": "暴雨", "FOG": "雾",
                "LIGHT_SNOW": "小雪", "MODERATE_SNOW": "中雪", "HEAVY_SNOW": "大雪",
                "STORM_SNOW": "暴雪", "DUST": "浮尘", "SAND": "沙尘", "WIND": "大风"
            }
            weather_text = skycon_dict.get(skycon, "未知天气")

            # 拼接回复字符串
            res = (
                f"当前位置天气：{weather_text}，"
                f"气温：{temp}℃（体感温度：{apparent_temp}℃），"
                f"空气湿度：{humidity:.0f}%，"
                f"风速：{wind_speed} m/s"
            )
            print(res)
            return res
        else:
            print("未知天气，查询不到")
            return "未知天气，查询不到"
    except:
        print("查询失败")
        return "查询失败"


if __name__ == '__main__':
    print(get_status())