from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from langchain.schema import SystemMessage, HumanMessage, AIMessage
import logging
import os
from dotenv import load_dotenv
import json

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

class LLMInterface:
    """LLM交互接口
    
    处理与LLM的交互,包括提示词管理和响应处理
    支持多种模型配置:
    - OpenAI GPT
    - DeepSeek
    - Claude
    - Google Gemini
    """
    
    def __init__(self, model_type: str = "openai"):
        """初始化LLM接口
        
        Args:
            model_type: 使用的模型类型 (openai/deepseek/claude/gemini)
        """
        self.model_type = model_type
        self.init_llm()
        
        # 系统提示词模板
        self.system_template = """你是一个游戏助手AI。
        
        游戏规则:
        1. {game_rules}
        
        你的职责:
        1. 理解玩家输入
        2. 根据游戏规则做出响应
        3. 保持对话的连贯性和趣味性
        
        当前游戏状态:
        {game_state}
        """
        
        # 用户提示词模板
        self.user_template = """玩家动作: {player_action}
        
        请根据当前游戏状态和规则,对玩家的动作做出合适的响应。
        """
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_template),
            ("human", self.user_template),
        ])
        
        # 初始化对话历史
        self.chat_history = []
        
    def init_llm(self):
        """初始化LLM模型"""
        if self.model_type == "gemini":
            # 初始化Gemini模型
            model = os.getenv("GOOGLE_MODEL_NAME", "gemini-pro")
            self.llm = ChatGoogleGenerativeAI(
                api_key=os.getenv("GOOGLE_API_KEY"),
                model=model,
                temperature=0.7,
                streaming=True
            )
            logger.info(f"使用Gemini模型 {model}")
            
        elif self.model_type == "claude":
            # 初始化Claude模型
            model = os.getenv("CLAUDE_MODEL_NAME", "claude-3-sonnet-20240229")
            self.llm = ChatAnthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY"),
                model=model,
                temperature=0.7,
                streaming=True
            )
            logger.info(f"使用Claude模型 {model}")
            
        elif self.model_type == "deepseek":
            # 初始化DeepSeek模型
            model = os.getenv("DEEPSEEK_MODEL_NAME", "deepseek-chat")
            base_url = os.getenv("DEEPSEEK_API_BASE")
            self.llm = ChatOpenAI(
                api_key=os.getenv("DEEPSEEK_API_KEY"),
                model=model,
                base_url=base_url,
                temperature=0.7,
                streaming=True
            )
            logger.info(f"使用DeepSeek模型 {model}")
            
        else:  # openai
            # 初始化OpenAI模型
            model = os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo")
            base_url = os.getenv("OPENAI_API_BASE")
            self.llm = ChatOpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                model=model,
                base_url=base_url,
                temperature=0.7,
                streaming=True
            )
            logger.info(f"使用OpenAI模型 {model}")
    
    def format_history(self) -> str:
        """格式化对话历史
        
        Returns:
            格式化后的对话历史字符串
        """
        formatted = []
        for msg in self.chat_history:
            role = msg["role"]
            content = msg["content"]
            formatted.append(f"{role}: {content}")
        return "\n".join(formatted)
        
    async def process_input(self, 
                    player_action: str,
                    game_rules: str,
                    game_state: Dict[str, Any]) -> str:
        """处理玩家输入
        
        Args:
            player_action: 玩家动作
            game_rules: 游戏规则
            game_state: 游戏状态
            
        Returns:
            LLM响应
        """
        try:
            # 准备上下文消息
            context_str = f"""游戏规则：
{game_rules}

游戏状态：
{json.dumps(game_state, ensure_ascii=False, indent=2)}

聊天历史：
{self.format_history()}

玩家输入: {player_action}
"""
            
            # 获取LLM响应
            response = await self.llm.ainvoke([
                SystemMessage(content=self.system_template),
                HumanMessage(content=context_str)
            ])
            
            # 更新对话历史
            self.chat_history.append({"role": "user", "content": player_action})
            self.chat_history.append({"role": "assistant", "content": response.content})
            
            return response.content
            
        except Exception as e:
            logger.error(f"Error processing LLM input: {e}")
            return "抱歉,我现在无法正确理解和处理你的输入。"
    
    def update_system_prompt(self, new_template: str):
        """更新系统提示词模板
        
        Args:
            new_template: 新的提示词模板
        """
        self.system_template = new_template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_template),
            ("human", self.user_template),
        ])
    
    def update_user_prompt(self, new_template: str):
        """更新用户提示词模板
        
        Args:
            new_template: 新的提示词模板
        """
        self.user_template = new_template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_template),
            ("human", self.user_template),
        ])
