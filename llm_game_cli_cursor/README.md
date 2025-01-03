# LLM游戏框架

基于LangGraph和Streamlit构建的LLM驱动的游戏框架，支持人机交互的回合制游戏开发。

## 技术栈

- **LangGraph**: 状态管理和工作流控制
- **Streamlit**: 用户界面框架
- **LangChain**: LLM交互和链式调用
- **Python 3.9+**: 开发语言

## 主要特性

- 基于LangGraph的游戏状态管理
- 支持多种LLM模型接入（OpenAI、Google、DeepSeek等）
- 标准化的Streamlit组件界面
- 回合制游戏流程控制
- 实时对话交互系统

## 安装说明

1. 克隆仓库:
```bash
git clone <repository_url>
cd llm_game_cli_cursor
```

2. 安装依赖:
```bash
pip install -r requirements.txt
```

3. 环境配置:
创建`.env`文件并配置以下变量:
```
OPENAI_API_KEY=your_openai_api_key
OPENAI_API_BASE=your_openai_api_base
GOOGLE_API_KEY=your_google_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_API_BASE=your_deepseek_api_base
```

## 项目结构

```
llm_game_cli_cursor/
├── main.py           # 主程序入口和GUI实现
├── game_graph.py     # LangGraph游戏流程和状态管理
├── llm_interaction.py # LLM交互和对话管理
├── requirements.txt  # 项目依赖
└── .env             # 环境变量配置
```

## 核心功能模块

### 1. 游戏状态管理 (game_graph.py)
- LangGraph工作流定义
- 游戏状态转换逻辑
- 回合制流程控制

### 2. LLM交互 (llm_interaction.py)
- 多模型支持
- 对话上下文管理
- 命令解析和执行

### 3. 用户界面 (main.py)
- 游戏状态显示
- 聊天界面
- 操作控制面板
- 实时状态更新

## LangGraph节点说明

游戏流程图由以下核心节点组成：

### 1. 初始化节点 (init)
- 功能：初始化游戏状态
- 设置游戏开始标志
- 初始化玩家回合
- 设置初始可用动作
- 流转至：route节点

### 2. 路由节点 (route)
- 功能：决定下一步流程
- 根据游戏状态进行路由判断
- 更新可用动作列表
- 处理中断和UI更新
- 流转至：player/ai/end节点

### 3. 玩家回合节点 (player)
- 功能：处理玩家回合逻辑
- 验证玩家动作合法性
- 执行玩家命令
- 更新游戏状态
- 流转至：route节点

### 4. AI回合节点 (ai)
- 功能：处理AI回合逻辑
- 生成AI响应
- 执行AI动作
- 更新游戏状态
- 流转至：route节点

### 5. 结束节点 (end)
- 功能：处理游戏结束
- 计算游戏结果
- 更新最终状态
- 结束游戏流程

### 状态转换流程

```
[START] -> [init] -> [route] -> [player/ai] -> [route] -> [end]
                        ^           |
                        |___________|
```

- 游戏开始时从init节点进入
- route节点负责状态判断和流程分发
- player和ai节点交替执行，通过route节点进行切换
- 满足结束条件时，route节点将流程引导至end节点

## 主要功能

1. **游戏流程控制**
   - 回合制游戏流程
   - 状态自动转换
   - 有效动作验证

2. **对话系统**
   - 实时聊天交互
   - 命令解析执行
   - 上下文管理

3. **界面功能**
   - 游戏状态展示
   - 操作按钮控制
   - 聊天消息历史
   - 实时更新机制

## 开发指南

### 状态管理
- 使用`GameGraph`类管理游戏状态
- 实现状态验证和转换
- 处理异常情况

### LLM交互
- 配置模型参数
- 实现对话管理
- 处理API限制

### 界面开发
- 使用Streamlit标准组件
- 实现响应式更新
- 优化用户体验

## 注意事项

1. **API密钥管理**
   - 妥善保管API密钥
   - 使用环境变量配置
   - 注意API使用限制

2. **状态同步**
   - 保持状态一致性
   - 正确处理状态更新
   - 避免并发问题

3. **性能优化**
   - 控制API调用频率
   - 优化状态更新逻辑
   - 合理使用缓存机制 