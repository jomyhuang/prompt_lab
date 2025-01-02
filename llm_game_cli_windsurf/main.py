import streamlit as st
from game_state import GameStateManager
from game_graph import build_game_graph
from game_ui import (
    init_session_state,
    render_sidebar,
    render_game_view,
    render_action_view,
    update_ui
)
from llm_interface import LLMInterface
from langgraph.checkpoint.memory import MemorySaver
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_game():
    """初始化游戏
    
    初始化各个组件并设置初始状态
    """
    if "game_state_manager" not in st.session_state:
        st.session_state.game_state_manager = GameStateManager()
    
    if "llm_interface" not in st.session_state:
        st.session_state.llm_interface = LLMInterface()
    
    if "game_graph" not in st.session_state:
        checkpointer = MemorySaver()
        st.session_state.game_graph = build_game_graph(checkpointer)

def main():
    """主函数"""
    st.set_page_config(
        page_title="LLM游戏框架",
        page_icon="🎮",
        layout="wide"
    )
    
    # 初始化
    init_session_state()
    init_game()
    
    # 获取当前游戏状态
    game_state = st.session_state.game_state_manager.get_state()
    
    # 渲染UI
    render_sidebar(game_state)
    render_game_view(game_state)
    render_action_view(game_state)
    
    # 处理状态更新
    if game_state["ui_state"]["require_update"]:
        update_ui()

if __name__ == "__main__":
    main()
