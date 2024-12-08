# Bot194 提示词自动测试工具开发指示

## 1. 项目概述

### 1.1 目标
创建一个自动化测试工具，用于验证和评估Bot194的提示词系统的正确性、一致性和性能。

### 1.2 核心功能需求
1. 提示词测试执行器
2. 上下文状态管理器
3. 对话流程模拟器
4. 结果验证系统
5. 测试报告生成器

## 2. 详细功能描述

### 2.1 提示词测试执行器
- **功能描述**：
  - 加载和解析测试用例文件
  - 按序执行测试指令
  - 维护测试环境状态
  - 记录测试过程

- **关键特性**：
  - 支持批量测试用例执行
  - 可配置的测试超时机制
  - 测试用例依赖关系管理
  - 测试中断和恢复机制

### 2.2 上下文状态管理器
- **功能描述**：
  - 管理游戏状态数据
  - 追踪资源变化
  - 记录建筑状态
  - 维护事件历史

- **关键特性**：
  - 状态快照和回滚
  - 状态变更验证
  - 状态一致性检查
  - 状态持久化存储

### 2.3 对话流程模拟器
- **功能描述**：
  - 模拟用户输入
  - 验证机器人响应
  - 检查对话连贯性
  - 评估对话质量

- **关键特性**：
  - 多轮对话支持
  - 上下文关联验证
  - 对话模式匹配
  - 情感一致性检查

### 2.4 结果验证系统
- **功能描述**：
  - 验证输出格式
  - 检查业务逻辑
  - 评估性能指标
  - 识别异常情况

- **关键特性**：
  - JSON Schema 验证
  - 业务规则检查
  - 性能阈值监控
  - 异常模式识别

### 2.5 测试报告生成器
- **功能描述**：
  - 生成测试摘要
  - 详细测试记录
  - 错误分析报告
  - 性能统计数据

- **关键特性**：
  - 可配置的报告模板
  - 多种输出格式支持
  - 图表可视化
  - 历史数据对比

## 3. 配置需求

### 3.1 测试用例配置
```json
{
    "testConfig": {
        "timeout": 30000,
        "retries": 3,
        "concurrent": false,
        "saveState": true
    },
    "environmentConfig": {
        "baseContext": "./context/",
        "outputPath": "./reports/",
        "logLevel": "info"
    }
}
```

### 3.2 验证规则配置
```json
{
    "validationRules": {
        "format": ["json", "schema"],
        "logic": ["resources", "buildings", "limits"],
        "dialogue": ["context", "emotion", "style"]
    }
}
```

## 4. 输出规范

### 4.1 测试报告格式
```json
{
    "summary": {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "duration": 0
    },
    "details": [
        {
            "testId": "",
            "status": "",
            "duration": 0,
            "error": null,
            "context": {},
            "output": {}
        }
    ],
    "performance": {
        "avgResponseTime": 0,
        "maxMemoryUsage": 0,
        "errorRate": 0
    }
}
```

### 4.2 错误报告格式
```json
{
    "error": {
        "type": "",
        "message": "",
        "context": {},
        "stack": "",
        "suggestion": ""
    }
}
```

## 5. 开发阶段规划

### 5.1 第一阶段：基础框架
- 搭建测试执行环境
- 实现基本的测试用例解析
- 建立简单的状态管理
- 开发基础验证系统

### 5.2 第二阶段：核心功能
- 完善状态管理机制
- 实现对话流程模拟
- 开发详细的验证规则
- 建立报告生成系统

### 5.3 第三阶段：高级特性
- 添加性能监控
- 实现并发测试
- 开发可视化界面
- 优化错误处理

### 5.4 第四阶段：优化和扩展
- 提升测试效率
- 增加更多验证规则
- 完善报告系统
- 添加插件支持

## 6. 注意事项

### 6.1 开发准则
1. 遵循模块化设计原则
2. 确保代码可测试性
3. 保持良好的错误处理
4. 编写详细的文档

### 6.2 测试重点
1. 提示词格式正确性
2. 业务逻辑准确性
3. 状态管理可靠性
4. 对话质量评估

### 6.3 性能考虑
1. 控制测试执行时间
2. 优化内存使用
3. 减少IO操作
4. 支持大规模测试

## 7. 模型集成框架

### 7.1 LLM 适配层
- **功能描述**：
  - 统一的模型接口抽象
  - 多模型并行测试支持
  - 模型响应对比分析
  - 性能基准测试

- **支持模型**：
  - OpenAI (GPT-3.5/4)
  - Anthropic Claude
  - Google PaLM
  - 本地部署模型
  - 自定义模型接入

### 7.2 LangChain 集成
- **核心组件应用**：
  - Memory 管理
    - 对话历史追踪
    - 上下文窗口优化
    - 状态持久化
  
  - Chains 设计
    - 测试流程链
    - 验证规则链
    - 结果分析链
  
  - Agents 实现
    - 自动测试代理
    - 结果验证代理
    - 报告生成代理
  
  - Prompts 管理
    - 模板版本控制
    - 动态提示词生成
    - A/B测试支持

### 7.3 配置规范扩展
```json
{
    "llmConfig": {
        "providers": {
            "openai": {
                "model": "gpt-4",
                "temperature": 0.7,
                "maxTokens": 2000
            },
            "anthropic": {
                "model": "claude-2",
                "temperature": 0.5
            },
            "local": {
                "endpoint": "http://localhost:8000",
                "model": "llama2"
            }
        },
        "testing": {
            "parallel": true,
            "compareResults": true,
            "metricCollection": true
        }
    },
    "langchainConfig": {
        "memory": {
            "type": "buffer",
            "maxTokens": 4000,
            "persistence": true
        },
        "chains": {
            "maxSteps": 10,
            "timeout": 30000,
            "retry": 3
        },
        "agents": {
            "maxIterations": 5,
            "tools": ["calculator", "validator", "reporter"]
        }
    }
}
```

### 7.4 测试指标扩展
```json
{
    "llmMetrics": {
        "responseTime": {
            "avg": 0,
            "p95": 0,
            "p99": 0
        },
        "tokenUsage": {
            "prompt": 0,
            "completion": 0,
            "total": 0
        },
        "quality": {
            "accuracy": 0,
            "consistency": 0,
            "relevance": 0
        }
    },
    "chainMetrics": {
        "executionTime": 0,
        "stepCount": 0,
        "memoryUsage": 0,
        "successRate": 0
    }
}
```

## 8. LLM测试特性

### 8.1 提示词评估
- 不同模型的理解差异
- 提示词有效性分析
- 上下文窗口优化
- 令牌使用效率

### 8.2 响应质量评估
- 输出一致性检查
- 逻辑连贯性分析
- 语言质量评估
- 创意度量化

### 8.3 性能优化
- 批量处理优化
- 缓存策略
- 并行处理
- 成本控制

### 8.4 安全性考虑
- 提示词注入防护
- 敏感信息过滤
- 模型输出审核
- 访问控制

## 9. 开发阶段规划更新

### 9.1 第一阶段：基础框架
- 原有内容
- 添加基础LLM适配层
- 实现简单的Chain

### 9.2 第二阶段：核心功能
- 原有内容
- 完善多模型支持
- 实现核心Agents

### 9.3 第三阶段：高级特性
- 原有内容
- 优化Chain设计
- 添加高级Memory管理

### 9.4 第四阶段：优化和扩展
- 原有内容
- 实现模型性能对比
- 优化提示词管理

## 10. 注意事项补充

### 10.1 LLM集成考虑
1. API密钥管理
2. 错误重试策略
3. 速率限制处理
4. 成本预算控制

### 10.2 LangChain最佳实践
1. Chain组合优化
2. Memory清理策略
3. Agent行为控制
4. 提示词模板管理

## 11. 开发环境配置

### 11.1 Anaconda环境
```yaml
name: prompt_test
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.10
  - pip
  - langchain
  - openai
  - anthropic
  - pandas
  - numpy
  - pytest
  - jupyter
  - pip:
    - python-dotenv
    - rich
    - textual
    - customtkinter
    - dearpygui
```

### 11.2 UI方案建议

#### 方案1：CustomTkinter
最简单的现代化GUI框架，基于Tkinter但具有现代外观
```python
import customtkinter as ctk

class PromptTester(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("提示词测试工具")
        
        # 设置主题
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # 创建主要组件
        self.prompt_input = ctk.CTkTextbox(self, height=200)
        self.prompt_input.pack(padx=20, pady=10, fill="x")
        
        # 模型选择
        self.model_var = ctk.StringVar(value="GPT-4")
        self.model_select = ctk.CTkOptionMenu(
            self,
            values=["GPT-4", "Claude", "PaLM"],
            variable=self.model_var
        )
        self.model_select.pack(pady=10)
        
        # 测试按钮
        self.test_button = ctk.CTkButton(
            self,
            text="运行测试",
            command=self.run_test
        )
        self.test_button.pack(pady=10)
        
        # 结果显示
        self.result_text = ctk.CTkTextbox(self, height=200)
        self.result_text.pack(padx=20, pady=10, fill="x")

    def run_test(self):
        # 测试逻辑
        pass

# 启动应用
app = PromptTester()
app.mainloop()
```

#### 方案2：DearPyGui
轻量级但功能强大的GUI框架，适合数据展示
```python
import dearpygui.dearpygui as dpg

dpg.create_context()
dpg.create_viewport(title="提示词测试工具")

with dpg.window(label="测试控制台"):
    # 提示词输入
    dpg.add_input_text(
        label="提示词",
        multiline=True,
        height=150,
        tag="prompt_input"
    )
    
    # 模型选择
    dpg.add_combo(
        ["GPT-4", "Claude", "PaLM"],
        label="选择模型",
        default_value="GPT-4",
        tag="model_select"
    )
    
    # 测试按钮
    dpg.add_button(
        label="运行测试",
        callback=lambda: run_test()
    )
    
    # 结果显示
    dpg.add_text("测试结果:", tag="result_label")
    dpg.add_input_text(
        multiline=True,
        readonly=True,
        height=150,
        tag="result_output"
    )

dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
```

#### 方案3：Textual (TUI)
终端界面，最轻量级的选择
```python
from textual.app import App
from textual.widgets import Header, Footer, TextArea, Button, Select
from textual.containers import Container

class PromptTesterTUI(App):
    CSS = """
    Screen {
        layout: grid;
        grid-size: 2;
        grid-gutter: 2;
    }
    
    #prompt_input {
        height: 60%;
        dock: top;
    }
    
    #controls {
        height: 40%;
        dock: bottom;
    }
    """
    
    def compose(self):
        yield Header()
        yield Container(
            TextArea(id="prompt_input", placeholder="输入提示词..."),
            Select([("gpt4", "GPT-4"), ("claude", "Claude")], id="model_select"),
            Button("运行测试", id="test_button"),
            TextArea(id="results", readonly=True),
            id="main_container"
        )
        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "test_button":
            await self.run_test()

    async def run_test(self):
        # 测试逻辑
        pass

# 运行应用
app = PromptTesterTUI()
app.run()
```

#### 方案4：PySimpleGUI
最简单直观的GUI框架之一
```python
import PySimpleGUI as sg

sg.theme('DarkBlue')

layout = [
    [sg.Text('提示词测试工具')],
    [sg.Multiline(size=(50, 10), key='-PROMPT-')],
    [sg.Combo(['GPT-4', 'Claude', 'PaLM'], default_value='GPT-4', key='-MODEL-')],
    [sg.Button('运行测试'), sg.Button('清除')],
    [sg.Multiline(size=(50, 10), key='-OUTPUT-', disabled=True)]
]

window = sg.Window('提示词测试工具', layout)

while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED:
        break
    if event == '运行测试':
        # 测试逻辑
        pass
    if event == '清除':
        window['-PROMPT-'].update('')
        window['-OUTPUT-'].update('')

window.close()
```

#### 方案5：Toga (BeeWare)
原生跨平台GUI框架
```python
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

class PromptTester(toga.App):
    def startup(self):
        main_box = toga.Box(style=Pack(direction=COLUMN))
        
        self.prompt_input = toga.MultilineTextInput(
            placeholder='输入提示词...',
            style=Pack(flex=1)
        )
        
        self.model_select = toga.Selection(
            items=['GPT-4', 'Claude', 'PaLM']
        )
        
        button = toga.Button(
            '运行测试',
            on_press=self.run_test,
            style=Pack(padding=5)
        )
        
        self.output_view = toga.MultilineTextInput(
            readonly=True,
            style=Pack(flex=1)
        )
        
        main_box.add(self.prompt_input)
        main_box.add(self.model_select)
        main_box.add(button)
        main_box.add(self.output_view)
        
        self.main_window = toga.MainWindow(title='提示词测试工具')
        self.main_window.content = main_box
        self.main_window.show()

    def run_test(self, widget):
        # 测试逻辑
        pass

def main():
    return PromptTester('提示词测试', '测试工具')
```

#### 方案6：Urwid
另一个强大的TUI框架
```python
import urwid

class PromptTester:
    def __init__(self):
        self.prompt = urwid.Edit(('prompt', u"提示词:\n"), multiline=True)
        self.model = urwid.RadioButton(
            ['GPT-4', 'Claude', 'PaLM'],
            'GPT-4'
        )
        self.output = urwid.Text("")
        self.button = urwid.Button("运行测试")
        urwid.connect_signal(self.button, 'click', self.run_test)
        
        # 布局
        self.layout = urwid.Pile([
            urwid.LineBox(self.prompt),
            urwid.Divider(),
            urwid.LineBox(urwid.Pile([self.model])),
            self.button,
            urwid.LineBox(self.output)
        ])
        
        self.main = urwid.Filler(self.layout, 'top')
        
    def run_test(self, button):
        # 测试逻辑
        pass

    def run(self):
        urwid.MainLoop(self.main).run()

if __name__ == "__main__":
    app = PromptTester()
    app.run()
```

#### 方案7：Flet
基于Flutter的现代化Python UI框架
```python
import flet as ft

def main(page: ft.Page):
    page.title = "提示词测试工具"
    
    # 创建控件
    prompt_input = ft.TextField(
        multiline=True,
        min_lines=3,
        label="输入提示词",
        width=600
    )
    
    model_dropdown = ft.Dropdown(
        width=200,
        options=[
            ft.dropdown.Option("GPT-4"),
            ft.dropdown.Option("Claude"),
            ft.dropdown.Option("PaLM")
        ]
    )
    
    output_text = ft.TextField(
        multiline=True,
        min_lines=3,
        read_only=True,
        label="测试结果",
        width=600
    )
    
    def run_test(e):
        # 测试逻辑
        pass
    
    test_button = ft.ElevatedButton("运行测试", on_click=run_test)
    
    # 添加到页面
    page.add(
        prompt_input,
        model_dropdown,
        test_button,
        output_text
    )

ft.app(target=main)
```

这些框架各有特点：

1. **PySimpleGUI**：
   - 最容易上手
   - 代码最少
   - 开发速度快
   - 适合快速原型

2. **Toga (BeeWare)**：
   - 原生跨平台
   - 界面美观
   - 性能好
   - 可打包为独立应用

3. **Urwid**：
   - 终端界面
   - 高度可定制
   - 性能优秀
   - 支持复杂布局

4. **Flet**：
   - 现代化UI
   - 基于Flutter
   - 响应式设计
   - 支持Web部署

如果追求最快速简单的实现，建议使用 **PySimpleGUI**，它的学习曲线最平缓，代码最简洁，足够满足基本需求。

### 11.3 界面功能精简
- **核心功能**：
  1. 提示词输入/编辑
  2. 模型选择
  3. 测试执行
  4. 结果显示
  5. 简单的测试历史

- **数据展示**：
  - 文本形式展示结果
  - 简单的状态指示
  - 基础的错误提示

- **交互流程**：
  1. 输入提示词
  2. 选择测试模型
  3. 执行测试
  4. 查看结果

这些方案都比较轻量级，容易上手：
- CustomTkinter：最容易入门，现代化外观
- DearPyGui：性能好，适合数据展示
- Textual：最轻量，终端界面

建议从最简单的 CustomTkinter 开始，需要更多功能再逐步扩展。

### 11.4 部署考虑
1. **本地开发**：
   ```bash
   streamlit run app.py --server.port=8501
   ```

2. **容器化**：
   ```dockerfile
   FROM continuumio/miniconda3
   
   WORKDIR /app
   COPY environment.yml .
   RUN conda env create -f environment.yml
   
   COPY . .
   EXPOSE 8501
   
   CMD ["conda", "run", "-n", "prompt_test", "streamlit", "run", "app.py"]
   ```

3. **多用户支持**：
   - 用户认证
   - 会话管理
   - 资源隔离
   - 并发控制
