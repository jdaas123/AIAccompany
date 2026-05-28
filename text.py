# import requests


# BASE_URL = "https://api.deepseek.com"

# API_KEY = "sk-09d98c7ed6e640968cff76806561fc22"


# response = requests.post(
#     f"{BASE_URL}/chat/completions",
#     headers={"Authorization": f"Bearer {API_KEY}"},
#     json={
#         "model": "deepseek-v4-pro",
#         "messages": [
#             {"role": "system", "content": "你是我女朋友"},
#             {"role": "user", "content": "hello"},
#         ],
#         "thinking": {"type": "disabled"},
#         # "reasoning_effort": "high",
#         "stream": False,
#     },
# )

# print(response.json())

# import os
# from openai import OpenAI

# client = OpenAI(
#     api_key = API_KEY, base_url="https://api.deepseek.com"
# )

# response = client.chat.completions.create(
#     model="deepseek-v4-pro",
#     messages=[
#         {"role": "system", "content": "You are a helpful assistant"},
#         {"role": "user", "content": "Hello"},
#     ],
#     stream=False,
#     reasoning_effort="high",
#     extra_body={"thinking": {"type": "enabled"}},
# )

# print(response.choices[0].message.content)


a = [1,2,34,5,6]
