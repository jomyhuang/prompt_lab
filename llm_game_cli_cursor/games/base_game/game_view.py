import streamlit as st
from agent_tool import add_system_message, add_user_message, add_assistant_message

def render_game_stats(game_state: dict):
    """渲染游戏状态信息
    
    显示关键游戏信息:
    - 当前回合数
    - 游戏阶段
    - 游戏状态(进行中/结束)
    
    Args:
        game_state: 当前游戏状态字典
    """
    st.markdown(f"""
    - 当前回合: **{game_state['current_turn']}**
    - 游戏阶段: **{game_state['phase']}**
    - 游戏状态: **{'进行中' if not game_state['game_over'] else '已结束'}**
    """)

def render_welcome_screen():
    """显示欢迎界面"""
    # 添加模式标识到标题
    mode_indicator = "⚡ Streaming" if st.session_state.streaming else "🔄 Invoke"
    st.header(f"🎮 欢迎来到LLM游戏框架！({mode_indicator})")
    
    # 使用列来居中显示内容
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        ### 关于游戏 Gen By Cursor
        这是一个基于大语言模型的游戏框架，支持：
        
        - 基于LangGraph的状态管理
        - Human-in-loop交互模式
        - 标准化的Streamlit UI组件
        - 清晰的提示词工程
        
        ### 游戏特点
        1. 支持多种LLM模型
        2. 灵活的状态管理
        3. 实时对话交互
        4. 可扩展的游戏逻辑
        
        ### 准备好了吗？
        """)
        
        # 开始游戏按钮
        if st.button("开始游戏", use_container_width=True):
            st.session_state.game_started = True
            st.session_state.current_message = "游戏开始！请选择你的行动。"
            st.session_state.gui_feedback = "start"
            st.session_state.gui_feedback_params = {
                "phase": "game start",
                "game_started": True
            }
            add_system_message("start run game agent....")
            st.session_state.require_update = True

def render_game_view():
    """渲染游戏主界面
    
    显示:
    - 游戏标题
    - 当前游戏状态
    - 游戏信息
    - 可用动作列表
    """
    
    # 获取游戏状态
    game_state = st.session_state.game_agent.get_game_state()
    
    # 如果游戏未开始，显示欢迎界面
    if not st.session_state.game_started:
        render_welcome_screen()
        return
    
    # 修改标题显示，添加模式标识
    mode_indicator = "⚡ Streaming" if st.session_state.streaming else "🔄 Invoke"
    st.header(f"🎮 LLM Game Framework ({mode_indicator})", divider="rainbow")

    # 显示游戏状态
    st.caption(f"当前游戏阶段: {game_state['phase']}")
    render_game_stats(game_state)
    
    # 显示当前消息
    st.info(st.session_state.current_message)
    if game_state["info"]:
        st.write(game_state["info"])
    
    # 显示可用动作
    if game_state["valid_actions"]:
        st.write("可用动作:", ", ".join(game_state["valid_actions"])) 