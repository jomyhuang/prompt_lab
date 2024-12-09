# Prompt Lab

这是一个基于LangChain和OpenAI的提示词工程实验项目，专注于开发和测试LLM提示词系统。

## 环境配置

### 1. 安装Conda
如果你还没有安装Conda，请先从[Anaconda官网](https://www.anaconda.com/download)下载并安装。

### 2. 创建环境
在项目根目录下运行以下命令创建新的conda环境：
```bash
conda env create -f environment.yml
```

### 3. 激活环境
```bash
conda activate prompt_lab
```

### 4. 配置环境变量
创建一个`.env`文件，包含以下内容：
```
OPENAI_API_KEY=你的OpenAI API密钥
OPENAI_API_BASE=你的API基础URL（如果使用代理）
OPENAI_MODEL_NAME=gpt-3.5-turbo
```

## 项目结构
- `lab_runner/`: 主要的代码目录
  - `test_langchain_connection.py`: LangChain连接测试模块
- `prompt_engineering/`: LLM提示词实验目录
  - `bot194/`: 提示词系统性实验项目
    - `01/`: 基础角色定义与行为约束实验
    - `02/`: 进阶指令遵循与输出规范实验
  - `town1/`: 结构化输出与状态管理实验
    - 基于JSON Schema的输出格式控制
    - 实现严格的状态追踪与数据一致性
    - 包含完整的指令集与响应规范

## 使用说明
1. 确保已经配置好环境变量
2. 运行测试连接：
```bash
python lab_runner/test_langchain_connection.py
``` 