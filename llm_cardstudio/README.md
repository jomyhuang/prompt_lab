# LLM Card Studio (智能卡牌游戏开发工作室)

基于大语言模型的智能卡牌游戏开发平台，集成了游戏设计、开发和测试的完整工具链。

## 核心特性

### 1. LLM 命令交互系统
- 智能命令解析与执行
- 多模型支持与切换
- 自然语言游戏规则解释
- 动态规则调整

### 2. 游戏管理系统
- 完整的游戏状态管理
- 回合制对战系统
- 卡牌效果处理器
- 存档管理功能

### 3. GUI 界面
- 基于 Streamlit 的现代界面
- 实时游戏状态展示
- 卡牌操作可视化
- 对战记录回放

## 项目结构

```
llm_cardstudio/
├── gui_main.py                    # GUI主程序
├── game_manager.py               # 游戏核心管理器
├── llm_commands_interaction.py   # LLM命令交互系统
├── llm_interaction.py           # LLM基础交互
├── pe_commands.py               # 提示词命令处理
├── model_config.py              # 模型配置
├── debug_utils.py               # 调试工具
├── cards.json                   # 卡牌数据
├── decks.json                   # 卡组配置
└── docs/                        # 文档目录
```

## 测试驱动开发文档

- `tdd_gamerules.md`: 游戏规则测试用例
- `tdd_gamestate.md`: 游戏状态管理测试
- `tdd_pe_llm_card.md`: LLM卡牌交互测试

## 配置说明

### 环境配置
1. 创建并配置 `.env` 文件:
```env
OPENAI_API_KEY=你的API密钥
MODEL_NAME=选用的模型
```

### 卡牌配置 (cards.json)
```json
{
  "card_id": {
    "name": "卡牌名称",
    "type": "卡牌类型",
    "cost": "能量消耗",
    "effect": "效果描述"
  }
}
```

## 开发指南

### 添加新卡牌
1. 在 `cards.json` 中定义卡牌属性
2. 实现卡牌效果处理器
3. 添加对应的测试用例
4. 更新游戏平衡性文档

### 自定义游戏规则
1. 修改 `game_manager.py` 中的规则定义
2. 更新 LLM 提示词模板
3. 测试新规则的交互效果

## 注意事项
- 确保 API 密钥配置正确
- 定期备份游戏存档
- 遵循测试驱动开发流程
- 保持代码文档的同步更新
