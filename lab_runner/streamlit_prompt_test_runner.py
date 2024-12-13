import streamlit as st
import json
import os
from typing import Dict, Any, List
from dataclasses import dataclass
from pathlib import Path
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.llms import Ollama
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from dotenv import load_dotenv
import logging
import time
import datetime
import csv
import pandas as pd
from typing import Optional, Tuple

# 加载环境变量并设置日志
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TestCase:
    name: str
    input_data: Dict[str, Any]
    expected_output: Dict[str, Any]

@dataclass
class TestResult:
    test_case: TestCase
    actual_output: Dict[str, Any]
    passed: bool
    error_message: str = ""
    execution_time: float = 0.0

@dataclass
class ModelVendorConfig:
    name: str                    # 模型商名称
    models: List[str]           # 该商家提供的模型列表
    baseline_models: List[str]  # 该商家的基线模型列表
    api_key_env: str           # 环境变量中API KEY的名称
    base_url: str              # API基础URL
    model_class: Optional[str] = None  # 模型基类名称，可选

# 模型商配置
MODEL_VENDORS = {
    "SMALLAI": ModelVendorConfig(
        name="SmallAI",
        models=["moonshot-v1-32k",
        "Doubao-pro-128k",
        "gemini-2.0-flash-exp",
        "gpt-3.5-turbo",
        "claude-3-sonnet-20240229",
        "claude-3-5-sonnet-20240620",
        "claude-3-5-sonnet-20241022",
        "c-3-5-sonnet-20241022",
        "gpt-4-turbo",
        "qwen-max",
        "glm-4"
        ],  
        baseline_models=["moonshot-v1-32k",
        "Doubao-pro-128k",
        "claude-3-5-sonnet-20241022"
#        "gpt-4-turbo",
#        "glm-4"],
        ],
        api_key_env="SMALLAI_API_KEY",
        base_url="https://ai98.vip/v1",
        model_class="ChatOpenAI"  # 使用 OpenAI 基类
    ),
    "GoogleAPI": ModelVendorConfig(
        name="GoogleAPI",
        models=["gemini-2.0-flash","gemini-1.5-flash","gemini-1.5-pro"],
        baseline_models=["gemini-2.0-flash"],
        api_key_env="GOOGLE_API_KEY",
        base_url=None,
        model_class="ChatGoogleGenerativeAI"
    ),
    "Ollama": ModelVendorConfig(
        name="Ollama",
        models=["llama2", "mistral", "mixtral", "codellama", "qwen", "yi"],
        baseline_models=["mixtral"],
        api_key_env=None,  # Ollama 不需要 API key
        base_url="http://localhost:11434",  # 默认的 Ollama 地址
        model_class="Ollama"
    ),
    "LLMStudio": ModelVendorConfig(
        name="LLMStudio",
        models=["llmstudio"],  # LLMStudio 作为本地服务
        baseline_models=[],
        api_key_env=None,
        base_url="http://localhost:8000",  # 默认的 LLMStudio 地址
        model_class="ChatOpenAI"  # LLMStudio 兼容 OpenAI 接口
    ),
    "Anthropic": ModelVendorConfig(
        name="Anthropic",
        models=["claude-3-opus", "claude-3-sonnet", "claude-2.1", "claude-2", "claude-instant"],
        baseline_models=["claude-3-opus", "claude-2.1"],
        api_key_env="ANTHROPIC_API_KEY",
        base_url="https://api.anthropic.com/v1",
        model_class="ChatAnthropic"
    ),
    "Zhipu": ModelVendorConfig(
        name="Zhipu",
        models=["chatglm_turbo", "chatglm_pro", "chatglm_std", "chatglm_lite", "glm-4", "glm-4v"],
        baseline_models=["glm-4"],
        api_key_env="ZHIPU_API_KEY",
        base_url="https://open.bigmodel.cn/api/paas/v3/model-api",
        model_class="ChatOpenAI"  # 使用 OpenAI 基类
    ),
    "Baidu": ModelVendorConfig(
        name="Baidu",
        models=["ERNIE-Bot-4", "ERNIE-Bot", "ERNIE-Bot-turbo", "ERNIE-Bot-8k"],
        baseline_models=["ERNIE-Bot-4"],
        api_key_env="BAIDU_API_KEY",
        base_url="https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat",
        model_class="ChatOpenAI"  # 使用 OpenAI 基类
    )
}

def get_model_configs():
    """获取模型配置并验证API密钥"""
    available_vendors = {}
    
    for vendor_name, config in MODEL_VENDORS.items():
        # 如果不需要API密钥（本地模型）或者有API密钥
        if config.api_key_env is None:
            available_vendors[vendor_name] = config
        else:
            api_key = os.getenv(config.api_key_env)
            if api_key:
                available_vendors[vendor_name] = config
    
    return available_vendors

class PromptTestRunner:
    def __init__(self):
        load_dotenv()
        
        # 定义提示词目录
        self.prompt_dir = "prompt_engineering/bot194/01"
        
        # 定义日志目录和文件
        self.log_dir = Path(__file__).parent / "test_logs"
        self.log_dir.mkdir(exist_ok=True)
        self.csv_log_file = self.log_dir / "test_results.csv"
        self.detail_log_dir = self.log_dir / "details"
        self.detail_log_dir.mkdir(exist_ok=True)
        
        # 如果CSV文件不存在，创建并写入表头
        if not self.csv_log_file.exists():
            with open(self.csv_log_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    '测试时间',
                    '提示词系统',
                    '模型',
                    '测试用例',
                    '执行时间(秒)',
                    '测试结果',
                    '错误信息',
                    '详细日志文件'
                ])
        
        # 定义提示词配置映射
        self.prompt_configs = {
            "建造系统": {
                "prompt": "bot_skill_build_prompt_02.md",
                "test_cases": "bot_skill_build_test_cases.md"
            },
            "资源管理": {
                "prompt": "resource_manager_prompt_02.md",
                "test_cases": "resource_manager_test_cases.md"
            },
            "数组定义": {
                "prompt": "array_definition_prompt.md",
                "test_cases": "array_definition_test_cases.md"
            },
        }

    def load_prompt(self, prompt_name: str):
        """加载选定的提示词"""
        config = self.prompt_configs[prompt_name]
        self.prompt_filename = config["prompt"]
        self.test_cases_filename = config["test_cases"]
        
        # 从文件加载系统提示词
        prompt_file = Path(__file__).parent.parent / self.prompt_dir / self.prompt_filename
        with open(prompt_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 处理提示词中的变量标记
        content = content.replace("{", "{{").replace("}", "}}")
        content = content.replace("{{{{", "{").replace("}}}}", "}")

        # 系统提示词模板
        self.system_prompt = content + """
注意：
1. 你必须直接返回JSON格式数据，不要在JSON前后添加任何其他文本、对话或说明
2. 返回的JSON必须是一个完整且有效的JSON对象
3. 所有字段值必须符合其预期的数据类型（例如：数字、字符串、布尔值、对象等）
4. 确保所有必需的字段都存在于输出中
5. 不要在JSON中添加注释
6. 输出JSON的键值统一使用小写字母
"""
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt)
        ])
        return len(self.system_prompt)

    def load_test_cases(self, test_file_path: str) -> List[TestCase]:
        """从Markdown文件加载测试用例"""
        test_cases = []
        
        with open(test_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        def extract_json_content(text: str, marker: str) -> str:
            start_marker = f"##### {marker}\n```json"
            end_marker = "```"
            start = text.find(start_marker)
            if start == -1:
                return ""
            start = start + len(start_marker)
            end = text.find(end_marker, start)
            if end == -1:
                return ""
            json_text = text[start:end].strip()
            return json_text
        
        test_sections = content.split('#### 测试用例')
        loaded_cases = []
        errors = []
        
        for section in test_sections[1:]:
            try:
                name = section.split('\n')[0].strip()
                input_text = extract_json_content(section, "input.json")
                output_text = extract_json_content(section, "output.json")
                
                if not input_text or not output_text:
                    errors.append(f"测试用例 {name} 缺少输入或输出JSON")
                    continue
                
                try:
                    input_json = json.loads(input_text)
                    output_json = json.loads(output_text)
                    
                    test_cases.append(TestCase(
                        name=name,
                        input_data=input_json,
                        expected_output=output_json
                    ))
                    loaded_cases.append(name)
                except json.JSONDecodeError as je:
                    errors.append(f"JSON解析错误 - 测试用例 {name}: {str(je)}")
                    continue
                    
            except Exception as e:
                errors.append(f"解析错误 - 测试用例 {name if 'name' in locals() else 'unknown'}: {str(e)}")
                continue
        
        return test_cases, loaded_cases, errors

    def _compare_outputs(self, actual: Dict[str, Any], expected: Dict[str, Any]) -> tuple[bool, list]:
        """比较实际输出和预期输出，返回是否匹配和不匹配的详细信息"""
        def compare_dicts(actual_dict: Dict[str, Any], expected_dict: Dict[str, Any], path: str = "") -> tuple[bool, list]:
            errors = []
            for key, expected_value in expected_dict.items():
                if key not in actual_dict:
                    errors.append(f"缺少字段 {path}{key}")
                    continue
                    
                actual_value = actual_dict[key]
                
                if isinstance(expected_value, dict):
                    if not isinstance(actual_value, dict):
                        errors.append(f"字段类型不匹配 {path}{key}：期望 dict，实际 {type(actual_value).__name__}")
                        continue
                    sub_result, sub_errors = compare_dicts(actual_value, expected_value, f"{path}{key}.")
                    errors.extend(sub_errors)
                elif isinstance(expected_value, (int, float)):
                    if not isinstance(actual_value, (int, float)):
                        errors.append(f"数值类型不匹配 {path}{key}：期望 number，实际 {type(actual_value).__name__}")
                        continue
                    if abs(actual_value - expected_value) > 0.01:
                        errors.append(f"数值不匹配 {path}{key}：期望 {expected_value}，实际 {actual_value}")
                elif isinstance(expected_value, bool):
                    if not isinstance(actual_value, bool):
                        errors.append(f"布尔类型不匹配 {path}{key}：期望 bool，实际 {type(actual_value).__name__}")
                        continue
                    if actual_value != expected_value:
                        errors.append(f"布尔值不匹配 {path}{key}：期望 {expected_value}，实际 {actual_value}")
                elif isinstance(expected_value, str):
                    if not isinstance(actual_value, str):
                        errors.append(f"字段类型不匹配 {path}{key}：期望 string，实际 {type(actual_value).__name__}")
                        continue
                    # 字符串只检查类型，不比较内容
                elif isinstance(expected_value, list):
                    if not isinstance(actual_value, list):
                        errors.append(f"列表类型不匹配 {path}{key}：期望 list，实际 {type(actual_value).__name__}")
                        continue
                    if len(actual_value) != len(expected_value):
                        errors.append(f"列表长度不匹配 {path}{key}：期望 {len(expected_value)}，实际 {len(actual_value)}")
                    # 可以根据需要添加列表元素的详细比较
                    
            return len(errors) == 0, errors
            
        is_match, error_details = compare_dicts(actual, expected)
        return is_match, error_details

    def get_chat_model(self, model_name: str, vendor_config: ModelVendorConfig):
        """根据模型商配置获取对应的聊天模型实例"""
        temperature = float(os.getenv("TEMPERATURE", "0.7"))

        if vendor_config.model_class == "ChatAnthropic":
            return ChatAnthropic(
                model=model_name,
                anthropic_api_key=os.getenv(vendor_config.api_key_env),
                temperature=temperature,
                streaming=True
            )
        elif vendor_config.model_class == "Ollama":
            return Ollama(
                model=model_name,
                base_url=vendor_config.base_url,
                temperature=temperature
            )
        elif vendor_config.model_class == "ChatGoogleGenerativeAI":
            return ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=os.getenv(vendor_config.api_key_env),
                temperature=temperature
                #,convert_system_message_to_human=True
            )
        else:  # 默认使用 ChatOpenAI（包括 LLMStudio，因为它兼容 OpenAI 接口）
            return ChatOpenAI(
                model=model_name,
                temperature=temperature,
                base_url=vendor_config.base_url,
                api_key=os.getenv(vendor_config.api_key_env),
                streaming=True
            )

    def run_test(self, test_case: Dict[str, Any], expected_output: Dict[str, Any], model_name: str) -> tuple[bool, Dict[str, Any], float, str]:
        """运行单个测试用例并返回结果、实际输出、执行时间和错误信息"""
        start_time = time.time()
        error_msg = ""
        actual_output = {}
        
        try:
            input_json = json.dumps(test_case, ensure_ascii=False, indent=2)
            
            system_content = self.system_prompt.format(
                input=test_case.get("input", ""),
                context=json.dumps(test_case.get("context", {}), ensure_ascii=False)
            )
            
            try:
                # 获取当前选中的模型商配置
                vendor_config = st.session_state.selected_vendor
                
                # 根据模型商配置获取聊天模型实例
                chat = self.get_chat_model(model_name, vendor_config)
                
                messages = [
                    SystemMessage(content=system_content),
                    HumanMessage(content=input_json)
                ]
                
                result = chat.invoke(messages)
                
                try:
                    content = result.content
                    json_start = content.find('{')
                    json_end = content.rfind('}')
                    if json_start != -1 and json_end != -1:
                        content = content[json_start:json_end + 1]
                    
                    actual_output = json.loads(content)
                    self._validate_output_format(actual_output)
                    
                    is_match, error_details = self._compare_outputs(actual_output, expected_output)
                    if is_match:
                        return True, actual_output, time.time() - start_time, ""
                    else:
                        error_msg = "输出与预期不匹配：\n" + "\n".join(error_details)
                        return False, actual_output, time.time() - start_time, error_msg
                        
                except json.JSONDecodeError:
                    error_msg = "AI响应不是有效的JSON格式"
                    return False, {}, time.time() - start_time, error_msg
                    
            except Exception as e:
                error_msg = f"API调用错误: {str(e)}"
                return False, {}, time.time() - start_time, error_msg
                
        except Exception as e:
            error_msg = f"测试执行出错: {str(e)}"
            return False, {}, time.time() - start_time, error_msg

    def _validate_output_format(self, output: Dict[str, Any]):
        """验证输出格式是否符合规范"""
        if not isinstance(output, dict):
            raise ValueError("Output must be a dictionary")
        
        required_fields = ["updated_context", "process", "botstatus", "message", "dialogue"]
        for field in required_fields:
            if field not in output:
                raise ValueError(f"Missing required field: {field}")

    def save_test_results(self, prompt_system: str, model: str, case_name: str, 
                         result: Dict[str, Any], test_time: str = None):
        """保存测试结果到CSV和详细日志文件"""
        if test_time is None:
            test_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
        # 创建详细日志文件名
        detail_file_name = f"{test_time.replace(':', '-')}_{model}_{case_name}.json"
        detail_file_path = self.detail_log_dir / detail_file_name
        
        # 保存详细结果到JSON文件
        with open(detail_file_path, 'w', encoding='utf-8') as f:
            json.dump({
                "test_time": test_time,
                "prompt_system": prompt_system,
                "model": model,
                "case_name": case_name,
                "input_data": result["input_data"],
                "expected_output": result["expected_output"],
                "actual_output": result["actual_output"],
                "passed": result["passed"],
                "execution_time": result["execution_time"],
                "error": result["error"]
            }, f, ensure_ascii=False, indent=2)
        
        # 保存结果到CSV文件
        with open(self.csv_log_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                test_time,
                prompt_system,
                model,
                case_name,
                f"{result['execution_time']:.2f}",
                "通过" if result["passed"] else "失败",
                result["error"] or "",
                detail_file_name
            ])

def main():
    st.set_page_config(
        page_title="Prompt Test Runner",
        page_icon="🧪",
        layout="wide"
    )
    
    st.title("🧪 Prompt Test Runner")
    
    # 初始化测试运行器
    if 'runner' not in st.session_state:
        st.session_state.runner = PromptTestRunner()
        st.session_state.test_cases = []
        st.session_state.loaded_cases = []
        st.session_state.errors = []
        st.session_state.results = {}
    
    # 获取可用的模型商配置
    available_vendors = get_model_configs()
    
    if not available_vendors:
        st.error("未找到任何可用的模型配置，请检查环境变量中的API密钥设置")
        return
        
    # 可选模型列表
    models = []
    for vendor in available_vendors.values():
        models.extend(vendor.models)
    
    # baseline 模型列表
    baseline_models = []
    for vendor in available_vendors.values():
        baseline_models.extend(vendor.baseline_models)
    
    # 侧边栏配置
    with st.sidebar:
        st.header("配置")
        
        # 选择模型商
        vendor_names = list(available_vendors.keys())
        selected_vendor_name = st.selectbox(
            "选择模型商",
            options=vendor_names,
            key="vendor_selector"
        )
        
        # 获取选中的模型商配置
        selected_vendor = available_vendors[selected_vendor_name]
        st.session_state.selected_vendor = selected_vendor
        
        # 当模型商改变时，重置选中的模型列表
        if ('previous_vendor' not in st.session_state or 
            st.session_state.previous_vendor != selected_vendor_name):
            st.session_state.selected_models = [selected_vendor.models[0]]
            st.session_state.previous_vendor = selected_vendor_name
        
        # 选择基线模型按钮
        if st.button("选择基线模型"):
            st.session_state.selected_models = selected_vendor.baseline_models
        
        # 多选模型
        selected_models = st.multiselect(
            "选择要测试的模型",
            options=selected_vendor.models,
            default=st.session_state.selected_models
        )
        # 更新选中的模型
        st.session_state.selected_models = selected_models
    
    # 主界面
    if st.button("加载提示词和测试用例", key="load_button"):
        with st.spinner("正在加载..."):
            # 加载提示词
            prompt_length = st.session_state.runner.load_prompt("建造系统")
            st.success(f"提示词加载完成，长度：{prompt_length}")
            
            # 加载测试用例
            test_file = Path(__file__).parent.parent / st.session_state.runner.prompt_dir / st.session_state.runner.test_cases_filename
            st.session_state.test_cases, st.session_state.loaded_cases, st.session_state.errors = st.session_state.runner.load_test_cases(str(test_file))
            
            if st.session_state.test_cases:
                st.success(f"成功加载 {len(st.session_state.test_cases)} 个测试用例")
            if st.session_state.errors:
                st.error("\n".join(st.session_state.errors))
    
    # 主界面
    if st.session_state.test_cases:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("测试用例")
            
            # 初始化选中的测试用例
            if 'selected_test_cases' not in st.session_state:
                st.session_state.selected_test_cases = [st.session_state.test_cases[0].name]
            
            # 选择全部按钮
            if st.button("选择全部用例"):
                st.session_state.selected_test_cases = [case.name for case in st.session_state.test_cases]
            
            # 测试用例多选框
            selected_cases = st.multiselect(
                "选择要运行的测试用例",
                options=[case.name for case in st.session_state.test_cases],
                default=st.session_state.selected_test_cases
            )
            # 更新选中的测试用例
            st.session_state.selected_test_cases = selected_cases
        
        with col2:
            st.subheader("运行测试")
            
            # 显示已选择的模型列表（单行紧凑显示）
            if st.session_state.selected_models:
                model_list = ", ".join([f"`{model}`" for model in st.session_state.selected_models])
                st.markdown(f"已选择的模型: {model_list}")
            
            if st.button("运行测试"):
                st.session_state.results = {}
                
                # 对每个选中的模型运行测试
                test_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                for model in st.session_state.selected_models:
                    st.subheader(f"模型: {model}")
                    model_results = {}
                    
                    for case_name in st.session_state.selected_test_cases:
                        test_case = next(case for case in st.session_state.test_cases if case.name == case_name)
                        with st.spinner(f"正在运行测试用例: {case_name}"):
                            passed, actual_output, execution_time, error = st.session_state.runner.run_test(
                                test_case.input_data,
                                test_case.expected_output,
                                model
                            )
                            
                            result = {
                                "passed": passed,
                                "execution_time": execution_time,
                                "error": error,
                                "actual_output": actual_output,
                                "expected_output": test_case.expected_output,
                                "input_data": test_case.input_data
                            }
                            
                            model_results[case_name] = result
                            
                            # 保存测试结果
                            st.session_state.runner.save_test_results(
                                "建造系统",
                                model,
                                case_name,
                                result,
                                test_time
                            )
                    
                st.session_state.results[model] = model_results
        
        # 显示测试结果
        if st.session_state.results:
            st.subheader("测试结果")
            
            # 为每个模型显示结果
            for model, model_results in st.session_state.results.items():
                st.markdown(f"### 模型: {model}")
                
                # 计算统计数据
                total = len(model_results)
                passed = sum(1 for r in model_results.values() if r["passed"])
                failed = total - passed
                pass_rate = (passed/total)*100 if total > 0 else 0
                total_time = sum(r["execution_time"] for r in model_results.values())
                avg_time = total_time / total if total > 0 else 0
                
                # 显示统计信息
                cols = st.columns(6)
                cols[0].metric("总用例数", total)
                cols[1].metric("通过", passed)
                cols[2].metric("失败", failed)
                cols[3].metric("通过率", f"{pass_rate:.1f}%")
                cols[4].metric("总耗时", f"{total_time:.2f}秒")
                cols[5].metric("平均耗时", f"{avg_time:.2f}秒")
                
                # 显示详细结果
                for case_name, result in model_results.items():
                    with st.expander(f"{'✅' if result['passed'] else '❌'} {case_name} ({result['execution_time']:.2f}秒)"):
                        if result["error"]:
                            st.error(result["error"])
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.subheader("输入")
                            st.json(result["input_data"])
                        
                        with col2:
                            st.subheader("期望输出")
                            st.json(result["expected_output"])
                        
                        with col3:
                            st.subheader("实际输出")
                            if result["actual_output"]:
                                st.json(result["actual_output"])
                            else:
                                st.error("无输出")

        # 添加查看历史记录部分
        st.divider()  # 添加分隔线
        st.subheader("历史记录查看")
        
        if os.path.exists(st.session_state.runner.csv_log_file):
            # 下载按钮和最近记录显示
            with open(st.session_state.runner.csv_log_file, 'r', encoding='utf-8') as f:
                csv_content = f.read()
            st.download_button(
                "下载CSV测试记录",
                csv_content,
                "test_results.csv",
                "text/csv",
                key='download_csv'
            )
            
            # 显示最近的测试记录
            st.subheader("最近的测试记录")
            df = pd.read_csv(st.session_state.runner.csv_log_file)
            st.dataframe(df.tail(10))
            
            # 三栏布局显示详细日志
            st.subheader("详细日志查看")
            log_files = list(st.session_state.runner.detail_log_dir.glob("*.json"))
            if log_files:
                # 按修改时间排序，最新的在前面
                log_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                
                # 创建一个更友好的显示格式
                log_options = {}
                for f in log_files:
                    # 获取文件修改时间
                    mtime = datetime.datetime.fromtimestamp(os.path.getmtime(f))
                    # 创建显示名称：时间 - 模型 - 测试用例
                    display_name = f"{mtime.strftime('%Y-%m-%d %H:%M:%S')} - {f.stem}"
                    log_options[display_name] = f
                
                # 上部分：两栏布局显示日志列表和基本信息
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 日志列表")
                    selected_log_display = st.selectbox(
                        "选择要查看的日志",
                        options=list(log_options.keys()),
                        key='log_selector_new'
                    )
                
                if selected_log_display:
                    selected_log_file = log_options[selected_log_display]
                    with open(selected_log_file, 'r', encoding='utf-8') as f:
                        log_data = json.load(f)
                        
                    with col2:
                        st.markdown("#### 测试信息")
                        st.write(f"**测试时间:** {log_data['test_time']}")
                        st.write(f"**提示词系统:** {log_data['prompt_system']}")
                        st.write(f"**模型:** {log_data['model']}")
                        st.write(f"**测试用例:** {log_data['case_name']}")
                        st.write(f"**执行时间:** {log_data['execution_time']:.2f}秒")
                        st.write(f"**测试结果:** {'✅ 通过' if log_data['passed'] else '❌ 失败'}")
                        if log_data['error']:
                            st.error(f"错误信息:\n{log_data['error']}")
                    
                    # 下部分：三栏布局显示数据
                    st.divider()
                    data_col1, data_col2, data_col3 = st.columns(3)
                    
                    with data_col1:
                        st.markdown("#### 输入数据")
                        st.json(log_data['input_data'])
                    
                    with data_col2:
                        st.markdown("#### 期望输出")
                        st.json(log_data['expected_output'])
                        
                    with data_col3:
                        st.markdown("#### 实际输出")
                        st.json(log_data['actual_output'])

if __name__ == "__main__":
    main()
