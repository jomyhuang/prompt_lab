from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

def chat_with_ai():
    # 加载环境变量
    load_dotenv()
    
    # 初始化 ChatOpenAI，使用代理服务
    chat = ChatOpenAI(
        model_name=os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo"),
        temperature=0.7,
        openai_api_base=os.getenv("OPENAI_API_BASE"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        default_headers={
            "Content-Type": "application/json",
        }
    )
    
    # 创建一个简单的提示模板
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个友好的AI助手。"),
        ("user", "{input}")
    ])
    
    # 创建对话链
    chain = prompt | chat
    
    print(f"正在使用模型: {os.getenv('OPENAI_MODEL_NAME')}")
    print("开始对话（输入 'quit' 或 'exit' 结束对话）...")
    
    while True:
        user_input = input("\n你: ").strip()
        
        if user_input.lower() in ['quit', 'exit']:
            print("结束对话...")
            break
            
        if not user_input:
            continue
            
        try:
            response = chain.invoke({"input": user_input})
            print(f"\nAI: {response.content}")
        except Exception as e:
            print(f"\n错误: {str(e)}")

def test_connection():
    # 简单的连接测试
    try:
        chat_with_ai()
        return True
    except Exception as e:
        print(f"连接测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    test_connection() 