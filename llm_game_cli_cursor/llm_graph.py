from typing import Dict, List, Tuple, Any, Annotated, Callable
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import Graph, END, START
import json
import logging
from agent_tool import init_my_model

logger = logging.getLogger(__name__)

# 基础游戏助手提示词
PROMPT_TEMPLATES = {
    "basic_game": """
你是一个游戏AI助手。基于以下信息帮助玩家：            
当前游戏状态:
{game_state}
聊天历史:
{chat_history}
玩家输入:
{user_input}
请分析情况并给出建议或执行相应操作。
""",
    
    "action_parser": """
分析用户的输入，提取出用户想要执行的游戏动作。

用户输入: {user_input}
游戏状态: {game_state}

请以JSON格式返回以下信息：
{
    "action": "动作类型",
    "target": "目标对象",
    "parameters": {
        "参数1": "值1",
        "参数2": "值2"
    }
}
""",
    
    "strategy_advisor": """
作为游戏策略顾问，根据当前游戏状态为玩家提供战略建议。

当前游戏状态:
{game_state}
玩家历史行动:
{chat_history}
玩家询问:
{user_input}

请提供具体的策略建议，包括:
1. 当前局势分析
2. 可行的策略选项
3. 建议的下一步行动
"""
}

# 上下文准备器函数
CONTEXT_PREPARERS = {
    "basic_game": lambda state: {
        "game_state": {
            "game_started": state["game_state"].get("game_started", False),
            "current_turn": state["game_state"].get("current_turn", "player"),
            "game_over": state["game_state"].get("game_over", False),
            "game_data": state["game_state"].get("game_data", {}),
            "phase": state["game_state"].get("phase", "phase"),
            "valid_actions": state["game_state"].get("valid_actions", []),
            "error": state["game_state"].get("error", ""),
            "info": state["game_state"].get("info", "")
        },
        "chat_history": state["chat_history"],
        "user_input": state["user_input"]
    },
    
    "action_parser": lambda state: {
        "user_input": state["user_input"],
        "game_state": {
            "valid_actions": state["game_state"].get("valid_actions", []),
            "current_phase": state["game_state"].get("phase", ""),
            "game_data": state["game_state"].get("game_data", {})
        }
    },
    
    "strategy_advisor": lambda state: {
        "game_state": state["game_state"].get("game_data", {}),
        "chat_history": state["chat_history"],
        "user_input": state["user_input"]
    }
}

class LLMGraphState:
    """LLM图状态管理器"""
    
    def __init__(self):
        self.chat_history: List[Dict[str, str]] = []
        self.game_state: Dict = {}
        self.user_input: str = ""
        self.llm = init_my_model("deepseek")  # 可选: google, openai, deepseek
        
    def format_history(self) -> str:
        """格式化最近的对话历史"""
        formatted = []
        for entry in self.chat_history[-5:]:
            formatted.append(f"{entry['role']}: {entry['content']}")
        return "\n".join(formatted)
    
    def add_to_history(self, role: str, content: str):
        """添加消息到历史记录"""
        self.chat_history.append({"role": role, "content": content})
        if len(self.chat_history) > 10:
            self.chat_history.pop(0)
            
    def clear_history(self):
        """清除对话历史"""
        self.chat_history = []
        
    def get_chat_history(self) -> List[Dict[str, str]]:
        """获取对话历史"""
        return self.chat_history

class LLMGraph:
    """基于LangGraph的LLM对话生成器"""
    
    def __init__(self):
        self.state = LLMGraphState()
        self.graphs = {}
        
    def _build_graph(self, template_key: str) -> Graph:
        """构建特定类型的对话生成图"""
        def prepare_context(state: Dict) -> Dict:
            """准备对话上下文"""
            logger.info(f"准备上下文, template_key: {template_key}")
            context = CONTEXT_PREPARERS[template_key](state)
            state["context"] = context
            logger.debug(f"上下文准备完成: {context}")
            return state
        
        def generate_response(state: Dict) -> Dict:
            """生成AI回复"""
            logger.info("开始生成AI回复")
            prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATES[template_key])
            chain = prompt | state["llm"]
            
            if state.get("streaming", False):
                logger.info("使用流式输出模式")
                state["response_stream"] = chain.stream(state["context"])
            else:
                response = chain.invoke(state["context"])
                content = response.content
                if isinstance(content, list):
                    content = next((item for item in content if item), "")
                state["response"] = content
                logger.debug(f"生成回复内容: {content}")
                
            return state
        
        def update_history(state: Dict) -> Dict:
            """更新对话历史"""
            logger.info("更新对话历史")
            if not state.get("streaming", False):
                state["chat_history"].append({
                    "role": "user",
                    "content": state["user_input"]
                })
                state["chat_history"].append({
                    "role": "assistant",
                    "content": state["response"]
                })
                logger.debug(f"更新后的历史记录长度: {len(state['chat_history'])}")
            return state
        
        # 构建图
        logger.info(f"开始构建图, 模板类型: {template_key}")
        workflow = Graph()
        
        # 添加节点
        workflow.add_node("prepare_context", prepare_context)
        workflow.add_node("generate_response", generate_response)
        workflow.add_node("update_history", update_history)
        
        # 连接节点
        workflow.add_edge(START, "prepare_context")
        workflow.add_edge("prepare_context", "generate_response")
        workflow.add_edge("generate_response", "update_history")
        workflow.add_edge("update_history", END)
        
        logger.info(f"图构建完成, 模板类型: {template_key}")
        return workflow.compile()
    
    def _get_graph(self, template_key: str) -> Graph:
        """获取或创建特定类型的图"""
        if template_key not in self.graphs:
            self.graphs[template_key] = self._build_graph(template_key)
        return self.graphs[template_key]
    
    def generate_response(self, user_input: str, game_state: Dict, streaming: bool = False) -> Any:
        """生成基础游戏助手回复"""
        return self._generate_with_template("basic_game", user_input, game_state, streaming)
    
    def generate_action_parse(self, user_input: str, game_state: Dict) -> Dict:
        """生成动作解析结果"""
        response = self._generate_with_template("action_parser", user_input, game_state, False)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.error("Failed to parse action response as JSON")
            return {"action": "unknown", "target": None, "parameters": {}}
    
    def generate_strategy_advice(self, user_input: str, game_state: Dict, streaming: bool = False) -> Any:
        """生成策略建议"""
        return self._generate_with_template("strategy_advisor", user_input, game_state, streaming)
    
    def _generate_with_template(self, template_key: str, user_input: str, game_state: Dict, streaming: bool = False) -> Any:
        """使用特定模板生成回复
        
        Args:
            template_key: 模板类型的键名
            user_input: 用户输入
            game_state: 游戏状态
            streaming: 是否使用流式输出
        """
        state = {
            "user_input": user_input,
            "game_state": game_state,
            "chat_history": self.state.format_history(),
            "llm": self.state.llm,
            "streaming": streaming
        }
        
        graph = self._get_graph(template_key)
        result = graph.invoke(state)
        
        if streaming:
            return result["response_stream"]
        else:
            if template_key == "basic_game":  # 只有基础对话需要更新历史
                self.state.add_to_history("user", user_input)
                self.state.add_to_history("assistant", result["response"])
            return result["response"] 