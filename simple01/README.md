# LangChain 大语言模型应用

这是一个基于 LangChain 框架开发的大语言模型应用，使用 Gemini-Pro 模型实现智能卡牌游戏助手功能。

## 项目结构

- `.env`: 环境变量配置文件
- `gui_main.py`: 主程序入口
- `llm_interaction.py`: LLM交互相关代码
- `streamlit_gui.py`: Streamlit GUI界面
- `card_manager.py`: 卡片管理模块
- `game_manager.py`: 游戏管理模块
- `player_manager.py`: 玩家管理模块
- `cards.json`: 卡牌数据配置文件
- `card_cost_model.py`: 卡牌消耗计算模型
- `debug_utils.py`: 调试工具

## 功能特性

1. 基于LangChain框架与Gemini-Pro模型交互
2. 提供友好的Streamlit Web界面
3. 智能卡牌游戏系统
   - 卡牌管理
   - 游戏状态追踪
   - AI决策支持
4. 玩家管理系统
   - 玩家信息管理
   - 对战记录
5. 智能对话
   - 上下文感知
   - 历史记录管理
   - 智能决策建议

## 环境要求

- Python 3.8+
- LangChain
- Streamlit
- Google Gemini-Pro API Key

## 使用说明

1. 环境配置
   - 复制 `.env.template` 为 `.env`
   - 在 `.env` 文件中配置你的 Google API Key
   ```
   GOOGLE_API_KEY="your-google-api-key-here"
   ```

2. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

3. 运行应用
   ```bash
   streamlit run streamlit_gui.py
   ```

## 开发规范

1. 代码规范
   - 遵循PEP8规范
   - 使用类型注解
   - 添加详细的注释
   - 使用模块化设计

2. 提示词工程
   - 保持提示词清晰严谨
   - 结构化的提示模板
   - JSON格式的输出规范

3. 界面开发
   - 使用Streamlit标准组件
   - 不使用自定义CSS
   - 保持界面简洁直观

## 主要模块说明

1. LLM交互模块 (llm_interaction.py)
   - 管理与Gemini-Pro模型的交互
   - 处理对话历史
   - 生成AI响应

2. 游戏管理模块 (game_manager.py)
   - 管理游戏状态
   - 处理游戏逻辑
   - 协调玩家行动

3. 卡牌系统 (card_manager.py, card_cost_model.py)
   - 卡牌数据管理
   - 消耗计算
   - 效果处理

4. 用户界面 (streamlit_gui.py)
   - 交互界面
   - 游戏状态显示
   - 操作反馈

## 更新日志

### v0.1.0 (2024-12-16)
- 初始版本发布
- 实现基础游戏功能
- 集成Gemini-Pro模型
- 完成Streamlit界面

## 待办事项
- 优化AI响应速度
- 增加更多游戏特性
- 改进用户界面交互
- 添加数据分析功能

## 贡献指南
1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 发起Pull Request

## 问题反馈
如有问题或建议，请提交Issue
