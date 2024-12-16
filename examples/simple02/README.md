# LLMCard Studio - 基于大语言模型的卡牌对战游戏框架

LLMCard Studio 是一个创新的卡牌对战游戏框架，它结合了大语言模型(LLM)和Streamlit界面，为玩家提供了一个独特的、基于对话的卡牌对战体验。

## 项目特点

- 基于对话的游戏交互
- 动态卡牌生成系统
- 智能AI对手
- 实时游戏状态可视化
- 灵活的卡牌成本计算模型

## 技术栈

- Python 3.8+
- Streamlit
- LangChain
- OpenAI API

## 项目结构

```
llmcard_studio/
├── streamlit_gui.py      # Streamlit界面实现
├── llm_interaction.py    # LLM交互逻辑
├── game_manager.py       # 游戏状态管理
├── card_manager.py       # 卡牌管理
├── player_manager.py     # 玩家管理
└── card_cost_model.py    # 卡牌成本计算模型
```

## 核心功能

### 1. 对话式交互
- 玩家可以通过自然语言输入来进行游戏操作
- LLM负责解析玩家意图并转换为游戏动作

### 2. 卡牌系统
- 动态卡牌生成
- 卡牌属性平衡
- 智能成本计算

### 3. AI对手
- 基于LLM的智能决策
- 动态策略调整
- 实时响应玩家行动

### 4. 游戏界面
- 实时生命值显示
- 战斗记录查看
- 手牌管理
- 游戏状态监控

## 安装说明

1. 克隆项目
```bash
git clone [项目地址]
cd llmcard_studio
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置环境变量
创建.env文件并配置以下变量：
```
OPENAI_API_KEY=你的OpenAI API密钥
OPENAI_MODEL_NAME=gpt-4
OPENAI_API_BASE=https://api.openai.com/v1
```

4. 启动游戏
```bash
streamlit run streamlit_gui.py
```

## 使用指南

### 开始游戏
1. 运行游戏后，你会看到游戏界面，包含你的生命值、AI对手的生命值和当前手牌
2. 使用自然语言输入来进行游戏操作，例如：
   - "使用第一张卡牌攻击对手"
   - "查看我的手牌信息"
   - "结束我的回合"

### 卡牌操作
- 每张卡牌都有其独特的属性和效果
- 使用卡牌时需要考虑成本和策略
- 可以通过对话来了解卡牌的详细信息

### 对战策略
- 合理管理手牌资源
- 观察AI对手的行为模式
- 利用卡牌组合效果

## 开发指南

### 添加新卡牌类型
1. 在`card_manager.py`中定义新的卡牌类
2. 在`card_cost_model.py`中添加相应的成本计算逻辑
3. 更新LLM提示词模板以支持新卡牌类型

### 自定义AI行为
1. 修改`llm_interaction.py`中的AI响应提示模板
2. 调整AI决策参数
3. 添加新的策略模式

### 扩展游戏功能
1. 在`game_manager.py`中添加新的游戏机制
2. 更新Streamlit界面以支持新功能
3. 完善相应的文档说明

## 贡献指南

欢迎提交Pull Request来改进项目。在提交之前，请确保：

1. 代码符合项目的编码规范
2. 添加了必要的测试用例
3. 更新了相关文档
4. 提供了清晰的提交信息

## 许可证

本项目采用 MIT 许可证
