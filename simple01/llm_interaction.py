from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
import google.generativeai as genai
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

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

# 设置Google API密钥
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

class LLMInteraction:
    def __init__(self):
        # 初始化Gemini模型
        self.llm = ChatGoogleGenerativeAI(
            model=os.getenv("GOOGLE_MODEL_NAME", "gemini-pro"),  # 从环境变量读取模型名称，默认为gemini-pro
            temperature=0.7,
            top_p=0.9,
            top_k=40,
            max_output_tokens=2048,
        )
        
        # 初始化对话历史
        self.chat_history = []
        self.last_game_state = None
        
        # 设置上下文提示模板
        context_template = """你是一个卡牌游戏AI助手。基于以下信息帮助玩家:
        
        当前游戏状态:
        {game_state}
        
        聊天历史:
        {chat_history}
        
        玩家输入:
        {user_input}
        
        请分析情况并给出建议。注意保持回答简洁明了。
        """
        
        self.context_chain = LLMChain(
            llm=self.llm,
            prompt=ChatPromptTemplate.from_template(context_template)
        )
        
        # 初始化动作解析提示模板
        self.action_prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个游戏助手，负责解析玩家的行动。"),
            ("human", "{user_input}")
        ])
        self.action_chain = self.action_prompt | self.llm
        
        # 初始化AI响应提示模板
        self.ai_response_prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个游戏助手，负责分析游戏状态并给出建议。"),
            ("human", "{game_state}")
        ])
        self.ai_response_chain = self.ai_response_prompt | self.llm
    
    def format_history(self):
        """格式化聊天历史"""
        formatted = []
        for entry in self.chat_history[-5:]:  # 只保留最近5条记录
            formatted.append(f"{entry['role']}: {entry['content']}")
        return "\n".join(formatted)
    
    def add_to_history(self, role, content):
        """添加消息到历史记录"""
        self.chat_history.append({"role": role, "content": content})
        if len(self.chat_history) > 10:  # 限制历史记录长度
            self.chat_history.pop(0)
    
    def parse_user_action(self, user_input):
        """解析用户输入"""
        # 添加用户输入到历史记录
        self.add_to_history("user", user_input)
        return user_input  # 简单返回用户输入，后续可以添加更复杂的解析逻辑
    
    def generate_ai_response(self, user_input, game_state):
        """生成AI响应
        
        Args:
            user_input (str): 用户输入的文本
            game_state (dict): 当前游戏状态
            
        Returns:
            str: AI的响应文本
        """
        self.last_game_state = game_state
        
        # 构建提示
        prompt = f"""基于当前游戏状态和用户输入，请分析并给出建议：
        
        用户输入：
        {user_input}
        
        当前游戏状态：
        {game_state}
        
        请分析局势并给出建议。回答要简洁明了，重点说明：
        1. 对用户输入的理解
        2. 当前游戏形势分析
        3. 具体的建议
        """
        
        try:
            # 使用Gemini生成响应
            response = self.llm.invoke(prompt)
            ai_response = response.content
            
            # 添加到历史记录
            self.add_to_history("assistant", ai_response)
            return ai_response
            
        except Exception as e:
            print(f"生成响应时出错: {str(e)}")
            return "抱歉，我现在无法给出建议。"
    
    def clear_history(self):
        """清除对话历史"""
        self.chat_history = []
        
    def get_chat_history(self):
        """获取对话历史"""
        return self.chat_history