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

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

class LLMInteraction:
    """LLM交互管理器
    
    处理与大语言模型的交互，包括命令解析和响应生成
    """
    def __init__(self):
        # 初始化LLM模型
        use_model = "deepseek"  # 可选: google, openai, deepseek
        
        if use_model == "google":
            model = "gemini-pro"
            self.llm = ChatGoogleGenerativeAI(
                api_key=os.getenv("GOOGLE_API_KEY"),
                model=model,
                temperature=0,
                streaming=True
            )
            logger.info(f"使用Gemini模型 {model}")
            
        elif use_model == "deepseek":
            model = "deepseek-chat"
            base_url = os.getenv("DEEPSEEK_API_BASE")
            self.llm = ChatOpenAI(
                api_key=os.getenv("DEEPSEEK_API_KEY"),
                model=model,
                base_url=base_url,
                temperature=0,
                streaming=True
            )
            logger.info(f"使用DeepSeek模型 {model}")
            
        else:  # openai
            model = "gpt-3.5-turbo"
            base_url = os.getenv("OPENAI_API_BASE")
            self.llm = ChatOpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                model=model,
                base_url=base_url,
                temperature=0,
                streaming=True
            )
            logger.info(f"使用OpenAI模型 {model}")
        
        # 初始化对话历史
        self.chat_history = []
        self.last_game_state = None
        self.commands_processor = None
        
        # 设置上下文提示模板
        self.context_prompt = ChatPromptTemplate.from_template(
            """你是一个游戏AI助手。基于以下信息帮助玩家：
            
            当前游戏状态:
            {game_state}
            
            聊天历史:
            {chat_history}
            
            玩家输入:
            {user_input}
            
            请分析情况并给出建议或执行相应操作。
            """
        )
        
        # 创建对话链
        self.context_chain = self.context_prompt | self.llm
    
    async def generate_ai_response(self, user_input: str, game_state: dict) -> str:
        """生成AI响应
        
        Args:
            user_input: 用户输入
            game_state: 当前游戏状态
            
        Returns:
            str: AI的响应
        """
        try:
            # 准备上下文
            context = {
                "game_state": json.dumps(game_state, ensure_ascii=False, indent=2),
                "chat_history": self.format_history(),
                "user_input": user_input
            }
            
            # 生成响应
            # response = await self.context_chain.ainvoke(context)
            response = AIMessage(content="[generate_ai_response] test response")
            content = response.content
            # print(f"[generate_ai_response] response ---- {response}")

            # 如果内容是列表，取第一个非空元素
            if isinstance(content, list):
                content = next((item for item in content if item), "")
            
            # 更新对话历史 (llm_interaction保留对话上下文)
            self.add_to_history("user", user_input)
            self.add_to_history("assistant", content)
            
            return content
        except Exception as e:
            logger.error(f"[generate_ai_response] Failed to generate AI response: {str(e)}")
            return "抱歉，生成响应时出现错误"

    # def generate_ai_response_stream(self, user_input: str, game_state: dict):
    #     """生成AI响应 streaming 测试
        
    #     Args:
    #         user_input: 用户输入
    #         game_state: 当前游戏状态
            
    #     Returns:
    #         str: AI的响应
    #     """

    #     # 准备上下文
    #     context = {
    #         "game_state": json.dumps(game_state, ensure_ascii=False, indent=2),
    #         "chat_history": self.format_history(),
    #         "user_input": user_input
    #     }
        
    #     # 生成响应
    #     response = self.context_chain.invoke(context)
        
    #     content = response.content
    #     # # print(f"[generate_ai_response] response ---- {response}")

    #         # # 如果内容是列表，取第一个非空元素
    #         # if isinstance(content, list):
    #         #     content = next((item for item in content if item), "")
            
    #         # # 更新对话历史 (llm_interaction保留对话上下文)
    #         # self.add_to_history("user", user_input)
    #         # self.add_to_history("assistant", content)
            
    #     return content
    
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
    
    def parse_user_action(self, user_input: str) -> Dict[str, Any]:
        """解析用户输入为游戏动作
        
        Args:
            user_input: 用户输入
            
        Returns:
            Dict[str, Any]: 解析后的动作
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
    
    def clear_history(self):
        """清除对话历史"""
        self.chat_history = []
    
    def get_chat_history(self) -> List[Dict[str, str]]:
        """获取对话历史
        
        Returns:
            List[Dict[str, str]]: 对话历史记录
        """
        return self.chat_history 