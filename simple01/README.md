# LangChain 大语言模型应用

这是一个基于 LangChain 框架开发的大语言模型应用。

## 项目结构

- `.env`: 环境变量配置文件
- `main.py`: 主程序入口
- `llm_interaction.py`: LLM交互相关代码
- `streamlit_gui.py`: Streamlit GUI界面
- `card_manager.py`: 卡片管理模块
- `game_manager.py`: 游戏管理模块
- `player_manager.py`: 玩家管理模块

## 功能特性

1. 基于LangChain框架与大语言模型交互
2. 提供友好的Web界面
3. 支持卡片游戏系统
4. 玩家管理系统

## 环境要求

- Python 3.8+
- LangChain
- Streamlit
- OpenAI API Key

## 使用说明

1. 配置环境变量
   在 `.env` 文件中配置必要的API密钥

2. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

3. 运行应用
   ```bash
   streamlit run streamlit_gui.py
   ```

## 开发规范

1. 代码遵循PEP8规范
2. 使用类型注解
3. 添加详细的注释
4. 使用模块化设计

## 更新日志

### v0.1.0
- 初始版本
- 基础功能实现
