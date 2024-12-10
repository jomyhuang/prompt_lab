# Prompt Lab (提示词实验室)

这是一个专注于LLM(大语言模型)提示词工程的实验项目，用于开发、测试和优化各类AI模型的提示词系统。

## 项目特点

- 🚀 支持多个主流LLM模型测试
- 📊 完整的测试用例管理系统
- 📈 详细的性能分析和对比
- 🛠 灵活的提示词优化工具

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

创建`lab_runner/.env`文件：

```env
OPENAI_API_KEY=你的OpenAI API密钥
OPENAI_API_BASE=你的API基础URL（可选，使用代理时需要）
OPENAI_MODEL_NAME=gpt-3.5-turbo
PROMPT_FILENAME=prompt.md
TEST_CASES_FILENAME=test_cases.md
PROMPT_DIR=prompt_engineering
TEMPERATURE=0.7
```

### 3. 运行测试

```bash
# 运行基础连接测试
python lab_runner/test_langchain_connection.py

# 运行提示词测试
python lab_runner/prompt_test_runner.py
```

## 项目结构

```
prompt_lab/
├── lab_runner/                # 核心运行代码
│   ├── test_langchain_connection.py
│   └── prompt_test_runner.py
├── prompt_engineering/        # 提示词实验
│   ├── bot194/               # 系统性实验
│   │   ├── 01/              # 基础实验
│   │   └── 02/              # 进阶实验
│   └── town1/                # 特定场景实验
└── environment.yml           # 环境配置文件
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


