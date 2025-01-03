import streamlit as st
import random
import time
import asyncio
from typing import Optional
from datetime import datetime
from game_graph import GameGraph, GameAction
from llm_interaction import LLMInteraction
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
import logging
from langgraph.types import interrupt, Command

logger = logging.getLogger(__name__)

def _init_session_state():
    """初始化会话状态
    
    使用st.session_state管理GUI状态:
    - 游戏是否已开始
    - 玩家信息
    - 当前消息
    - 界面更新标志
    - 处理状态标志
    """
    # logger.info(f"_init_session_state {time.time()}")
    if "initialized" not in st.session_state:
        # 游戏逻辑状态管理器
        st.session_state.llm_interaction = LLMInteraction()
        st.session_state.messages = []
        st.session_state.initialized = True
        st.session_state.thread_id = str(random.randint(1, 1000000))
        st.session_state.checkpointer = None
        
        # GUI状态
        st.session_state.game_started = False
        st.session_state.player_info = {}
        st.session_state.current_message = "欢迎来到游戏!"
        st.session_state._user_chat_input = None
        st.session_state.require_update = False
        st.session_state.processing_state = False

        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            # format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            format='%(levelname)s - %(message)s',
            force=True
        )

        if not logger.hasHandlers():
            console_handler = logging.StreamHandler()
            logger.addHandler(console_handler)

        add_system_message("欢迎来到游戏!")
        logger.info("_init_session_state Initialized")

def _init_gamegraph():
    # 初始化游戏LangGraph工作流
    # logger.info(f"_init_gamegraph {time.time()}")
    if "game_graph" not in st.session_state:
        # checkpointer = MemorySaver()
        # config = {"configurable": {"thread_id": st.session_state.thread_id}}
        # st.session_state.config = config

        # game_graph = GameGraph(checkpointer=checkpointer, thread_id=st.session_state.thread_id)
        game_graph = GameGraph()
        st.session_state.game_graph = game_graph
        st.session_state.checkpointer = game_graph.checkpointer
        st.session_state.thread_id = game_graph.thread_id
        config = {"configurable": {"thread_id": st.session_state.thread_id}}
        st.session_state.config = config

        # logger.info(f"_init_gamegraph {st.session_state.thread_id}")
        initial_state = st.session_state.game_graph.get_game_state()
        # st.session_state.game_state 用于取用便利, 不要做任何修改
        logger.info("_init_gamegraph before initial invoke start-to-route")
        state = st.session_state.game_graph.graph.invoke(initial_state, config=config)
        st.session_state.game_state = state
        st.session_state.game_graph.set_game_state(state)
        logger.info("_init_gamegraph after initial invoke start-to-route")


def render_sidebar_controls():
    """渲染侧边栏控制界面"""
    with st.sidebar:
        st.header("🛠️ 游戏控制台")

        # 手动更新按钮
        if st.button("手动更新界面"):
            st.rerun()

        # 显示游戏状态
        game_state = st.session_state.game_graph.get_game_state()

        if game_state:
            with st.expander("🔍 查看游戏状态", expanded=True):
                st.json(game_state, expanded=3)
        

def render_game_stats(game_state: dict):
    """渲染游戏状态信息
    
    Args:
        game_state: 当前游戏状态
    """
    st.markdown(f"""
    - 当前回合: **{game_state['current_turn']}**
    - 游戏阶段: **{game_state['phase']}**
    - 游戏状态: **{'进行中' if not game_state['game_over'] else '已结束'}**
    """)

def render_welcome_screen():
    """显示欢迎界面"""
    st.title("🎮 欢迎来到LLM游戏框架！")
    
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
            # 初始化游戏状态
            game_state = st.session_state.game_graph.get_game_state()
            # print("welcome screen game_state:", game_state)
            # 更新GUI状态
            st.session_state.game_started = True
            st.session_state.current_message = "游戏开始！请选择你的行动。"
            
            # 使用graph.invoke resume
            print(f"[welcome] Before start button invoke ----")
            config = {"configurable": {"thread_id": st.session_state.thread_id}}
            state = st.session_state.game_graph.graph.invoke(Command(resume="start"), config=config)
            st.session_state.game_state = state
            st.session_state.game_graph.set_game_state(state)
            print(f"[welcome] After start button invoke ----")
            
            st.session_state.require_update = True

def render_game_view():
    """渲染游戏主界面"""
    # 获取游戏状态
    game_state = st.session_state.game_graph.get_game_state()
    

    # 渲染侧边栏控制
    render_sidebar_controls()

    # 如果游戏未开始，显示欢迎界面
    if not st.session_state.game_started:
        render_welcome_screen()
        return
    
    st.header("🎮 LLM Game Framework", divider="rainbow")

    # 显示游戏状态
    st.caption(f"当前游戏阶段: {game_state['phase']}")
    render_game_stats(game_state)
    
    # 显示当前消息
    st.info(st.session_state.current_message)
    
    # 显示可用动作
    if game_state["valid_actions"]:
        st.write("可用动作:", ", ".join(game_state["valid_actions"]))

def render_chat_view():
    """渲染聊天界面"""
    # 渲染聊天消息历史
    chat_container = st.container(height=500)
    with chat_container:
        for message in st.session_state.messages:
            # message 采用langchain规范对话类型: SystemMessage, HumanMessage, AIMessage
            with st.chat_message(message.type):
                st.markdown(message.content)
    
    require_update = False
    # 渲染对话输入框
    user_input = st.chat_input("输入你的行动或问题...", key="chat_input")
    if user_input:
        add_user_chat_input(user_input)
        require_update = True

    return require_update

def render_action_view():

    # 只在游戏开始后显示动作区
    if not st.session_state.game_started:
        return
    
    """渲染玩家操作界面"""
    game_state = st.session_state.game_graph.get_game_state()
    
    if game_state["current_turn"] == "player":
        st.markdown("### 🎮 你的回合")
        
        # 创建按钮列
        button_cols = st.columns(3)
        
        # 根据可用动作显示按钮
        valid_actions = game_state["valid_actions"]
        if "play" in valid_actions:
            with button_cols[0]:
                if st.button("出牌", key="play", use_container_width=True):
                    add_user_message("测试goto")
                    # 使用graph.invoke resume
                    print(f"Before play button invoke ----")
                    config = {"configurable": {"thread_id": st.session_state.thread_id}}
                    state = st.session_state.game_graph.graph.invoke(
                        Command(goto="end"),
                        config=config
                    )
                    st.session_state.game_state = state
                    st.session_state.game_graph.set_game_state(state)
                    print(f"After play button invoke ----")
        
        if "end_turn" in valid_actions:
            with button_cols[1]:
                if st.button("结束回合", key="end_turn", use_container_width=True):
                    add_user_message("结束回合")
                    # 使用graph.invoke resume
                    print(f"Before end turn button invoke ----")
                    config = {"configurable": {"thread_id": st.session_state.thread_id}}
                    state = st.session_state.game_graph.graph.invoke(
                        Command(resume="end_turn"),
                        config=config
                    )
                    st.session_state.game_state = state
                    st.session_state.game_graph.set_game_state(state)
                    print(f"After end turn button invoke ----")
                
        with button_cols[2]:
            if st.button("给出建议", key="get_advice", use_container_width=True):
                add_user_chat_input("分析当前局势，给出建议")


def add_system_message(message: str):
    """添加系统消息"""
    st.session_state.messages.append(SystemMessage(content=message))
    st.session_state.require_update = True

def add_user_message(message: str):
    """添加用户消息"""
    st.session_state.messages.append(HumanMessage(content=message))
    st.session_state.require_update = True

def add_assistant_message(message: str):
    """添加助手消息"""
    st.session_state.messages.append(AIMessage(content=message))
    st.session_state.require_update = True

def add_user_chat_input(message: str):
    """添加用户聊天输入"""
    st.session_state._user_chat_input = message
    add_user_message(message)

def process_command_input(user_input: str):
    """处理用户命令输入
    
    Args:
        user_input: 用户输入
    """
    add_user_message(user_input)
    
    # 解析用户输入
    action = st.session_state.llm_interaction.parse_user_action(user_input)
    
    # 创建GameAction对象
    game_action = GameAction(
        action_type=action["action"],
        player_id="player",
        timestamp=datetime.now(),
        data=action["parameters"]
    )
    
    # 获取当前状态
    current_state = st.session_state.game_graph.get_game_state()
    
    # # 使用graph.invoke恢复执行
    # config = {"configurable": {"thread_id": st.session_state.thread_id}}
    # print(f"[process_command_input] Before invoke ----")
    # result = st.session_state.game_graph.game_graph.graph.invoke(
    #     Command(resume=action, update=current_state),
    #     config=config
    # )
    # print(f"[process_command_input] After invoke ----")
    
    # 更新游戏状态
    st.session_state.game_graph.update_state(result, game_action)
    st.session_state.require_update = True

async def _process_game_loop():
    """处理游戏循环"""
    require_update = False
    
    # 检查是否正在处理状态
    if st.session_state.processing_state:
        return False
        
    try:
        st.session_state.processing_state = True
        
        #检查是否有LLM响应
        if st.session_state._user_chat_input:
            game_state = st.session_state.game_graph.get_game_state()
            response = await st.session_state.llm_interaction.generate_ai_response(
                st.session_state._user_chat_input,
                game_state
            )
            add_assistant_message(response)
            st.session_state._user_chat_input = None
            require_update = True
        
        # 如果需要强制更新,重置标志并更新界面
        if st.session_state.require_update:
            st.session_state.require_update = False
            require_update = True
            
    finally:
        st.session_state.processing_state = False
        
    return require_update

async def main():
    """主函数"""
    # 设置页面配置
    st.set_page_config(
        page_title="🎮 LLM Game Framework",
        page_icon="🎮",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # 分割界面为游戏区和聊天区
    game_col, chat_col = st.columns([1, 1])
    
    # 渲染游戏区
    with game_col:
        render_game_view()
    
    # 渲染聊天区
    with chat_col:
        if render_chat_view():
            # 新的对话优先进行刷新
            logger.info(f"[main] new chat piority rerun {time.time()}")
            # st.session_state.require_update = False
            # st.rerun()

        # 渲染动作区
        render_action_view()
    
    # 处理状态更新
    if await _process_game_loop():
        st.session_state.require_update = False
        logger.info(f"[main] after _process_game_loop rerun {time.time()}")
        st.rerun()

if __name__ == "__main__":

        # 初始化会话状态
    _init_session_state()

    # 初始化游戏LangGraph工作流 -- 直到route节点,进入Human-in-loop
    _init_gamegraph()

    asyncio.run(main()) 
