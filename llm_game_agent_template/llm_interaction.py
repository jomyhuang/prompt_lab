from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
import os
from dotenv import load_dotenv
import json
import logging
from typing import List, Dict, Any, Optional
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
import asyncio
from agent_tool import init_my_model
# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)


PROMPT_BASIC_GAMEASSISTANT = """
你是一个游戏AI助手。基于以下信息帮助玩家：            
当前游戏状态:
{game_state}
聊天历史:
{chat_history}
玩家输入:
{user_input}
请分析情况并给出建议或执行相应操作。
"""

class LLMInteraction:
    """支持GameAgent的LLM交互管理器
    
    处理与大语言模型的交互，包括:
    1. 初始化和配置LLM模型
    2. 管理对话历史
    3. 生成AI响应
    4. 解析用户命令
    5. 维护上下文
    """

    def __init__(self):
        """初始化LLM交互管理器
        
        配置内容:
        1. 选择并初始化LLM模型(google/openai/deepseek)
        2. 设置对话历史
        3. 配置上下文提示模板
        4. 创建对话处理链
        """
        
        # 初始化LLM模型, 简化模型选择
        use_model = "deepseek"  # 可选: google, openai, deepseek
        self.llm = init_my_model(use_model)
        
        # 初始化对话历史
        self.chat_history = []
        self.last_game_state = None
        self.commands_processor = None

    def format_history(self) -> str:
        """格式化聊天历史
        
        Returns:
            str: 格式化的历史记录
        """
        formatted = []
        for entry in self.chat_history[-5:]:  # 只保留最近5条记录
            formatted.append(f"{entry['role']}: {entry['content']}")
        return "\n".join(formatted)
    
    def add_to_history(self, role: str, content: str):
        """添加消息到历史记录
        
        Args:
            role: 消息角色
            content: 消息内容
        """
        self.chat_history.append({"role": role, "content": content})
        if len(self.chat_history) > 10:  # 限制历史记录长度
            self.chat_history.pop(0)

    def clear_history(self):
        """清除对话历史"""
        self.chat_history = []
    
    def get_chat_history(self) -> List[Dict[str, str]]:
        """获取对话历史
        
        Returns:
            List[Dict[str, str]]: 对话历史记录
        """
        return self.chat_history 

    def generate_ai_response(self, user_input: str, game_state: dict = {}, streaming:bool=False) -> str:
        """生成AI响应
        
        处理流程:
        1. 准备上下文信息
        2. 调用LLM生成响应
        3. 处理响应格式
        4. 更新对话历史
        
        Args:
            user_input: 用户输入文本
            game_state: 当前游戏状态
            
        Returns:
            str: 生成的AI响应
        """
        # 设置上下文提示模板
        self.context_prompt = ChatPromptTemplate.from_template(
            PROMPT_BASIC_GAMEASSISTANT
        )

        # 创建对话链
        self.context_chain = self.context_prompt | self.llm
 
        # 准备上下文
        # BUG: TypeError: Object of type HumanMessage is not JSON serializable
        # JSON 序列化失败, 有可能是 HumanMessage 类型的问题
        # 不使用json.dumps, 直接传入game_state
        # try:
        #     game_state_input = json.dumps(game_state, ensure_ascii=False, indent=2)
        # except:
        #     logger.error(f"[generate_ai_response] game_state_input json.dumps error: {game_state}")
        #     game_state_input = ""

        input_state = {
            "game_started": game_state.get("game_started", False),
            "current_turn": game_state.get("current_turn", "player"),
            # "messages": game_state.get("messages", []),
            "game_over": game_state.get("game_over", False),
            "game_data": game_state.get("game_data", {}),
            # "last_action": game_state.get("last_action", ""),
            "phase": game_state.get("phase", "phase"),
            "valid_actions": game_state.get("valid_actions", []),
            "error": game_state.get("error", ""),
            "info": game_state.get("info", "")
        }

        context = {
            "game_state": input_state,
            "chat_history": self.format_history(),
            "user_input": user_input
        }
        
        if streaming:
            # ISSUE: 流式输出时, 对话历史没有更新
            # # 更新对话历史 (llm_interaction保留对话上下文)
            # self.add_to_history("user", user_input)
            # self.add_to_history("assistant", content)
            return self.context_chain.stream(context)
        else:
            # 生成响应
            response = self.context_chain.invoke(context)
            content = response.content

            # 如果内容是列表，取第一个非空元素
            if isinstance(content, list):
                content = next((item for item in content if item), "")
    
            # 更新对话历史 (llm_interaction保留对话上下文)
            self.add_to_history("user", user_input)
            self.add_to_history("assistant", content)
    
            return content
 
    def generate_ai_response_stream(self, user_input: str, game_state: dict):
        return self.generate_ai_response(user_input, game_state, streaming=True)


    def parse_user_action(self, user_input: str) -> Dict[str, Any]:
        """解析用户输入为游戏动作
        
        处理流程:
        1. 记录用户输入历史
        2. 使用LLM解析意图
        3. 转换为标准动作格式
        4. 错误处理和回退
        
        Args:
            user_input: 用户输入文本
            
        Returns:
            Dict[str, Any]: 解析后的动作数据
            {
                "action": str,     # 动作类型
                "target": str,     # 目标对象
                "parameters": dict # 附加参数
            }
        """
        try:
            # 添加用户输入到历史记录
            self.add_to_history("user", user_input)
            
            # 使用LLM解析用户输入
            parse_prompt = ChatPromptTemplate.from_template(
                """分析用户的输入，提取出用户想要执行的游戏动作。
                
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
            )
            
            parse_chain = parse_prompt | self.llm
            response = parse_chain.invoke({"user_input": user_input})
            
            # 解析JSON响应
            try:
                action_data = json.loads(response.content)
                return action_data
            except json.JSONDecodeError:
                logger.error("Failed to parse LLM response as JSON")
                return {"action": "unknown", "target": None, "parameters": {}}
                
        except Exception as e:
            logger.error(f"Failed to parse user action: {str(e)}")
            return {"action": "error", "target": None, "parameters": {}}
