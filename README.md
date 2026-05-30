# 🤖 QQ AI 女友机器人

> 基于 NapCatQQ + DeepSeek 实现的 QQ AI 伴侣，支持多模态输入，24小时在线陪你聊天。

---
### 具体代码在master分支。



## ✨ 功能

- 💬 接收并识别：文本、表情包、图片、视频、音频
- 🤖 AI 理解内容，智能回复
- ⚡ 实时响应，24小时在线
- 📤 当前支持发送：文本消息

---

## 🛠 技术栈

- **Python** — 核心逻辑
- **NapCatQQ** — QQ 协议端，负责收发消息
- **DeepSeek API** — AI 对话模型
- **HTTP** — NapCatQQ 与程序之间的通信方式

---

## 📦 环境要求

- Python 3.10+
- [NapCatQQ](https://github.com/NapNeko/NapCatQQ)（需单独下载安装）
- DeepSeek API Key

---

## 🚀 快速开始

### 第一步：配置 NapCatQQ

1. 下载并启动 NapCatQQ
2. 扫码登录你的 QQ 账号
3. 进入设置，配置 HTTP 服务器和客户端：

```
HTTP 服务器（接收消息）
  监听端口：9988（可自定义）

HTTP 客户端（上报消息给程序）
  上报地址：http://127.0.0.1:7788（可自定义）
```

### 第二步：安装依赖

```bash
git clone https://github.com/你的用户名/你的仓库名.git
cd 你的仓库名

pip install -r requirements.txt
# 或 uv sync
```

### 第三步：配置环境变量

复制 `.env.example` 为 `.env`，填入配置：

```bash
cp .env.example .env
```

```env
DEEPSEEK_API_KEY=sk-你的key

# NapCatQQ HTTP 服务器地址（发消息用）
NAPCAT_URL=http://127.0.0.1:3000

# 本程序监听端口（接收 NapCatQQ 上报）
LISTEN_PORT=5000
```

### 第四步：启动

```bash
python main.py
```

---

## ⚙️ 自定义端口

如果修改了 NapCatQQ 的端口，对应修改 `.env` 里的地址即可，无需改代码。

---

## 📁 项目结构

```
├── main.py          # 入口文件
├── .env.example     # 环境变量模板
├── requirements.txt
└── README.md
```

---

## 📌 注意事项

- NapCatQQ 必须保持运行状态，否则收不到消息
- DeepSeek API Key 请妥善保管，不要上传到 GitHub
- 本项目仅供学习交流使用

---

## 📬 联系

有问题欢迎提 Issue 或小红书找我。
