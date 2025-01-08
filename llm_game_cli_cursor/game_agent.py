import streamlit as st
from typing import Dict, Any, Optional, List, TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph.message import add_messages
from agent_tool import add_system_message, add_user_message, add_assistant_message
from dataclasses import dataclass
from datetime import datetime
import logging
import uuid
import random
import json

logger = logging.getLogger(__name__)

class GameState(TypedDict):
    """游戏状态类型定义
    
    专注于LangGraph图节点状态:
    - 游戏进度状态: game_started, game_over
    - 对话历史: messages
    - 动作历史: last_action
    - 会话上下文: thread_id, phase
    - 游戏控制: current_turn, valid_actions
    - 错误处理: error, info
    """
    game_started: bool          # 游戏是否开始
    # messages: list        # 对话历史记录
    messages: Annotated[list, add_messages]        # 对话历史记录
    current_turn: str           # 当前回合玩家
    game_over: bool            # 游戏是否结束 
    game_data: dict            # 游戏数据(棋盘/卡牌等)
    last_action: str           # 最后执行的动作
    phase: str                 # 游戏阶段
    valid_actions: List[str]   # 当前可用动作
    thread_id: str             # 会话ID
    error: Optional[str]       # 错误信息
    info: Optional[str]      # 消息提示

@dataclass 
class GameAction:
    """游戏动作数据类
    
    记录动作相关信息用于状态转换
    """
    action_type: str
    player_id: str
    timestamp: datetime
    data: dict

class GameAgent:
    """游戏工作流管理器
    
    处理游戏流程的构建和执行,并管理游戏状态
    主要职责:
    1. 初始化和管理游戏状态
    2. 构建和执行LangGraph工作流
    3. 处理状态转换和验证
    4. 管理游戏进程
    """
    def __init__(self, checkpointer: Optional[MemorySaver] = None, thread_id: str = None):
        if checkpointer is None:
            checkpointer = MemorySaver()
            logger.info("checkpointer is None, use GameGraph MemorySaver")
        
        if thread_id is None:
            thread_id = str(random.randint(1, 1000000))
            logger.info("thread_id is None, use GameGraph uuid")

        self.checkpointer = checkpointer
        self.thread_id = thread_id
        self.game_state = self.init_game_state()
        self.graph = self.build_graph()
        self.interrupt_state = None
        self.stream_chunk = []
        self.stream_flow = None
        self.stream_current_node = None
       
    def init_game_state(self) -> GameState:
        """初始化游戏状态"""
        logger.info(f"[init_game_state] init game state")
        return GameState(
            game_started=False,
            messages=[],
            current_turn="player",
            game_over=False,
            game_data={},
            last_action="",
            phase="init",
            valid_actions=["start"],
            thread_id=str(uuid.uuid4()),
            error=None,
            info=None
        )

    def build_graph(self) -> StateGraph:
        """构建游戏流程图
        
        Returns:
            StateGraph: 构建好的状态图
            
        Raises:
            RuntimeError: 图构建失败时抛出
        """
        try:
            # 1. 创建状态图
            graph_builder = StateGraph(GameState)
            
            # 2. 添加节点
            graph_builder.add_node("init", self._init_state)
            graph_builder.add_node("welcome", self._welcome_state)
            graph_builder.add_node("route", self._route_state)
            graph_builder.add_node("player_turn", self._player_turn)
            graph_builder.add_node("ai_turn", self._ai_turn)
            graph_builder.add_node("end", self._end_game)
            
            # 3. 设置边和条件
            graph_builder.add_edge(START, "init")
            graph_builder.add_edge("init", "welcome")
            graph_builder.add_edge("welcome", "route")

            graph_builder.add_conditional_edges(
                "route",
                self._route_condition,
                {
                    "player": "player_turn",
                    "ai": "ai_turn",
                    "end": "end"
                }
            )
            graph_builder.add_edge("player_turn", "route")
            graph_builder.add_edge("ai_turn", "route")
            graph_builder.add_edge("end", END)

            if not self.checkpointer:
                logger.error("build graph error, checkpointer is required")
                raise ValueError("build graph error, checkpointer is required")
            
            return graph_builder.compile(checkpointer=self.checkpointer)
            
        except Exception as e:
            logger.error(f"Failed to build graph: {str(e)}")
            raise RuntimeError(f"Graph build failed: {str(e)}")

    def run_agent(self, state: GameState=None, config: dict=None) -> GameState:
        if state is None:
            state = self.get_game_state()

        if config is None:
            config = {"configurable": {"thread_id": self.thread_id}}

        if isinstance(state, str):
            state = Command(resume="resume")

        logger.info("run_agent before invoke")
        # 中断状态清空
        self.interrupt_state = None
        self.stream_chunk = None
        new_state = self.graph.invoke(state, config=config)
        self.set_game_state(new_state)
        self.stream_chunk = new_state
        logger.info("run_agent after invoke")
        return new_state

    # def resume_agent(self, command: Command=None, config: dict=None) -> GameState:
    #     if command is None:
    #         command = Command(resume="resume")

    #     if config is None:
    #         config = {"configurable": {"thread_id": self.thread_id}}

    #     logger.info("resume_agent before invoke")
    #     # 中断状态清空
    #     self.interrupt_state = None
    #     self.stream_chunk = None
    #     new_state = self.graph.invoke(command, config=config)
    #     self.set_game_state(new_state)
    #     logger.info("resume_agent after invoke")
    #     return new_state

    def run_agent_stream(self, state: GameState=None, config: dict=None):
        if state is None:
            state = self.get_game_state()

        if config is None:
            config = {"configurable": {"thread_id": self.thread_id}}

        if isinstance(state, str):
            state = Command(resume="resume")

        logger.info("run_agent_stream before invoke")
        # 中断状态清空
        self.interrupt_state = None
        self.stream_chunk = []
        self.stream_current_node = None
        
        # 使用stream_mode="updates" 来获取状态更新, Stream parser
        stream_flow = ""    
        for chunk in self.graph.stream(state, config=config, stream_mode="updates"):
        # for chunk in self.graph.stream(state, config=config, stream_mode="values"):
            for key, value in chunk.items():
                print(f"来自节点 '{key}' 的输出:")
                print("---")
                print(value)
                try:
                    if not key == "__interrupt__":
                        self.stream_current_node = key
                        self.set_game_state(value)
                    else:
                        self.set_game_interrupt(value)
                except Exception as e:
                    logger.error(f"Error stream set game state: {str(e)}")
                print("\n---")
            yield f" -> {key}"
            stream_flow += f" -> {key}"
            # 保存整个streaming chunk
            self.stream_chunk.append(chunk)

        self.stream_flow = stream_flow
        logger.info(f"finish run_agent_stream after invoke {datetime.now()}")
        return chunk

    def _run_agent_interrupt(self, info: Any = None):
        """运行游戏中断"""
        if not st.session_state.streaming:
            self.set_game_interrupt(info)
            logger.info("run_agent_interrupt: under invoke mode set game interrupt manually")

    def validate_state(self, state: GameState) -> bool:
        """验证游戏状态的有效性"""
        try:
            if not isinstance(state["current_turn"], str):
                raise ValueError("current_turn must be string")
            if not isinstance(state["valid_actions"], list):
                raise ValueError("valid_actions must be list") 
            return True
        except Exception as e:
            logger.error(f"State validation failed: {str(e)}")
            raise

    # def update_state(self, state: GameState, action: GameAction) -> GameState:
    #     """更新游戏状态"""
    #     try:
    #         new_state = state.copy()
    #         new_state["last_action"] = action.action_type
    #         new_state["action_history"].append({
    #             "type": action.action_type,
    #             "player": action.player_id,
    #             "time": action.timestamp.isoformat(),
    #             "data": action.data
    #         })
    #         self.game_state = new_state
    #         return new_state
    #     except Exception as e:
    #         logger.error(f"State update failed: {str(e)}")
    #         raise

    def get_game_state(self) -> GameState:
        """获取当前游戏状态"""
        return self.game_state

    def set_game_state(self, state: GameState):
        """设置当前游戏状态"""
        if self.validate_state(state):
            self.game_state = state
            logger.info("game_state set: new value")

    def set_game_interrupt(self, info: Any = None):
        """设置当前游戏Human-in-Loop中断状态"""
        ### 解包tuple
        if isinstance(info, tuple):
            self.interrupt_state = info[0].value
        else:
            self.interrupt_state = info
        # print("set_game_interrupt: new value", self.interrupt_state)
        logger.info("set_game_interrupt: new value")

    def is_game_interrupt(self):
        """判断当前游戏是否处于Human-in-Loop中断状态"""
        return self.interrupt_state is not None

    def _init_state(self, state: GameState) -> GameState:
        """初始化游戏状态节点
        
        处理新游戏的初始化:
        - 设置游戏开始标志
        - 初始化游戏阶段
        - 设置初始可用动作
        - 设置初始玩家回合
        
        Args:
            state: 初始状态
            
        Returns:
            GameState: 初始化后的状态
        """
        print("[init_state] 进入初始化节点")
        
        # 如果是新游戏，设置初始状态
        if not state["game_started"]:
            state["game_started"] = True
            state["phase"] = "init phase"
            state["info"] = "游戏开始！请选择你的行动。"
            state["valid_actions"] = ["start"]
            state["current_turn"] = "start"

        state["messages"]= AIMessage(content=f"_init_state {datetime.now()}")
        # state["messages"] = add_messages(state["messages"], [AIMessage(content=f"_init_state {datetime.now()}")])

        return state
    
    def _welcome_state(self, state: GameState) -> GameState:
        """欢迎状态节点
        
        显示欢迎信息并等待用户操作
        使用interrupt等待UI交互
        
        Args:
            state: 当前状态
            
        Returns:
            GameState: 更新后的状态
        """
        print("[welcome_state] 进入欢迎状态节点")
        # print("[welcome_state] Before interrupt ----")
        # action = interrupt("interrupt from welcome")
        # print("[welcome_state] After interrupt ----", action)
        # state["last_action"] = action

        state["messages"]= AIMessage(content=f"_welcome_state {datetime.now()}")
        # add_messages(state["messages"], [AIMessage(content=f"_welcome_state {datetime.now()}")])

        return state
    
    def _route_state(self, state: GameState) -> GameState:
        """路由状态节点
        
        根据当前状态决定下一步流程:
        - 更新可用动作
        - 设置回合信息
        - 准备下一个节点
        
        Args:
            state: 当前状态
            
        Returns:
            GameState: 路由后的状态
        """
        print("[route_state] 进入路由节点")
        # print("[route_state] Before interrupt ----")
        # # 使用interrupt等待UI更新
        # action = interrupt("interrupt from route_state")
        # print("[route_state] After interrupt ---- action:", action)
        # state["last_action"] = action

        if state["current_turn"] == "start":
            state["current_turn"] = "player"

        if state["current_turn"] == "player":
            state["valid_actions"] = ["play", "end_turn", "game_over"]
            state["info"] = "请选择行动"
        elif state["current_turn"] == "ai":
            state["valid_actions"] = []
            state["info"] = "AI回合..."
        else:
            state["valid_actions"] = []
            state["info"] = f"unknown route {state['current_turn']}"

        state["messages"]= [AIMessage(content=f"_route_state {datetime.now()}")]
        # add_messages(state["messages"], [AIMessage(content=f"_route_state {datetime.now()}")])
            
        return state
    
    def _route_condition(self, state: GameState) -> str:
        """路由条件判断
        
        Args:
            state: 当前状态
            
        Returns:
            str: 下一个节点名称
        """
        print("[route_condition] 进入路由条件节点", state["current_turn"], "last_action:", state["last_action"])

        # state["current_turn"] = "ai" if state["current_turn"] == "player" else "player"
        # print("end_turn ->", state["current_turn"])

        if state["game_over"]:
            return "end"
        elif state["current_turn"] == "player":
            return "player"
        else:
            return "ai"
    
    def _player_turn(self, state: GameState) -> GameState:
        """玩家回合处理
        
        Args:
            state: 当前状态
            
        Returns:
            GameState: 更新后的状态
        """
        print("[player_turn] 进入玩家回合节点")
        # if state["current_turn"] != "player" or state["game_over"]:
        #     return state
            
        # 准备游戏信息
        game_info = {
            "valid_actions": state["valid_actions"],
            "game_data": state["game_data"],
            "message": AIMessage(content="玩家回合开始")
        }
        state["info"] = "玩家回合开始"
        # st.session_state.messages.append(AIMessage(content="玩家回合开始"))

        # 使用interrupt等待玩家操作
        print("[player_turn] Before interrupt ----")
        # 非streamm模式下,将game_info作为interrupt的参数
        self._run_agent_interrupt(game_info)
        action = interrupt(game_info)
        print("[player_turn] After interrupt ----", action)
        state["last_action"] = action
        
        # 处理玩家操作
        if action == "end_turn":
            state["current_turn"] = "ai"
            state["info"] = "回合结束"
        elif action == "game_over":
            state["game_over"] = True
            state["info"] = "游戏结束"
        else:
            state["info"] = f"未知操作: {action}"

        state["messages"]= [AIMessage(content=f"_player_turn {datetime.now()}")]
        # add_messages(state["messages"], [AIMessage(content=f"_player_turn {datetime.now()}")])
                
        return state
    
    def _ai_turn(self, state: GameState) -> GameState:
        """AI回合处理
        
        Args:
            state: 当前状态
            
        Returns:
            GameState: 更新后的状态
        """
        print("[ai_turn] 进入AI回合节点")
        # if state["current_turn"] != "ai" or state["game_over"]:
        #     return state
        state["info"] = "AI回合开始"

        # 准备游戏信息
        game_info = {
            "valid_actions": state["valid_actions"],
            "game_data": state["game_data"]
        }

        # # AI决策逻辑
        # # TODO: 实现具体的AI决策
        # print("[ai_turn] Before interrupt ----")
        # action = interrupt(game_info)
        # print("[ai_turn] After interrupt ----", action)
        # state["last_action"] = action
        
        add_assistant_message("AI行动")
        # BUGFIX: (可能为streaming) 如果空下没有Message处理, 这里就会出来message很多的错误
        state["messages"]= [AIMessage(content=f"_ai_turn {datetime.now()}")]
        # add_messages(state["messages"], [AIMessage(content=f"_ai_turn {datetime.now()}")])

        # 回合结束
        state["current_turn"] = "player"
        state["info"] = "AI回合结束"

        return state
    
    def _end_game(self, state: GameState) -> GameState:
        """处理游戏结束
        
        Args:
            state: 当前状态
            
        Returns:
            GameState: 更新后的状态
        """
        print("[end_game] 进入游戏结束节点")
        add_assistant_message("游戏结束")

        # BUGFIX: (可能为streaming) 如果空下没有Message处理, 这里就会出来message很多的错误
        state["messages"]= [AIMessage(content=f"_end_game {datetime.now()}")]   
        state["current_turn"] = "end_game"
        state["info"] = "游戏结束"
        state["game_over"] = True
        return state 