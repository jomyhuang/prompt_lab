# Prompt Lab (提示词实验室)

这是一个专注于LLM(大语言模型)提示词工程的实验项目，用于开发、测试和优化各类AI模型的提示词系统。

## 项目特点

- 支持多个主流LLM模型测试
- 完整的测试用例管理系统
- 详细的性能分析和对比
- 灵活的提示词优化工具

## 支持的模型

- OpenAI系列
  - GPT-3.5-turbo
  - GPT-4-turbo
- Anthropic系列
  - Claude-3-sonnet
- 国内模型
  - Moonshot-v1-32k
  - Doubao-pro-128k
  - GLM-4
  - Qwen-max

## 快速开始

### 1. 环境配置

首先确保你已安装[Anaconda](https://www.anaconda.com/download)或Miniconda。

```bash
# 创建环境
conda env create -f environment.yml

# 激活环境
conda activate prompt_lab
```

### 2. 配置API密钥

创建`.env`文件：

```env
OPENAI_API_KEY=你的OpenAI API密钥
OPENAI_API_BASE=你的API基础URL（可选，使用代理时需要）
OPENAI_MODEL_NAME=gpt-3.5-turbo
PROMPT_FILENAME=prompt.md
TEST_CASES_FILENAME=test_cases.md
PROMPT_DIR=prompt_engineering
TEMPERATURE=0.7
```

## 子项目详细说明

### 1. lab_runner (提示词测试运行器)

核心功能模块：
- `streamlit_prompt_test_runner.py`: 基于Streamlit的GUI测试界面
  - 多模型切换与配置
  - 提示词项目管理
  - 测试用例批量运行
  - 实时结果展示
- `prompt_test_runner.py`: 核心测试引擎
  - 提示词解析与处理
  - 测试用例执行
  - 结果分析与评估
- `test_langchain_connection.py`: 模型连接测试
- `test_logs/`: 测试日志存储
- `dev_instructions.md`: 开发指南文档

配置文件：
- `config.json`: 全局配置
- `.env`: 环境变量配置

### 2. llm_cardstudio (LLM卡牌游戏工作室)

核心模块：
- 游戏引擎
  - `game_manager.py`: 游戏核心管理器
  - `player_manager.py`: 玩家管理系统
  - `model_config.py`: 模型配置管理
  
- LLM交互系统
  - `llm_interaction.py`: 基础LLM交互接口
  - `llm_commands_interaction.py`: 命令系统实现
  - `pe_commands.py`: 提示词命令处理器

- 游戏数据
  - `cards.json`: 卡牌数据定义
  - `decks.json`: 卡组配置
  - `cards_commands.json`: 卡牌命令定义

- 界面实现
  - `gui_main.py`: Streamlit GUI界面
  - `debug_utils.py`: 调试工具

- 测试驱动开发文档
  - `tdd_pe_llm_card.md`: 卡牌系统TDD文档
  - `tdd_gamestate.md`: 游戏状态TDD文档
  - `tdd_gamerules.md`: 游戏规则TDD文档

### 3. llm_game_agent_template (游戏智能体模板)

核心模块：
- 智能体框架
  - `game_agent.py`: 智能体核心实现
  - `agent_tool.py`: 智能体工具集
  - `llm_graph.py`: LangGraph流程图实现
  - `llm_interaction.py`: LLM交互接口

- 游戏实现
  - `games/`: 各类游戏实现目录
  - `main.py`: 主程序入口

- 开发文档
  - `todo.md`: 开发计划
  - `tdd_cli.md`: 命令行接口TDD文档

## 项目结构

```
prompt_lab/
├── lab_runner/                # 提示词测试运行器
├── llm_cardstudio/           # 卡牌游戏工作室
├── llm_game_agent_template/  # 游戏智能体模板
├── prompt_engineering/       # 提示词工程研究
└── environment.yml          # 环境配置文件
```

## 测试用例编写指南

测试用例使用Markdown格式，包含输入和预期输出：

```markdown
#### 测试用例名称

##### input.json
```json
{
    "input": "用户输入内容",
    "context": {
        "key": "上下文信息"
    }
}
```

##### output.json
```json
{
    "response": "期望的输出结果"
}
```
```

## 性能指标

测试结果会显示以下指标：
- 总测试用例数
- 通过用例数
- 失败用例数
- 通过率(%)
- 响应时间统计

## 注意事项

1. API限制
   - 请注意各平台的API调用限制
   - 建议配置合适的重试机制

2. 测试建议
   - 先用单个用例验证
   - 批量测试前检查配置
   - 保存重要测试结果

3. 安全提醒
   - 不要提交API密钥到代码库
   - 定期轮换API密钥
   - 设置合理的费用预算

## 贡献指南

欢迎提交Issue和Pull Request来改进项目。提交时请：

1. 清晰描述改动目的
2. 提供完整的测试用例
3. 更新相关文档

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交Issue或联系项目维护者。
