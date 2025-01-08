import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

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