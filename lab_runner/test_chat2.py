from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os
import asyncio
import logging
from typing import Optional, List, Dict, Any
import time

# 加载环境变量并设置日志
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedChatBot:
    def __init__(self):
        self.api_key = os.getenv("API_KEY")
        self.api_base = os.getenv("API_BASE_URL")
        self.provider = os.getenv("MODEL_PROVIDER", "claude").lower()
        self.model = (
            os.getenv("CLAUDE_MODEL")
            if self.provider == "claude"
            else os.getenv("OPENAI_MODEL")
        )
        
        self._init_model()
        self._init_prompts()

    def _init_model(self):
        """初始化模型"""
        print(self.model)
        print(self.api_key)
        print(self.api_base)
        
        try:
            self.chat = ChatOpenAI(
                model=self.model,
                #api_key=self.api_key,
                base_url=self.api_base,
                temperature=0.7,
                streaming=True
            )
            logger.info(f"初始化 {self.provider.upper()} 模型成功")
        except Exception as e:
            logger.error(f"初始化模型失败: {str(e)}")
            raise

    def _init_prompts(self):
        """初始化提示模板"""
        self.test_prompts = {
            "basic": "你好，请介绍一下自己",
            "story": "讲一个简短的故事",
            "code": "写一个简单的Python函数计算斐波那契数列",
            "math": "解释什么是欧拉公式",
            "creative": "创作一首关于春天的短诗"
        }

    def chat_sync(
        self,
        message: str,
        system_message: Optional[str] = None
    ) -> str:
        """同步对话"""
        try:
            messages = []
            if system_message:
                messages.append(SystemMessage(content=system_message))
            messages.append(HumanMessage(content=message))
            
            print(messages)
            response = self.chat.invoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"对话失败: {str(e)}")
            return f"Error: {str(e)}"

    async def chat_stream(
        self,
        message: str,
        system_message: Optional[str] = None
    ):
        """异步流式对话"""
        try:
            messages = []
            if system_message:
                messages.append(SystemMessage(content=system_message))
            messages.append(HumanMessage(content=message))
            
            async for chunk in self.chat.astream(messages):
                yield chunk.content
        except Exception as e:
            logger.error(f"流式对话失败: {str(e)}")
            yield f"Error: {str(e)}"

    async def run_test_suite(self):
        """运行测试套件"""
        results = []
        
        print(f"\n=== 测试 {self.provider.upper()} 模型 ===")
        
        # 1. 基础功能测试
        print("\n1. 基础功能测试:")
        for test_name, prompt in self.test_prompts.items():
            print(f"\n测试 {test_name}:")
            start_time = time.time()
            response = self.chat_sync(prompt)
            end_time = time.time()
            
            results.append({
                "test": test_name,
                "time": end_time - start_time,
                "success": "Error" not in response
            })
            
            print(f"回复: {response}")
            print(f"耗时: {end_time - start_time:.2f}秒")

        # 2. 流式输出测试
        print("\n2. 流式输出测试:")
        print("回复: ", end="", flush=True)
        async for chunk in self.chat_stream(
            "用简短的段落描述一下你的特点"
        ):
            print(chunk, end="", flush=True)
        print("\n")

        # 3. 系统提示测试
        print("\n3. 系统提示测试:")
        system_msg = "你是一个专业的Python教师"
        response = self.chat_sync(
            "解释什么是装饰器",
            system_message=system_msg
        )
        print(f"回复: {response}")

        # 输出测试统计
        print("\n=== 测试统计 ===")
        success_count = sum(1 for r in results if r["success"])
        print(f"总测试数: {len(results)}")
        print(f"成功数: {success_count}")
        print(f"失败数: {len(results) - success_count}")
        print(f"平均响应时间: {sum(r['time'] for r in results)/len(results):.2f}秒")

async def main():
    """主函数"""
    try:
        bot = EnhancedChatBot()
        await bot.run_test_suite()
    except Exception as e:
        logger.error(f"测试过程发生错误: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())