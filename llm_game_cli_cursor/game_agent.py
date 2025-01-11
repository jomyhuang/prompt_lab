import streamlit as st
from typing import Dict, Any, Optional, List, TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, RemoveMessage
from langgraph.graph.message import add_messages
from agent_tool import add_system_message, add_user_message, add_assistant_message
from dataclasses import dataclass
from datetime import datetime
import logging
import random
import time

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
    info: Optional[str]        # 消息提示

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
        self.config = {"configurable": {"thread_id": self.thread_id}}
        self._game_state = self.init_game_state()
        self.graph = self.build_graph()
        self.interrupt_state = None
        self.stream_chunk = []
        self.stream_flow = None
        self.stream_current_node = None
        self.is_new_player_turn = False
       
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
            phase="phase",
            valid_actions=["start"],
            thread_id=self.thread_id,
            error="",
            info=""
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
            graph_builder.add_node("chat", self._chat_state)
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
                    # "chat": "chat",
                    "end": "end"
                }
            )
            # graph_builder.add_edge("player_turn", "route")
            graph_builder.add_edge("ai_turn", "route")
            # graph_builder.add_edge("chat", "route")
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
            state = {}

        if config is None:
            config = {"configurable": {"thread_id": self.thread_id}}

        if isinstance(state, str):
            state = Command(resume="resume")
        
        if isinstance(state, Command):
            if not self.is_game_interrupt():
                logger.error("run_agent error, state is not interrupt, but input Command")
                raise ValueError("run_agent error, state is not interrupt, but input Command")

        logger.info("run_agent before invoke")
        # 中断状态清空
        self.interrupt_state = None
        self.stream_chunk = None
        new_state = self.graph.invoke(state, config=config)
        self.set_game_state(new_state)
        self.stream_chunk = new_state
        # print("run_agent new_state", new_state)
        logger.info("run_agent after invoke")
        return new_state

    def run_agent_stream(self, state: GameState=None, config: dict=None):
        if state is None:
            state = {}

        if config is None:
            config = {"configurable": {"thread_id": self.thread_id}}

        if isinstance(state, str):
            state = Command(resume="resume")

        if isinstance(state, Command):
            if not self.is_game_interrupt():
                logger.error("run_agent_stream error, state is not interrupt, but input Command")
                raise ValueError("run_agent_stream error, state is not interrupt, but input Command")
            
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
                        # 基本使用的方式
                        # self.game_state.update(value)
                        # 使用Annotated类型的方式
                        self.set_game_state_from_stream(value)  
                    else:
                        self.set_game_interrupt(value)
                except Exception as e:
                    logger.error(f"Error stream set game state: {str(e)}")
                print("\n---")
            yield f" -> {key}"
            stream_flow += f" -> {key}"
            # 保存整个streaming chunk (deubg)
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

    def get_game_state(self) -> GameState:
        """获取当前游戏状态"""
        if self.graph is None:
            # return self._game_state
            # return {}
            raise ValueError("[get_game_state] error, graph is None")
        else:
            return self.graph.get_state(self.config).values

    def set_game_state(self, state: GameState):
        """设置当前游戏状态"""
        # if self.validate_state(state):
        #     self._game_state = state
        #     logger.info("game_state set: new value")
        pass

    def set_game_state_from_stream(self, state: GameState):
        """设置当前游戏状态(从stream中获取)"""
        # try:
        #     for key, value in state.items():
        #         field_type = GameState.__annotations__.get(key, None)
        #         if hasattr(field_type, "__metadata__") and field_type.__metadata__:
        #             reducer = field_type.__metadata__[0]
        #             current_value = self._game_state.get(key, [])
        #             self._game_state[key] = reducer(current_value, value)
        #         else:
        #             self._game_state[key] = value
                    
        #     logger.info("game_state set from stream: updated successfully")
        # except Exception as e:
        #     logger.error(f"Failed to update game state from stream: {str(e)}")
        #     raise
        pass

    def set_game_interrupt(self, info: Any = None):
        """设置当前游戏Human-in-Loop中断状态"""
        if info is None:
            info = {"interrupt": True}

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

    def _init_state(self, state: GameState) -> Dict:
        """初始化游戏状态节点"""
        print("[init_state] 进入初始化节点")
        
        updates = {}
        if not state["game_started"]:
            updates.update({
                "game_started": True,
                "phase": "init phase",
                "info": "游戏开始！请选择你的行动。",
                "valid_actions": ["start"],
                "current_turn": "start"
            })

        updates["messages"] = AIMessage(content=f"_init_state {datetime.now()}")
        return updates
    
    def _welcome_state(self, state: GameState) -> Dict:
        """欢迎状态节点"""
        print("[welcome_state] 进入欢迎状态节点")
        who_first = "player" # 决定谁先?
        self.is_new_player_turn = True

        return {
            "messages": AIMessage(content=f"_welcome_state {datetime.now()}"),
            "current_turn": who_first
        }
    
    def _route_state(self, state: GameState) -> Dict:
        """路由状态节点"""
        print("[route_state] 进入路由节点")
        
        updates = {}

        if state["current_turn"] == "player":
            updates.update({
                "valid_actions": ["play", "end_turn", "game_over"],
                "info": "请选择行动"
            })
        elif state["current_turn"] == "ai":
            updates.update({
                "valid_actions": [],
                "info": "AI回合..."
            })
        else:
            updates.update({
                "valid_actions": [],
                "info": f"unknown route current_turn {state['current_turn']}"
            })

        # updates["messages"] = [AIMessage(content=f"_route_state {datetime.now()}")]
        # 清理消息, 注释了 annotated[list, add_messages] 移除必须使用 RemoveMessage
        keep_last = 5
        if len(state["messages"]) > keep_last:
            print(f"messages len > {keep_last}, remove first message")

            messages = state["messages"]
            if len(messages) > keep_last:
                # 创建需要删除的消息列表
                messages_to_remove = [RemoveMessage(id=m.id) for m in messages[:-keep_last]]
                # print("messages_to_remove", messages_to_remove)
                updates.update({
                    "messages": messages_to_remove
                })

        return updates
    
    def _route_condition(self, state: GameState) -> str:
        """路由条件判断
        
        Args:
            state: 当前状态
            
        Returns:
            str: 下一个节点名称
        """
        # print("[route_condition] 进入路由条件节点", state["current_turn"])
        # print(state)
        print("[route_condition] 进入路由条件节点", state["current_turn"], "last_action:", state["last_action"])

        # if state["last_action"] == "chat":
        #     return "chat"

        if state["game_over"]:
            return "end"
        elif state["current_turn"] == "player":
            return "player"
        else:
            return "ai"
    
    def _player_turn(self, state: GameState) -> Dict:
        """玩家回合处理"""
        print("[player_turn] 进入玩家回合节点")
        
        player_info = "玩家回合开始" if self.is_new_player_turn else "玩家回合继续"
        game_info = {
            "valid_actions": state["valid_actions"],
            "game_data": state["game_data"],
            "message": AIMessage(content=player_info)
        }
        
        updates = {"info": player_info}
        
        print("[player_turn] Before interrupt ----")
        self._run_agent_interrupt(game_info)
        action = interrupt(game_info)
        print("[player_turn] After interrupt ----", action)
        updates["last_action"] = action
        self.is_new_player_turn = False

        if action == "end_turn":
            self.is_new_player_turn = True
            return Command(goto="route", update={
                "current_turn": "ai",
                "info": "回合结束"
            })
        elif action == "game_over":
            return Command(goto="route", update={
                "game_over": True,
                "info": "游戏结束"
            })
        elif action == "chat":
            # print("[player_turn] chat action", state["info"])
            # goto进入其他node后同样使用goto返回
            return Command(goto="chat",
                        update={"info": state["info"]})
        else:
            updates["info"] = f"未知操作: {action}"

        updates["messages"] = [AIMessage(content=f"_player_turn {datetime.now()}")]
        return Command(goto="player_turn",
                        update=updates)
    
    # 参考设计模式: route 模式, 采用 last_action 在route中判断, 从condition_edge中跳转
    # def _player_turn(self, state: GameState) -> Dict:
    #     """玩家回合处理"""
    #     print("[player_turn] 进入玩家回合节点")
        
    #     game_info = {
    #         "valid_actions": state["valid_actions"],
    #         "game_data": state["game_data"],
    #         "message": AIMessage(content="玩家回合开始")
    #     }
        
    #     updates = {"info": "玩家回合开始"}
        
    #     print("[player_turn] Before interrupt ----")
    #     self._run_agent_interrupt(game_info)
    #     action = interrupt(game_info)
    #     print("[player_turn] After interrupt ----", action)
    #     updates["last_action"] = action
        
    #     if action == "end_turn":
    #         updates.update({
    #             "current_turn": "ai",
    #             "info": "回合结束"
    #         })
    #     elif action == "game_over":
    #         updates.update({
    #             "game_over": True,
    #             "info": "游戏结束"
    #         })
    #     elif action == "chat":
    #         print("[player_turn] chat action", state["info"])
    #     else:
    #         updates["info"] = f"未知操作: {action}"

    #     updates["messages"] = [AIMessage(content=f"_player_turn {datetime.now()}")]
    #     return updates
    
    def _ai_turn(self, state: GameState) -> Dict:
        """AI回合处理"""
        print("[ai_turn] 进入AI回合节点")
        
        add_assistant_message("AI行动")
        time.sleep(1)
        
        # 处理AI回合Agent

        ai_info = "AI回合结束"
        add_assistant_message(ai_info)

        return {
            "info": ai_info,
            "current_turn": "player",
            "messages": [AIMessage(content=f"_ai_turn {datetime.now()}")]
        }
    
    def _end_game(self, state: GameState) -> Dict:
        """处理游戏结束"""
        print("[end_game] 进入游戏结束节点")
        add_assistant_message("游戏结束")
        
        return {
            "messages": [AIMessage(content=f"_end_game {datetime.now()}")],
            "current_turn": "end_game",
            "info": "游戏结束",
            "game_over": True
        }
    
    def _chat_state(self, state: GameState) -> Dict:
        """聊天状态节点"""
        user_message = state['info']
        
        print("[chat_state] 进入聊天状态节点:", user_message)
        add_assistant_message(f"[chat_state] 进入聊天状态节点 response {user_message}")
        
        return Command(goto="player_turn", update={
            "messages": AIMessage(content=f"_chat_state response {datetime.now()}"),
            # "current_turn": "player",
            # "last_action": None (返回None值,key被删除)
            "last_action": ""
        })
        # return {
        #     "messages": [AIMessage(content=f"_chat_state response {datetime.now()}")],
        #     "current_turn": "player",
        #     "last_action": None
        # }
