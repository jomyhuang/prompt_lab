import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def add_system_message(message: str):
    """添加系统消息到聊天历史
    
    Args:
        message: 系统消息内容
    """
    st.session_state.messages.append(SystemMessage(content=message))
    st.session_state.require_update_chat = True
    st.session_state.require_update = True

def add_user_message(message: str):
    """添加用户消息"""
    st.session_state.messages.append(HumanMessage(content=message))
    st.session_state.require_update_chat = True
    st.session_state.require_update = True

def add_assistant_message(message: str):
    """添加助手消息"""
    st.session_state.messages.append(AIMessage(content=message))
    st.session_state.require_update_chat = True
    st.session_state.require_update = True 


def init_my_model(use_model:str="deepseek"):
    
    if use_model == "google":
        model = "gemini-pro"
        print(f"使用Gemini模型 {model}")
        return ChatGoogleGenerativeAI(
            api_key=os.getenv("GOOGLE_API_KEY"),
            model=model,
            temperature=0,
            streaming=True
        )
        
    elif use_model == "deepseek":
        model = "deepseek-chat"
        base_url = os.getenv("DEEPSEEK_API_BASE")
        print(f"使用DeepSeek模型 {model}")
        return ChatOpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            model=model,
            base_url=base_url,
            temperature=0,
            streaming=True
        )
      
    else:  # openai
        model = "gpt-3.5-turbo"
        base_url = os.getenv("OPENAI_API_BASE")
        print(f"使用OpenAI模型 {model}")
        return ChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            model=model,
            base_url=base_url,
            temperature=0,
            streaming=True
        )
