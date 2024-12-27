# LLM Card Studio - 智能卡牌游戏助手

基于 LangChain 和 Streamlit 开发的智能卡牌游戏系统。通过大语言模型实现智能对战和交互式游戏体验。

## 项目特点

- 基于 LangChain 框架开发的智能对话系统
- 使用 Streamlit 构建现代化用户界面
- 完整的卡牌对战系统
- 智能 AI 对手
- 存档管理功能
- 简洁直观的操作体验

## 系统要求

- Python 3.8+
- 依赖包：
  - langchain
  - streamlit
  - google-generativeai (Gemini-Pro API)
  - python-dotenv
  - asyncio

## 项目结构

```
llm_cardstudio/
├── gui_main.py                    # 主程序入口和界面
├── game_manager.py                # 游戏管理核心
├── llm_commands_interaction.py    # LLM 命令交互处理
├── llm_interaction.py            # LLM 基础交互
├── player_manager.py             # 玩家管理
├── debug_utils.py                # 调试工具
├── model_config.py               # 模型配置
├── cards.json                    # 卡牌数据
├── cards_commands.json           # 卡牌命令配置
├── decks.json                    # 卡组配置
├── .env                         # 环境变量配置
└── saves/                       # 游戏存档目录
```

## 核心功能

1. 游戏系统
   - 完整的回合制对战系统
   - 智能的 AI 对手决策
   - 卡牌效果处理机制
   - 能量与资源管理
   - 游戏状态保存与加载

2. 卡牌系统
   - 多样化的卡牌类型
   - 复杂的卡牌效果处理
   - 战场位置管理
   - 攻击与防御机制
   - 能量消耗计算

3. 命令系统
   - 基于 JSON 的命令配置
   - 灵活的命令序列处理
   - 异步命令执行
   - 动画效果支持
   - 战斗结果处理

4. AI 对战系统
   - 基于 LLM 的智能决策
   - 动态策略调整
   - 场面评估
   - 优先级判断
   - 目标选择

## 游戏状态系统

1. 游戏主循环状态
   - welcome: 欢迎界面与卡组选择
   - start_game: 游戏初始化
   - deal_cards: 发牌阶段
   - determine_first: 决定先手
   - new_turn: 回合开始
   - player_turn: 玩家回合
   - opponent_turn: AI 对手回合
   - next_turn: 回合切换
   - end_game: 游戏结束

2. 玩家回合状态
   - start: 回合开始
   - draw_card: 抽牌阶段
   - action: 行动阶段
   - end_turn: 回合结束

3. 游戏数据结构
   - 玩家状态 (hp/energy/armor)
   - 场上卡牌管理
   - 手牌管理
   - 卡组状态
   - 回合信息

## 命令系统设计

1. 基础命令类型
   - MOVE_CARD: 卡牌移动
   - PLAY_ANIMATION: 动画效果
   - UPDATE_HEALTH: 生命值更新
   - APPLY_EFFECT: 效果应用
   - SELECT_ATTACKER: 选择攻击者
   - SELECT_TARGET: 选择目标
   - PERFORM_ATTACK: 执行攻击

2. 效果处理器
   - battlecry: 战吼效果
   - deathrattle: 亡语效果
   - taunt: 嘲讽效果
   - charge: 冲锋效果
   - spell_damage: 法术伤害

## 快速开始

1. 环境配置
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

2. 配置环境变量
```bash
# 编辑 .env 文件
GEMINI_API_KEY=your_api_key
MODEL_NAME=gemini-pro
```

3. 运行程序
```bash
streamlit run gui_main.py
```

## 开发指南

1. 代码规范
   - 遵循 PEP8 规范
   - 使用类型注解
   - 添加详细注释
   - 使用异步处理耗时操作

2. 界面开发
   - 使用 Streamlit 标准组件
   - 保持界面简洁清晰
   - 避免自定义 CSS
   - 优化用户交互体验

3. AI 开发
   - 优化 LLM 提示词
   - 完善决策逻辑
   - 增强策略多样性
   - 提升响应速度

## 版本历史

### v0.2.0
- 重构命令系统
- 添加异步支持
- 优化 AI 决策
- 改进界面交互
- 完善存档功能

### v0.1.0
- 基础游戏系统
- 卡牌对战功能
- 存档管理系统

## 待优化

- [ ] AI 策略进一步优化
- [ ] 添加更多卡牌效果
- [ ] 优化对战平衡性
- [ ] 改进界面动画效果
- [ ] 添加游戏音效
- [ ] 实现多人对战模式
- [ ] 优化网络延迟处理
- [ ] 添加排行榜系统

## 问题反馈

如有问题或建议，请提交 Issue
