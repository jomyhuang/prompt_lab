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

    def parse_user_action(self, user_input):
        action_info = self.action_chain.invoke({"user_input": user_input})
        return action_info

    def generate_ai_response(self, game_state):
        ai_response = self.ai_response_chain.invoke({"game_state": str(game_state)})
        return ai_response