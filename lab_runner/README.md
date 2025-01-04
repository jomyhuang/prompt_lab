# Lab Runner (提示词测试运行器)

基于 Streamlit 和 LangChain 开发的提示词测试与评估工具。

## 主要功能

### 1. 多模型支持
- OpenAI (GPT-3.5/4)
- Anthropic (Claude)
- 国内模型 (Moonshot/GLM-4等)
- 支持自定义API基础URL

### 2. 提示词测试功能
- 批量测试用例执行
- 实时结果展示
- 性能指标统计
- 测试日志记录

### 3. 可视化界面
- 模型选择与配置
- Temperature参数调节
- 测试用例管理
- 结果即时展示

## 核心文件说明

- `streamlit_prompt_test_runner.py`: Streamlit界面主程序
- `prompt_test_runner.py`: 提示词测试核心逻辑
- `test_langchain_connection.py`: 模型连接测试
- `config.json`: 配置文件
- `.env`: 环境变量配置

## 使用说明

### 环境配置
1. 创建并配置 `.env` 文件:
```env
OPENAI_API_KEY=你的API密钥
OPENAI_API_BASE=API基础URL(可选)
OPENAI_MODEL_NAME=模型名称
TEMPERATURE=0.7
```

### 运行程序
```bash
# 启动Streamlit界面
streamlit run streamlit_prompt_test_runner.py

# 运行连接测试
python test_langchain_connection.py
```

## 注意事项
- 请确保API密钥配置正确
- 建议使用虚拟环境运行
- 测试结果保存在 test_logs 目录
