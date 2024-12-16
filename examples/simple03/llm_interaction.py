"""
LLM交互模块
"""
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from dotenv import load_dotenv
import os

load_dotenv()

class LLMInteraction:
    def __init__(self):
        # 设置默认值，如果环境变量不存在
        api_key = os.getenv("OPENAI_API_KEY", "your-api-key-here")
        model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo")
        base_url = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        
        self.llm = ChatOpenAI(
            temperature=0.7, 
            api_key=api_key,
            model_name=model_name,
            base_url=base_url,
            streaming=True, 
            verbose=True
        )
        
        self.prompt = PromptTemplate(
            input_variables=["user_input", "game_state"],
            template="""
            你是一个卡牌游戏的AI助手。当前游戏状态：
            {game_state}
            
            用户输入：{user_input}
            
            请根据用户的输入和当前游戏状态，生成合适的响应。响应应该包括：
            1. 理解用户想要执行的操作
            2. 判断操作是否合法
            3. 如果合法，执行操作并返回结果
            4. 如果不合法，说明原因
            
            请用自然、友好的语气回应。
            """
        )
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)
    
    def process_user_input(self, user_input: str, game_state: dict = None) -> str:
        """处理用户输入"""
        try:
            if game_state is None:
                game_state = {"default": "游戏刚开始"}
            
            response = self.chain.run(
                user_input=user_input,
                game_state=str(game_state)
            )
            return response
        except Exception as e:
            return f"处理输入时出错：{str(e)}"
