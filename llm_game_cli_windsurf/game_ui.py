import streamlit as st
from typing import Dict, Any, List, Optional
from game_state import GameState
import logging

logger = logging.getLogger(__name__)

def init_session_state():
    """初始化session state"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "require_update" not in st.session_state:
        st.session_state.require_update = False

def render_sidebar(game_state: GameState):
    """渲染侧边栏
    
    Args:
        game_state: 当前游戏状态
    """
    with st.sidebar:
        st.header("🎮 游戏控制台")
        
        # 游戏控制按钮
        if st.button("开始新游戏", use_container_width=True):
            st.session_state.require_update = True
            
        # 游戏状态展示
        with st.expander("🔍 游戏状态", expanded=True):
            st.json(game_state)

def render_game_view(game_state: GameState):
    """渲染游戏主视图
    
    Args:
        game_state: 当前游戏状态
    """
    # 分割界面为游戏区和聊天区
    game_col, chat_col = st.columns([0.6, 0.4])
    
    with game_col:
        st.header("游戏区")
        render_game_area(game_state)
    
    with chat_col:
        st.header("对话区")
        render_chat_area(game_state)

def render_game_area(game_state: GameState):
    """渲染游戏区域
    
    Args:
        game_state: 当前游戏状态
    """
    # 游戏数据展示
    st.subheader("游戏数据")
    st.write(game_state["game_data"])
    
    # 玩家数据展示
    st.subheader("玩家数据")
    st.write(game_state["player_data"])

def render_chat_area(game_state: GameState):
    """渲染聊天区域
    
    Args:
        game_state: 当前游戏状态
    """
    # 显示消息历史
    for message in game_state["messages"]:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # 用户输入
    if prompt := st.chat_input():
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.require_update = True

def render_action_view(game_state: GameState):
    """渲染动作视图
    
    Args:
        game_state: 当前游戏状态
    """
    st.subheader("可用动作")
    
    # 这里可以根据游戏状态动态生成可用动作按钮
    if st.button("执行动作"):
        st.session_state.require_update = True

def update_ui():
    """更新UI状态"""
    if st.session_state.require_update:
        st.session_state.require_update = False
        st.rerun()
