from typing import Dict
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from models.game_state import GameState
from .prompts import (
    ACTION_PARSER_PROMPT,
    AI_ACTION_PROMPT,
    STATE_DESCRIPTION_PROMPT,
    RULE_EXPLANATION_PROMPT
)
import json

class LLMManager:
    def __init__(self, api_key: str, model_name: str = "gpt-3.5-turbo"):
        self.llm = ChatOpenAI(
            temperature=0.7,
            api_key=api_key,
            model_name=model_name,
            base_url="https://ai98.vip/v1"
        )
        
        # 初始化提示词模板
        self.action_parser_prompt = ChatPromptTemplate.from_template(ACTION_PARSER_PROMPT)
        self.ai_action_prompt = ChatPromptTemplate.from_template(AI_ACTION_PROMPT)
        self.state_description_prompt = ChatPromptTemplate.from_template(STATE_DESCRIPTION_PROMPT)
        self.rule_explanation_prompt = ChatPromptTemplate.from_template(RULE_EXPLANATION_PROMPT)
        
    def parse_user_action(self, user_input: str, game_state: GameState) -> Dict:
        """解析用户输入为游戏动作"""
        prompt_value = self.action_parser_prompt.format(
            user_input=user_input,
            game_state=game_state.to_dict()
        )
        
        response = self.llm.invoke(prompt_value)
        try:
            return json.loads(response.content)
        except:
            # 如果解析失败，返回一个默认的查询动作
            return {
                "action_type": "query_info",
                "card_index": None,
                "target_index": None,
                "additional_info": "无法解析的命令"
            }
        
    def generate_ai_action(self, game_state: GameState) -> Dict:
        """生成AI对手的行动"""
        prompt_value = self.ai_action_prompt.format(
            game_state=game_state.to_dict()
        )
        
        response = self.llm.invoke(prompt_value)
        try:
            return json.loads(response.content)
        except:
            # 如果解析失败，返回一个默认的结束回合动作
            return {
                "action_type": "end_turn",
                "reasoning": "AI决策出错"
            }
        
    def generate_state_description(self, game_state: GameState) -> str:
        """生成游戏状态描述"""
        prompt_value = self.state_description_prompt.format(
            game_state=game_state.to_dict()
        )
        
        response = self.llm.invoke(prompt_value)
        return response.content
        
    def explain_rule(self, question: str, context: str) -> str:
        """解释游戏规则"""
        prompt_value = self.rule_explanation_prompt.format(
            question=question,
            context=context
        )
        
        response = self.llm.invoke(prompt_value)
        return response.content
