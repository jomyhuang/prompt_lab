from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain  # 修复导入路径
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
from langchain.tools import tool
from langchain_anthropic import ChatAnthropic

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
        use_model= "deepseek"
        if use_model == "google":
            # 初始化Gemini模型
            model = "gemini-2.0-flash-exp"
            # model = os.getenv("GOOGLE_MODEL_NAME", "gemini-pro")
            # base_url = os.getenv("OPENAI_API_BASE")
            self.llm = ChatGoogleGenerativeAI(
                api_key=os.getenv("GOOGLE_API_KEY"),
                model=model,    # 从环境变量读取模型名称，默认为gemini-pro
                temperature=0,
                streaming=True
            )
            print(f"使用Gemini模型 {model}")
        elif use_model == "claude":
            model = "claude-3-5-sonnet-20241022"
            base_url = os.getenv("OPENAI_API_BASE")
            # small.AI (tool calling 错误)
            # self.llm = ChatAnthropic(
            self.llm = ChatOpenAI(
                model=model,
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=base_url,
                temperature=0,
                streaming=True
            )
            print(f"使用ChatAnthropic模型 {model}，API BASE URL={base_url}")
        elif use_model == "deepseek":
            # 初始化OpenAI模型
            model = "deepseek-chat"
            # model=os.getenv("OPENAI_MODEL_NAME", "gpt-4")    # 从环境变量读取模型名称，默认为gpt-4
            base_url = os.getenv("DEEPSEEK_API_BASE")
            self.llm = ChatOpenAI(
                api_key=os.getenv("DEEPSEEK_API_KEY"),
                model=model,
                base_url=base_url,
                temperature=0,
                streaming=True
            )
            print(f"使用DeepSeek官方模型 {model}，API BASE URL={base_url}")
        else:
            # 初始化OpenAI模型
            model = "gpt-3.5-turbo-1106"
            # model=os.getenv("OPENAI_MODEL_NAME", "gpt-4")    # 从环境变量读取模型名称，默认为gpt-4
            base_url = os.getenv("OPENAI_API_BASE")
            self.llm = ChatOpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                model=model,
                base_url=base_url,
                temperature=0,
                streaming=True
            )
            print(f"使用OpenAI模型 {model}，API BASE URL={base_url}")


        # 初始化对话历史
        self.chat_history = []
        self.last_game_state = None
        self.commands_processor = None  # 将在后续设置
    
        # 设置上下文提示模板
        context_template = """你是一个卡牌游戏AI助手。基于以下信息帮助玩家：
        
        当前游戏状态:
        {game_state}
        
        聊天历史:
        {chat_history}
        
        玩家输入:
        {user_input}
        
        你可以使用以下工具：
        - start_game: 开始新游戏
        - end_turn: 结束当前回合
        - play_card: 打出一张手牌
        - attack: 使用卡牌进行攻击
        
        请分析情况并给出建议或执行相应操作。如果玩家的输入不需要执行具体操作，直接给出对话回复即可。
        """
        
        # 使用新的 LLMChain API
        self.context_prompt = ChatPromptTemplate.from_template(context_template)
        self.context_chain = self.context_prompt | self.llm

    def set_commands_processor(self, processor):
        """设置命令处理器实例"""
        self.commands_processor = processor
        # 绑定工具到LLM
        if self.commands_processor and hasattr(self.commands_processor, 'game_tools'):
            tools = [
                self.commands_processor.start_game,
                self.commands_processor.end_turn,
                self.commands_processor.play_card,
                self.commands_processor.attack
            ]
            self.llm_with_tools = self.llm.bind_tools(tools)

    async def generate_ai_response(self, user_input: str, game_state: dict) -> str:
        """生成AI响应，支持工具调用
        
        Args:
            user_input: 用户输入
            game_state: 当前游戏状态
        
        Returns:
            str: AI的响应或工具调用的结果
        """
        if not self.commands_processor:
            return "系统未准备好，请稍后再试"
            
        # 确保工具已经绑定
        if not hasattr(self, 'llm_with_tools'):
            self.set_commands_processor(self.commands_processor)
            
        # 准备上下文消息
        context_str = f"""游戏状态：
{json.dumps(game_state, ensure_ascii=False, indent=2)}

聊天历史：
{self.format_history()}

玩家输入: {user_input}

你可以使用以下工具：
- start_game: 开始新游戏
- end_turn: 结束当前回合
- play_card: 打出一张手牌
- attack: 使用卡牌进行攻击

请分析情况并给出建议或执行相应操作。如果玩家的输入不需要执行具体操作，直接给出对话回复即可。
"""
        
        # 先尝试使用带工具的LLM进行响应
        # simple_context = f"你是一个AI游戏助手，负责管理卡牌游戏的对话和决策。玩家输入: {user_input}"
        print("llm_with_tools.ainvoke:", user_input)
        # response = self.llm_with_tools.invoke(simple_context)
        # response = self.llm_with_tools.invoke(context_str).tool_calls
        response = self.llm_with_tools.invoke(context_str)
        # response = await self.llm_with_tools.ainvoke(context_str)
        # response = await self.llm_with_tools.ainvoke(user_input)
        
        # 检查是否有工具调用
        if hasattr(response, 'tool_calls') and response.tool_calls:
            tool_results = []
            for tool_call in response.tool_calls:
                # 执行工具调用
                if isinstance(tool_call, dict):
                    tool_name = tool_call.get('name')
                    args = tool_call.get('args', {})
                else:
                    tool_name = tool_call.name
                    args = tool_call.args
                
                if tool_name:
                    # 找到对应的工具
                    matching_tools = [t for t in self.commands_processor.game_tools if t.name == tool_name]
                    if matching_tools:
                        tool = matching_tools[0]
                        print(f"工具 {tool_name} 调用参数:", args)
                        try:
                            # 使用工具的 invoke 方法
                            result = tool.invoke(args)
                            tool_results.append(f"工具 {tool_name} 调用结果： {result}")
                        except Exception as e:
                            print(f"工具 {tool_name} 调用失败，原因: {str(e)}")
                            tool_results.append(f"工具 {tool_name} 调用失败，原因: {str(e)}")
                    else:
                        print(f"未找到工具: {tool_name}")
                        print(f"可用工具: {[t.name for t in self.commands_processor.game_tools]}")
                        tool_results.append(f"未找到工具: {tool_name}")
            
            # 打印工具调用结果
            if tool_results:
                print("tool_results:")
                for r in tool_results:
                    print(r)
            else:
                print("tool_results [空]")
        
        # 如果响应中有内容，直接使用
        if hasattr(response, 'content') and response.content:
            content = response.content
            # 如果内容是列表，取第一个非空元素
            if isinstance(content, list):
                content = next((item for item in content if item and isinstance(item, str)), "")
            # 更新对话历史
            self.add_to_history("assistant", content)
            return content
            
        # 如果没有工具调用也没有内容，使用普通对话链生成响应
        chat_response = await self.context_chain.ainvoke({
            "game_state": game_state,
            "chat_history": self.format_history(),
            "user_input": user_input
        })
        
        content = chat_response.content
        # 如果内容是列表，取第一个非空元素
        if isinstance(content, list):
            content = next((item for item in content if item and isinstance(item, str)), "")
        
        # 更新对话历史
        self.add_to_history("assistant", content)
        
        return content
                
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
    
    def clear_history(self):
        """清除对话历史"""
        self.chat_history = []
        
    def get_chat_history(self):
        """获取对话历史"""
        return self.chat_history