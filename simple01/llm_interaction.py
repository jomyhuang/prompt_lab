from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

# 定义动作解析提示模板
ACTION_PARSING_PROMPT = """
分析用户的输入，提取出用户想要执行的游戏动作。

用户输入: {user_input}

请以JSON格式返回以下信息：
{{
    "action": "动作类型",
    "target": "目标对象",
    "parameters": {{
        "参数1": "值1",
        "参数2": "值2"
    }}
}}
"""

# 定义AI响应提示模板
AI_RESPONSE_PROMPT = """
基于当前游戏状态，生成合适的AI响应。

当前游戏状态:
{game_state}

请生成一个合适的响应，考虑以下因素：
1. 当前游戏局势
2. 可能的策略选择
3. 对玩家行动的回应

请返回你的决策和行动。
"""

# 添加上下文管理提示模板
CONTEXT_PROMPT = """
系统角色：你是一个AI游戏助手，负责管理卡牌游戏的对话和决策。

对话历史：
{chat_history}

当前游戏状态：
{game_state}

玩家最新输入：{user_input}

基于以上信息，请：
1. 分析玩家的意图和策略
2. 考虑历史对话中的关键信息
3. 结合当前游戏状态
4. 生成合适的响应

请以JSON格式返回：
{{
    "analysis": "对当前局势的分析",
    "strategy": "建议的策略",
    "response": "对玩家的响应",
    "action": {{
        "type": "建议的行动类型",
        "parameters": {{}}
    }}
}}
"""

load_dotenv()
llm = ChatOpenAI(
    temperature=0.7,
    api_key=os.getenv("OPENAI_API_KEY"),
    model_name=os.getenv("OPENAI_MODEL_NAME"),
    base_url=os.getenv("OPENAI_API_BASE"),
    streaming=True,
    verbose=True
)

class LLMInteraction:
    def __init__(self):
        self.action_prompt = PromptTemplate(
            template=ACTION_PARSING_PROMPT,
            input_variables=["user_input"]
        )
        self.action_chain = self.action_prompt | llm

        self.ai_response_prompt = PromptTemplate(
            template=AI_RESPONSE_PROMPT,
            input_variables=["game_state"]
        )
        self.ai_response_chain = self.ai_response_prompt | llm
        
        # 添加上下文相关的属性
        self.chat_history = []
        self.max_history_length = 10  # 保留最近10轮对话
        self.last_game_state = None
        
        # 初始化上下文提示模板
        self.context_prompt = PromptTemplate(
            template=CONTEXT_PROMPT,
            input_variables=["chat_history", "game_state", "user_input"]
        )
        self.context_chain = self.context_prompt | llm

    def add_to_history(self, role: str, content: str):
        """添加对话到历史记录"""
        self.chat_history.append({"role": role, "content": content})
        # 保持历史记录在指定长度内
        if len(self.chat_history) > self.max_history_length:
            self.chat_history = self.chat_history[-self.max_history_length:]

    def format_history(self) -> str:
        """格式化历史记录"""
        formatted = []
        for msg in self.chat_history:
            formatted.append(f"{msg['role']}: {msg['content']}")
        return "\n".join(formatted)

    def parse_user_action(self, user_input):
        # 添加用户输入到历史记录
        self.add_to_history("user", user_input)
        
        # 使用上下文感知的解析
        context_response = self.context_chain.invoke({
            "chat_history": self.format_history(),
            "game_state": str(self.last_game_state),
            "user_input": user_input
        })
        
        # 添加AI响应到历史记录
        self.add_to_history("assistant", str(context_response))
        
        return context_response

    def generate_ai_response(self, game_state):
        # 保存最新的游戏状态
        self.last_game_state = game_state
        
        # 使用上下文感知的响应生成
        ai_response = self.context_chain.invoke({
            "chat_history": self.format_history(),
            "game_state": str(game_state),
            "user_input": self.chat_history[-1]["content"] if self.chat_history else ""
        })
        
        # 添加AI响应到历史记录
        self.add_to_history("assistant", str(ai_response))
        
        return ai_response

    def clear_history(self):
        """清除对话历史"""
        self.chat_history = []
        
    def get_chat_history(self):
        """获取对话历史"""
        return self.chat_history