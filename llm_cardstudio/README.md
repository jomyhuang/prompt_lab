# 智能卡牌游戏助手

基于 LangChain 和 Streamlit 开发的智能卡牌游戏系统。

## 项目特点

- 基于 LangChain 框架开发
- 使用 Streamlit 构建用户界面
- 智能卡牌对战系统
- 存档管理功能
- 简洁直观的操作体验

## 系统要求

- Python 3.8+
- 依赖包：
  - langchain
  - streamlit
  - google-generativeai (Gemini-Pro API)

## 项目结构

```
simple01/
├── gui_main.py          # 主程序入口
├── game_manager.py      # 游戏管理核心
├── cards.json           # 卡牌数据配置
├── debug_utils.py       # 调试工具
└── saves/              # 游戏存档目录
```

## 游戏状态说明

1. 游戏主循环状态
   - welcome: 欢迎界面
   - start_game: 游戏开始初始化
   - deal_cards: 发牌阶段
   - determine_first: 决定首轮玩家
   - new_turn: 新回合开始
   - player_turn: 玩家回合
     - start: 回合开始阶段
     - draw_card: 抽牌阶段
     - action: 玩家行动阶段（使用卡牌）
     - end_turn: 回合结束阶段
   - opponent_turn: 对手回合
     - start: 回合开始阶段
     - draw_card: 抽牌阶段
     - action: AI行动阶段（选择使用卡牌）
     - end_turn: 回合结束阶段
   - next_turn: 进入下一回合
   - end_game: 游戏结束

2. 玩家状态
   - hp: 生命值 (初始100)
   - energy: 能量值 (每回合重置)
   - armor: 护甲值

3. 卡牌状态
   - field_cards: 场上的卡牌
   - hand_cards: 手牌
   - deck_state: 
     - deck: 牌组
     - draw_history: 抽牌历史
     - discard_pile: 弃牌堆

4. 回合信息
   - current_turn: 当前回合数
   - active_player: 当前行动玩家
   - phase: 回合阶段

5. 存档数据结构
   ```json
   {
     "info": {
       "save_time": "保存时间",
       "save_name": "存档名称",
       "turn": "当前回合",
       "player_hp": "玩家生命值",
       "opponent_hp": "对手生命值"
     },
     "game_state": "游戏状态数据",
     "deck_state": "卡组状态",
     "selected_decks": "选择的卡组"
   }
   ```

## 核心功能

1. 游戏管理
   - 游戏状态控制
   - 回合制对战系统
   - 卡牌使用机制
   - 存档读写功能

2. 卡牌系统
   - 卡牌效果处理
   - 能量消耗计算
   - 伤害/治疗机制

3. AI 对战
   - AI 决策系统
   - 智能出牌策略
   - 对战日志记录

## 快速开始

1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 运行程序
```bash
streamlit run gui_main.py
```

## 开发规范

1. 代码规范
   - 遵循 PEP8
   - 添加类型注解
   - 编写详细注释

2. 界面开发
   - 使用 Streamlit 标准组件
   - 保持界面简洁
   - 不使用自定义 CSS

## 使用说明

1. 游戏流程
   - 选择卡组开始游戏
   - 回合制对战模式
   - 使用能量打出卡牌
   - 合理利用卡牌效果

2. 存档功能
   - 支持游戏状态保存
   - 可随时读取存档
   - 自动存档管理

## 版本历史

### v0.1.0
- 基础游戏系统实现
- 卡牌对战功能
- 存档管理系统

## 待优化

- [ ] AI 策略优化
- [ ] 更多卡牌效果
- [ ] 对战平衡性调整
- [ ] 界面交互优化

## 问题反馈

如有问题或建议，请提交 Issue
