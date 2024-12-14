from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import WebBaseLoader
from langchain.chains import StuffDocumentsChain
from langchain.chains.llm import LLMChain
from langchain.prompts import PromptTemplate

import google.generativeai as genai

import os
from dotenv import load_dotenv
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


#os.environ.setdefault("GOOGLE_API_KEY","KEY")

#os.environ['GOOGLE_API_KEY'] = "KEY"
os.environ['USER_AGENT'] = "MyCustomAgent/1.0"

#Initialize Model
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

for model in genai.list_models():
    print(model.name)

model = genai.GenerativeModel("gemini-1.5-flash")
#gemini-2.0-flash-exp
print('genai.GenerativeModel')
response = model.generate_content("今天天气如何？ 你从哪里来？")
print(response.text)

#llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", transport='rest' )
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", api_key=os.getenv("GOOGLE_API_KEY") )

# 发送消息并获取输出
print('llm.invoke')
result = llm.invoke("简单介绍什么是langchain，你能说出来吗？")
print(result.content)