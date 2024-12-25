# LLM卡牌游戏 Agent系统详细设计

## 1. 多Agent协作系统详细设计

### 1.1 基础Agent类
```python
from langchain.agents import Agent
from langchain.schema import AgentAction, AgentFinish

class BaseCardGameAgent(Agent):
    """卡牌游戏基础Agent类"""
    
    def __init__(self, llm, tools, memory=None):
        self.llm = llm
        self.tools = tools
        self.memory = memory or ConversationBufferMemory()
        
    async def plan(self, inputs: dict) -> Union[AgentAction, AgentFinish]:
        """规划下一步行动"""
        pass
    
    def get_allowed_tools(self) -> List[str]:
        """获取允许使用的工具列表"""
        pass
```

### 1.2 GameMasterAgent详细设计
```python
class GameMasterAgent(BaseCardGameAgent):
    """游戏主持Agent，负责游戏流程控制"""
    
    def __init__(self, llm, tools):
        super().__init__(llm, tools)
        self.game_state = {}
        self.action_history = []
    
    async def validate_action(self, action: dict) -> bool:
        """验证行动合法性"""
        # 检查行动类型
        if action["type"] not in VALID_ACTIONS:
            return False
            
        # 检查资源是否足够
        if not self._check_resources(action):
            return False
            
        # 检查目标是否合法
        if not self._validate_targets(action):
            return False
            
        return True
    
    async def execute_action(self, action: dict) -> dict:
        """执行游戏行动"""
        # 验证行动
        if not await self.validate_action(action):
            raise InvalidActionError("非法行动")
            
        # 执行行动
        result = await self.tools.execute_action(action)
        
        # 更新状态
        self._update_game_state(result)
        
        # 记录历史
        self.action_history.append({
            "action": action,
            "result": result,
            "timestamp": time.time()
        })
        
        return result
    
    def _check_resources(self, action: dict) -> bool:
        """检查资源是否足够"""
        pass
    
    def _validate_targets(self, action: dict) -> bool:
        """验证目标合法性"""
        pass
    
    def _update_game_state(self, result: dict):
        """更新游戏状态"""
        pass
```

### 1.3 StrategyAgent详细设计
```python
class StrategyAgent(BaseCardGameAgent):
    """策略分析Agent，负责策略建议"""
    
    def __init__(self, llm, tools):
        super().__init__(llm, tools)
        self.strategy_cache = LRUCache(1000)
    
    async def analyze_situation(self, game_state: dict) -> dict:
        """分析当前局势"""
        # 分析手牌
        hand_analysis = await self._analyze_hand(game_state["hand_cards"])
        
        # 分析场面
        board_analysis = await self._analyze_board(game_state["field_cards"])
        
        # 分析对手
        opponent_analysis = await self._analyze_opponent(game_state["opponent"])
        
        return {
            "hand_analysis": hand_analysis,
            "board_analysis": board_analysis,
            "opponent_analysis": opponent_analysis
        }
    
    async def suggest_play(self, analysis: dict) -> List[dict]:
        """提供行动建议"""
        suggestions = []
        
        # 根据分析结果生成建议
        if analysis["board_analysis"]["under_threat"]:
            suggestions.extend(await self._generate_defensive_plays())
        else:
            suggestions.extend(await self._generate_offensive_plays())
            
        # 对建议进行排序
        sorted_suggestions = self._rank_suggestions(suggestions)
        
        return sorted_suggestions[:3]  # 返回top 3建议
    
    async def _analyze_hand(self, hand_cards: List[dict]) -> dict:
        """分析手牌"""
        pass
    
    async def _analyze_board(self, field_cards: dict) -> dict:
        """分析场面"""
        pass
    
    async def _analyze_opponent(self, opponent_state: dict) -> dict:
        """分析对手"""
        pass
```

### 1.4 NarratorAgent详细设计
```python
class NarratorAgent(BaseCardGameAgent):
    """解说Agent，负责游戏解说"""
    
    def __init__(self, llm, tools):
        super().__init__(llm, tools)
        self.narrative_style = "default"
        self.language = "zh_CN"
    
    async def generate_narration(self, event: dict) -> str:
        """生成解说文本"""
        # 获取事件模板
        template = self._get_event_template(event["type"])
        
        # 填充模板
        narration = await self._fill_template(template, event)
        
        # 添加情感色彩
        narration = await self._add_emotion(narration, event)
        
        return narration
    
    async def summarize_turn(self, turn_events: List[dict]) -> str:
        """总结回合"""
        summary = []
        
        # 分析关键事件
        key_events = self._identify_key_events(turn_events)
        
        # 生成回合总结
        for event in key_events:
            narration = await self.generate_narration(event)
            summary.append(narration)
            
        return "\n".join(summary)
    
    def _get_event_template(self, event_type: str) -> str:
        """获取事件模板"""
        pass
    
    async def _fill_template(self, template: str, event: dict) -> str:
        """填充模板"""
        pass
    
    async def _add_emotion(self, narration: str, event: dict) -> str:
        """添加情感色彩"""
        pass
```

## 2. 工具集系统详细设计

### 2.1 游戏操作工具（GameTools）
```python
from langchain.tools import BaseTool
from typing import Dict, List, Optional

class CardPlayTool(BaseTool):
    """卡牌使用工具"""
    
    name = "play_card"
    description = "使用一张卡牌"
    
    def _run(self, card_id: str, target_id: Optional[str] = None) -> dict:
        # 验证卡牌
        card = self._get_card(card_id)
        if not card:
            raise ValueError(f"找不到卡牌: {card_id}")
            
        # 验证目标
        if target_id and not self._validate_target(target_id):
            raise ValueError(f"无效的目标: {target_id}")
            
        # 检查费用
        if not self._check_cost(card):
            raise ValueError("费用不足")
            
        # 执行使用卡牌
        result = self._execute_card_play(card, target_id)
        
        return result
    
    async def _arun(self, card_id: str, target_id: Optional[str] = None) -> dict:
        """异步执行"""
        return await asyncio.to_thread(self._run, card_id, target_id)

class AttackTool(BaseTool):
    """攻击工具"""
    
    name = "perform_attack"
    description = "执行攻击行动"
    
    def _run(self, attacker_id: str, target_id: str) -> dict:
        # 验证攻击者
        attacker = self._get_card(attacker_id)
        if not attacker:
            raise ValueError(f"找不到攻击者: {attacker_id}")
            
        # 验证目标
        target = self._get_card(target_id)
        if not target:
            raise ValueError(f"找不到目标: {target_id}")
            
        # 检查攻击是否合法
        if not self._can_attack(attacker):
            raise ValueError("该单位无法攻击")
            
        # 执行攻击
        result = self._execute_attack(attacker, target)
        
        return result
```

### 2.2 查询工具（QueryTools）
```python
class CardInfoTool(BaseTool):
    """卡牌信息查询工具"""
    
    name = "get_card_info"
    description = "获取卡牌详细信息"
    
    def _run(self, card_id: str) -> dict:
        # 从数据库获取卡牌信息
        card_info = self._fetch_card_info(card_id)
        if not card_info:
            raise ValueError(f"找不到卡牌信息: {card_id}")
            
        # 格式化信息
        formatted_info = self._format_card_info(card_info)
        
        return formatted_info

class GameStateTool(BaseTool):
    """游戏状态查询工具"""
    
    name = "get_game_state"
    description = "获取当前游戏状态"
    
    def _run(self) -> dict:
        # 获取基础状态
        base_state = self._get_base_state()
        
        # 获取玩家状态
        player_state = self._get_player_state()
        
        # 获取对手状态
        opponent_state = self._get_opponent_state()
        
        return {
            "base": base_state,
            "player": player_state,
            "opponent": opponent_state
        }
```

### 2.3 分析工具（AnalysisTools）
```python
class BoardAnalysisTool(BaseTool):
    """场面分析工具"""
    
    name = "analyze_board"
    description = "分析当前场面状态"
    
    def _run(self) -> dict:
        # 获取场面信息
        board_state = self._get_board_state()
        
        # 分析优劣势
        advantage = self._analyze_advantage(board_state)
        
        # 分析威胁
        threats = self._analyze_threats(board_state)
        
        # 分析机会
        opportunities = self._analyze_opportunities(board_state)
        
        return {
            "advantage": advantage,
            "threats": threats,
            "opportunities": opportunities
        }

class ValueAnalysisTool(BaseTool):
    """价值分析工具"""
    
    name = "analyze_value"
    description = "分析卡牌或行动的价值"
    
    def _run(self, target_id: str, context: dict) -> dict:
        # 获取目标信息
        target = self._get_target(target_id)
        
        # 计算当前价值
        current_value = self._calculate_value(target, context)
        
        # 预测未来价值
        future_value = self._predict_future_value(target, context)
        
        # 计算协同价值
        synergy_value = self._calculate_synergy(target, context)
        
        return {
            "current_value": current_value,
            "future_value": future_value,
            "synergy_value": synergy_value
        }
```

## 3. Chain处理流程详细设计

### 3.1 游戏流程链（GameChain）
```python
from langchain.chains import Chain
from typing import Dict, Any

class GameChain(Chain):
    """游戏主流程处理链"""
    
    def __init__(
        self,
        game_master: GameMasterAgent,
        strategy: StrategyAgent,
        narrator: NarratorAgent,
        memory: Optional[BaseMemory] = None
    ):
        self.game_master = game_master
        self.strategy = strategy
        self.narrator = narrator
        self.memory = memory or ConversationBufferMemory()
        
    async def _call(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """处理游戏流程"""
        # 1. 获取用户输入
        user_input = inputs["user_input"]
        game_state = inputs["game_state"]
        
        # 2. 游戏主持Agent处理
        try:
            # 解析用户意图
            intent = await self.game_master.parse_intent(user_input)
            
            # 验证行动
            if intent["type"] == "action":
                validated = await self.game_master.validate_action(intent["action"])
                if not validated:
                    raise InvalidActionError("非法行动")
            
            # 执行行动
            action_result = await self.game_master.execute_action(intent)
            
        except GameError as e:
            return {
                "success": False,
                "error": str(e)
            }
        
        # 3. 策略Agent分析
        analysis = await self.strategy.analyze_situation(game_state)
        suggestions = await self.strategy.suggest_play(analysis)
        
        # 4. 解说Agent生成描述
        narration = await self.narrator.generate_narration({
            "action": action_result,
            "analysis": analysis
        })
        
        # 5. 更新记忆
        self.memory.save_context(inputs, {
            "action": action_result,
            "analysis": analysis,
            "narration": narration
        })
        
        return {
            "success": True,
            "action_result": action_result,
            "analysis": analysis,
            "suggestions": suggestions,
            "narration": narration
        }
    
    @property
    def input_keys(self) -> List[str]:
        return ["user_input", "game_state"]
    
    @property
    def output_keys(self) -> List[str]:
        return ["success", "action_result", "analysis", "suggestions", "narration"]
```

### 3.2 对话处理链（DialogueChain）
```python
class DialogueChain(Chain):
    """对话处理链"""
    
    def __init__(
        self,
        llm: BaseLLM,
        memory: Optional[BaseMemory] = None,
        prompt: Optional[BasePromptTemplate] = None
    ):
        self.llm = llm
        self.memory = memory or ConversationBufferMemory()
        self.prompt = prompt or self._get_default_prompt()
        
    async def _call(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """处理对话"""
        # 1. 获取对话历史
        chat_history = self.memory.load_memory_variables({})
        
        # 2. 准备提示词
        prompt = self.prompt.format(
            input=inputs["user_input"],
            chat_history=chat_history,
            game_state=inputs["game_state"]
        )
        
        # 3. 生成回复
        response = await self.llm.agenerate([prompt])
        
        # 4. 更新记忆
        self.memory.save_context(
            inputs,
            {"output": response.generations[0][0].text}
        )
        
        return {
            "response": response.generations[0][0].text,
            "chat_history": chat_history
        }
    
    def _get_default_prompt(self) -> BasePromptTemplate:
        """获取默认提示词模板"""
        template = """
        你是一个卡牌游戏助手。基于以下信息生成回复：
        
        当前游戏状态:
        {game_state}
        
        聊天历史:
        {chat_history}
        
        用户输入:
        {input}
        
        请生成合适的回复。
        """
        
        return PromptTemplate(
            input_variables=["game_state", "chat_history", "input"],
            template=template
        )
```

### 3.3 Chain协调器
```python
class ChainCoordinator:
    """Chain协调器"""
    
    def __init__(
        self,
        game_chain: GameChain,
        dialogue_chain: DialogueChain
    ):
        self.game_chain = game_chain
        self.dialogue_chain = dialogue_chain
        
    async def process(self, user_input: str, game_state: dict) -> dict:
        """处理用户输入"""
        # 1. 对话链处理
        dialogue_result = await self.dialogue_chain.run({
            "user_input": user_input,
            "game_state": game_state
        })
        
        # 2. 游戏链处理
        game_result = await self.game_chain.run({
            "user_input": user_input,
            "game_state": game_state
        })
        
        # 3. 整合结果
        return self._combine_results(dialogue_result, game_result)
    
    def _combine_results(
        self,
        dialogue_result: dict,
        game_result: dict
    ) -> dict:
        """整合处理结果"""
        return {
            "response": dialogue_result["response"],
            "action_result": game_result.get("action_result"),
            "suggestions": game_result.get("suggestions"),
            "narration": game_result.get("narration")
        }
```

这个详细设计文档提供了每个组件的具体实现细节，包括：

1. **Agent系统**：
   - 完整的类结构和方法定义
   - 详细的业务逻辑处理
   - 错误处理机制

2. **工具集**：
   - 具体的工具实现
   - 参数验证
   - 错误处理

3. **Chain处理流程**：
   - 完整的处理流程
   - 状态管理
   - 结果整合

您觉得这些细节是否足够清晰？需要我进一步解释某些部分吗？
