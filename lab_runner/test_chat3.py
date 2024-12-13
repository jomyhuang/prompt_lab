# 1. 环境准备
# 安装必要的 Python 包
# pip install langchain google-generativeai python-dotenv

import os
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import (
    HumanMessage,
)
from dotenv import load_dotenv

load_dotenv()

# 2. 配置 Google Gemini API 密钥和 Google Cloud 项目
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
#GOOGLE_PROJECT_ID = "os.getenv("GOOGLE_PROJECT_ID")" # 可选
GOOGLE_PROJECT_ID = "Gemini API" # 可选


print(f"GOOGLE_API_KEY: {GOOGLE_API_KEY}") # 打印 API 密钥（“KEY” + GOOGLE_API_KEY）
print(f"GOOGLE_PROJECT_ID: {GOOGLE_PROJECT_ID}") # 打印项目 ID（“PROJECT_ID” + GOOGLE_PROJECT_ID）
# 3. 初始化 Gemini 模型
genai.configure(api_key=GOOGLE_API_KEY)

# 初始化 Langchain 支持的 Gemini 模型
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=GOOGLE_API_KEY, project=GOOGLE_PROJECT_ID)
# model="gemini-pro", 其他选择见 google-generativeai 支持的模型列表


# 4.  创建提示词
messages = [
    HumanMessage(content="你好，请问今天天气怎么样？") # 你可以修改提示词为其他你感兴趣的内容
]


# 5. 使用 Langchain 执行查询

try:
    result = llm(messages)
    print(result.content)
except Exception as e:
    print(f"An error occurred: {e}")

