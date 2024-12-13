from langchain_ollama import ChatOllama
from langchain.schema import SystemMessage, HumanMessage

# 1. 定义 Ollama LLM
ollama_llm = ChatOllama(model="llama2") # 使用聊天模型

# 2. 定义 System Message
system_message = SystemMessage(
    content="You are a helpful and witty AI assistant. You should always provide a brief and humorous response."
)

# 3. 对话循环
while True:
    user_input = input("You: ")
    if user_input.lower() in ["quit", "exit", "bye"]:
        break

    # 4. 创建 Human Message
    human_message = HumanMessage(content=user_input)

    # 5. 构建 message 序列
    messages = [system_message, human_message]

    # 6. 调用模型并打印回复
    output = ollama_llm.invoke(messages)
    print(f"Ollama: {output.content.strip()}")