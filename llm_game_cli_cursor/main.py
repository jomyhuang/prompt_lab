import streamlit as st
import random
import time
import asyncio
from typing import Optional
from datetime import datetime
from game_agent import GameAgent, GameAction
from llm_interaction import LLMInteraction
from agent_tool import add_system_message, add_user_message, add_assistant_message
from games.base_game import render_game_view, render_action_view
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
import logging
from langgraph.types import interrupt, Command
import json
from pprint import pprint

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
    if "initialized" not in st.session_state:
        # 游戏逻辑状态管理器
        st.session_state.initialized = True
        st.session_state.llm_interaction = LLMInteraction()  # LLM交互管理器
        st.session_state.thread_id = None  # LangGraph线程ID
        st.session_state.checkpointer = None  # LangGraph状态检查点
        st.session_state.config = None  # LangGraph配置
        st.session_state.game_agent = None  # 游戏Agent实例
        st.session_state.streaming = True
        st.session_state.debug = None
        
        # GUI状态管理
        st.session_state.messages = []  # 聊天历史记录
        st.session_state.game_started = False  # 游戏是否开始标志
        # st.session_state.player_info = {}       # 玩家信息存储
        # st.session_state.current_message = "欢迎来到游戏!"  # 当前显示消息
        st.session_state._user_chat_input = None  # 用户输入缓存
        st.session_state.require_update = False  # GUI更新标志
        st.session_state.require_update_chat = False  # 新对话更新标志
        st.session_state.processing_state = False  # 状态处理标志

        # === 修改 GUI 反馈标记 ===
        st.session_state.gui_feedback = None  # GUI反馈信号
        st.session_state.gui_feedback_params = {}  # GUI反馈的附加参数
        st.session_state.agent_autogui = False
        # === 修改代码结束 ===

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

def _init_game_agent():
    """初始化游戏Agent工作流
    
    创建GameAgent实例并设置相关配置:
    - 初始化checkpointer
    - 设置thread_id
    - 配置LangGraph运行环境
    """
    if "game_agent" not in st.session_state or st.session_state.game_agent is None:
        game_agent = GameAgent()
        st.session_state.game_agent = game_agent
        st.session_state.checkpointer = game_agent.checkpointer
        st.session_state.thread_id = game_agent.thread_id
        config = {"configurable": {"thread_id": st.session_state.thread_id}}
        st.session_state.config = config

def render_sidebar_controls():
    """渲染侧边栏控制界面
    
    显示:
    - 手动更新按钮
    - 游戏状态JSON查看器
    """
    with st.sidebar:
        st.header("🛠️ 游戏控制台")

        # 手动更新按钮
        if st.button("手动更新界面"):
            logger.info("手动更新界面")
            st.rerun()

        # 显示游戏状态
        game_state = st.session_state.game_agent.get_game_state()

        def _default_handler(obj):
            try:
                return obj[0].value
            except:
                pass
            return None

        if game_state:
            with st.expander("🔍 查看游戏状态", expanded=True):
                st.json(game_state, expanded=3)

        if not st.session_state.game_agent is None:
            # 使用__dict__ 来获取所有属性, 使用default_handler 来处理不可序列化属性
            json_string = json.dumps(st.session_state.game_agent.__dict__ , default=_default_handler)
            with st.expander("🔍 session_state.game_agent", expanded=True):
                st.json(json_string, expanded=1)

        if not st.session_state.debug is None:
            with st.expander("🔍 session_state.debug", expanded=True):
                st.json(st.session_state.debug, expanded=2)

def _add_user_chat_input(message: str):
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
    current_state = st.session_state.game_agent.get_game_state()
    
    # 更新游戏状态
    # st.session_state.game_agent.update_state(result, game_action)
    # st.session_state.require_update = True

def _debug_game_state():
    game_state = st.session_state.game_agent.get_game_state()
    game_agent = st.session_state.game_agent

    st.session_state.debug = game_agent.graph.get_state(st.session_state.config)

    st.write("debug game state")
    st.json(st.session_state.debug, expanded=3)

# 核心逻辑代码, 不能任意修改 === 代码开始
def _process_streaming_agent() -> bool:

    if not st.session_state.game_started:
        return False

    if not st.session_state.streaming:
        return False

    require_update = False
    # st.session_state.agent_autogui = False
    # 1. 游戏启动处理
    if st.session_state.game_started and st.session_state.gui_feedback == "start":
        logger.info("[_process_streaming_agent][chat_view] Starting game workflow")
        game_agent = st.session_state.game_agent
        init_state = game_agent.init_game_state()
        # add_system_message("start run game agent....")
        # init agent call
        with st.chat_message("assistant"):
            response = st.write_stream(game_agent.run_agent_stream(init_state))

        st.session_state.debug = game_agent.stream_chunk
        add_assistant_message(response)
        st.session_state.gui_feedback = None
        st.session_state.gui_feedback_params = {}
        st.session_state.agent_autogui = True
        require_update = True
    # 2. Human-in-Loop Feedback 处理    
    if st.session_state.game_started and st.session_state.gui_feedback and st.session_state.gui_feedback != "start":
        feedback = st.session_state.gui_feedback
        params = st.session_state.gui_feedback_params
        game_agent = st.session_state.game_agent
        logger.info(f"[_process_streaming_agent][chat_view] Processing GUI feedback: {feedback}, params: {params}")

        # 判断feedback是否已经是Command类型
        if isinstance(feedback, Command):
            command = feedback
        else:
        # 构建 Command 对象
            command = Command(
                resume=feedback,
                update=params  # 使用反馈参数更新状态
            )

        # 调用 resume_agent 处理反馈
        # Use st.write_stream to display the output as it is generated
        with st.chat_message("assistant"):
            # response = st.write_stream(game_agent.resume_agent_stream(command))
            response = st.write_stream(game_agent.run_agent_stream(command))
        # if isinstance(response, list):
        #     response = next((item for item in response if item), "")

        st.session_state.debug = game_agent.stream_chunk
        add_assistant_message(response)
        st.session_state.agent_autogui = True
        # 清除已处理的GUI反馈
        st.session_state.gui_feedback = None
        st.session_state.gui_feedback_params = {}
        require_update = True

    return require_update
# 核心逻辑代码, 不能任意修改 === 代码结束

def _process_invoke_agent() -> bool:

    if not st.session_state.game_started:
        return False

    if st.session_state.streaming:
        return False

    game_agent = st.session_state.game_agent
    game_state = st.session_state.game_agent.get_game_state()

    # 1. 游戏启动处理
    require_update = False
    if st.session_state.game_started and not game_agent.get_game_state()["game_started"]:
        logger.info("[_process_invoke_agent] Starting game workflow")
        init_state = game_agent.init_game_state()
        game_agent.run_agent(init_state)
        st.session_state.gui_feedback = None
        st.session_state.gui_feedback_params = {}
        st.session_state.agent_autogui = True
        require_update = True
    # 2. 处理GUI反馈信号
    if st.session_state.game_started and st.session_state.gui_feedback and st.session_state.gui_feedback != "start":
        feedback = st.session_state.gui_feedback
        params = st.session_state.gui_feedback_params
        logger.info(f"[_process_invoke_agent] Processing GUI feedback: {feedback}, params: {params}")
        
        # 判断feedback是否已经是Command类型
        if isinstance(feedback, Command):
            command = feedback
        else:
            # 构建 Command 对象
            command = Command(
                resume=feedback,
                update=params  # 使用反馈参数更新状态
            )
        
        # 调用 resume_agent 处理反馈
        game_agent.run_agent(command)
        
        # 清除已处理的GUI反馈
        st.session_state.gui_feedback = None
        st.session_state.gui_feedback_params = {}
        st.session_state.agent_autogui = True
        require_update = True

    return require_update

# 测试agent自动反馈给GUI agent_autogui flag
def _process_agent_autogui():

    if not st.session_state.agent_autogui:
        return

    require_update = False
    game_agent = st.session_state.game_agent
    game_state = st.session_state.game_agent.get_game_state()
    st.session_state.agent_autogui = False

    if game_state["current_turn"] == "end_game":
        add_system_message("run agent is finished")
        st.session_state.game_started = False

    elif game_agent.is_game_interrupt() and not game_agent.interrupt_state is None:
        # tuple 解包
        # # interrupt_value = game_agent.interrupt_state            #获得一个tuple
        # interrupt_value = game_agent.interrupt_state[0].value     #获得一个dict
        message = game_agent.interrupt_state.get("message",None)
        if not message is None:
            # logger.info(f"[process_game_loop] interrupt game_info: {message}")
            if isinstance(message, AIMessage):
                add_assistant_message("[HIL] "+message.content)
            else:
                add_system_message("[HIL] "+message)

    return require_update

# 核心逻辑代码, 不能任意修改 === 代码开始
def _process_game_loop():
    """处理游戏循环
    
    主要职责:
    1. 统一处理 game_agent 的运行和恢复
    2. 处理用户输入和界面更新
    
    工作流程:
    1. run_agent: 游戏启动时调用
    2. resume_agent: 处理所有GUI反馈信号
    """
    require_update = False
    
    if st.session_state.processing_state:
        return False
        
    try:
        st.session_state.processing_state = True
        game_agent = st.session_state.game_agent
        game_state = st.session_state.game_agent.get_game_state()

        # 处理调用LLM对话生成 (迁移到chat_view)

        # 测试agent自动反馈给GUI

        # 不是streaming模式

    finally:
        st.session_state.processing_state = False    
        # 强制更新检查
        if st.session_state.require_update:
            st.session_state.require_update = False
            require_update = True
        
    return require_update
# 核心逻辑代码, 不能任意修改 === 代码结束

# 核心逻辑代码, 不能任意修改 === 代码开始
def render_chat_view():
    """渲染聊天界面
    
    包含:
    - 聊天历史记录显示
    - 用户输入框
    - 消息类型处理(System/Human/AI)
    
    Returns:
        bool: 是否需要更新界面
    """
    # 渲染聊天消息历史
    chat_container = st.container(height=600)
    require_update = False
    with chat_container:
        for message in st.session_state.messages:
            # message 采用langchain规范对话类型: SystemMessage, HumanMessage, AIMessage
            if isinstance(message, HumanMessage) or isinstance(message, AIMessage) or isinstance(message, SystemMessage):
                with st.chat_message(message.type):
                    st.markdown(message.content)
            else:
                st.markdown(message)

        if st.session_state._user_chat_input is not None and st.session_state._user_chat_input != "":
            # 1-1.测试stream对话输出
            game_state = st.session_state.game_agent.get_game_state()
            with st.chat_message("assistant"):
                response = st.write_stream(
                    st.session_state.llm_interaction.generate_ai_response_stream(
                        st.session_state._user_chat_input,game_state
            ))
            # 1-2.标准输出(代码不能删除)
            # response = st.session_state.llm_interaction.generate_ai_response(
            #             st.session_state._user_chat_input,game_state
            # )
            # with st.chat_message("assistant"):
            #     st.markdown(response)

            add_assistant_message(response)
            st.session_state._user_chat_input = None

        # 2.有新的对话输出完后, 再进行agent run
        if st.session_state.require_update_chat:
            time.sleep(0.5)
            require_update = True
        else:
            # 3. agent run 处理
            if st.session_state.streaming:
                require_update = _process_streaming_agent()
            else:
                require_update = _process_invoke_agent()
            
            if _process_agent_autogui():
                require_update = True
    
    # 渲染对话输入框
    user_input = st.chat_input("输入你的行动或问题...", key="chat_input")
    if user_input:
        _add_user_chat_input(user_input)
        st.session_state.require_update_chat = True

    return require_update
# 核心逻辑代码, 不能任意修改 === 代码结束

def main():
    """主函数
    
    程序入口点，负责:
    - 初始化页面配置
    - 初始化会话状态
    - 创建游戏Agent
    - 渲染主界面
    - 处理游戏循环
    """
    # 设置页面配置
    st.set_page_config(
        page_title="🎮 LLM Game Framework",
        page_icon="🎮",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # 初始化会话状态
    _init_session_state()

    # 初始化游戏Agent
    if not st.session_state.game_agent:
        _init_game_agent()

    # 渲染侧边栏控制
    render_sidebar_controls()

    # 分割界面为游戏区和聊天区
    chat_col, game_col  = st.columns([0.8, 1.2])
    
    # 1. 渲染聊天区
    with chat_col:
        if render_chat_view():
            # 1-1. 新的对话st.session_state.messages优先进行刷新, 检查 require_update_chat
            if st.session_state.require_update_chat:
                st.session_state.require_update_chat = False
                logger.info(f"[main][chat_view] require_update_chat 新的对话更新优先渲染 rerun {datetime.now()}")
                st.rerun()
            # 1-2. 对话状态优先进行刷新, 检查 require_update
            if st.session_state.require_update:
                st.session_state.require_update = False
                logger.info(f"[main][chat_view] require_update 对话状态优先渲染 rerun {datetime.now()}")
                st.rerun()
            
            # 1-3. 检查 require_update, loop最后强制更新
            st.session_state.require_update = True

        # 2. 渲染动作区
        render_action_view()

    # 3. 渲染游戏区
    with game_col:
        render_game_view()

        debug_button = st.button("debug")
        if debug_button:
            _debug_game_state()
    
    # 4. 处理状态更新
    if _process_game_loop() or st.session_state.require_update:
        st.session_state.require_update = False
        logger.info(f"[main] post _process_game_loop rerun {datetime.now()}")
        st.rerun()

if __name__ == "__main__":
    # asyncio.run(main()) 
    main() 
