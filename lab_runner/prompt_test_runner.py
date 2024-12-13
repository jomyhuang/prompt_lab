import json
import os
from typing import Dict, Any, List
from dataclasses import dataclass
from pathlib import Path
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from dotenv import load_dotenv
import logging
import time  # 添加在文件开头的import部分

#import ssl
#ssl._create_default_https_context = ssl._create_unverified_context
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
    execution_time: float = 0.0  # 添加执行时间字段

class PromptTestRunner:
    def __init__(self):
        load_dotenv()
#        model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo")
        
        # 定义提示词目录
        self.prompt_dir = "prompt_engineering/bot194/01"  # 改为正确的目录路径
        
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
        
        # 选择提示词配置
        self.select_prompt_config()
        
        # 根据不同模型配置合适的参数
#        temperature = float(os.getenv("TEMPERATURE", "0.7"))
        
#        self.chat = ChatOpenAI(
#            model=model_name,
#            temperature=temperature,
#            base_url=os.getenv("OPENAI_API_BASE"),
#            api_key=os.getenv("OPENAI_API_KEY"),
#            streaming=True
#        )
        

        # 从文件加载系统提示词
        prompt_file = Path(__file__).parent.parent / self.prompt_dir / self.prompt_filename
        print(f"Loading prompt from: {prompt_file}")
        with open(prompt_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 处理提示词中的变量标记
        content = content.replace("{", "{{").replace("}", "}}")  # 转义所有的花括号
        content = content.replace("{{{{", "{").replace("}}}}", "}")  # 恢复原有的双花括号

#当前输入: {{input}}
#当前上下文: {{context}}

        # 系统提示词模板(注入模板标记)
        self.system_prompt = content + f"""

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
#        self.prompt = ChatPromptTemplate.from_messages([
#            SystemMessage(content=self.system_prompt)
#        ])

#        print(f"使用模型: {model_name}")
        print("提示词加载完成，长度：", len(self.system_prompt))

    def select_prompt_config(self):
        """选择要测试的提示词配置"""
        print("\n📋 可用的提示词系统：")
        for i, name in enumerate(self.prompt_configs.keys(), 1):
            print(f"{i}. {name}")
        
        while True:
            try:
                choice = input("\n请选择要测试的提示词系统 (1-{}): ".format(len(self.prompt_configs)))
                choice = int(choice)
                if 1 <= choice <= len(self.prompt_configs):
                    selected_name = list(self.prompt_configs.keys())[choice - 1]
                    config = self.prompt_configs[selected_name]
                    self.prompt_filename = config["prompt"]
                    self.test_cases_filename = config["test_cases"]
                    print(f"\n✅ 已选择: {selected_name}")
                    print(f"提示词文件: {self.prompt_filename}")
                    print(f"测试用例文件: {self.test_cases_filename}")
                    break
                print(f"❌ 无效的选择，请输入1-{len(self.prompt_configs)}之间的数字")
            except ValueError:
                print("❌ 请输入有效的数字")

    def load_test_cases(self, test_file_path: str) -> List[TestCase]:
        """从Markdown文件加载测试用例"""
        test_cases = []
        
        with open(test_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        def extract_json_content(text: str, marker: str) -> str:
            """从文本中提取JSON内容"""
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
        
        # 分割测试用例部分
        test_sections = content.split('#### 测试用例')
        
        for section in test_sections[1:]:  # 跳过第一个分割（文件头部）
            try:
                # 提取测试用例名称
                name = section.split('\n')[0].strip()
                
                # 提取input.json和output.json内容
                input_text = extract_json_content(section, "input.json")
                output_text = extract_json_content(section, "output.json")
                
                if not input_text or not output_text:
                    print(f"⚠️ 警告: 测试用例 {name} 缺少输入或输出JSON")
                    continue
                
                # 解析JSON
                try:
                    input_json = json.loads(input_text)
                    output_json = json.loads(output_text)
                    
                    test_cases.append(TestCase(
                        name=name,
                        input_data=input_json,
                        expected_output=output_json
                    ))
                    print(f"✅ 成功加载测试用例: {name}")
                except json.JSONDecodeError as je:
                    print(f"❌ JSON解析错误 - 测试用例 {name}:")
                    print(f"  Input JSON:\n{input_text[:200]}")
                    print(f"  Output JSON:\n{output_text[:200]}")
                    print(f"  错误信息: {str(je)}")
                    continue
                    
            except Exception as e:
                print(f"❌ 解析错误 - 测试用例 {name if 'name' in locals() else 'unknown'}:")
                print(f"  错误信息: {str(e)}")
                continue
        
        if not test_cases:
            print("⚠️ 警告: 没有成功加载任何测试用例")
        else:
            print(f"\n📝 总共加载了 {len(test_cases)} 个测试用例")
            
        return test_cases

    def run_test(self, test_case: Dict[str, Any], expected_output: Dict[str, Any]) -> tuple[bool, float]:
        """运行单个测试用例并返回结果和执行时间"""
        start_time = time.time()  # 记录开始时间
        try:
            # 准备输入
            input_json = json.dumps(test_case, ensure_ascii=False, indent=2)
            
            # 构建消息格式
            system_content = self.system_prompt.format(
                input=test_case.get("input", ""),
                context=json.dumps(test_case.get("context", {}), ensure_ascii=False)
            )
            
            # 调用API
            try:
                #result = self.chat.invoke(
                #    [{"role": "system", "content": system_content}]
                #)
                # 使用将context和input 直接变成 HumanMessage
                messages = []
                messages.append(SystemMessage(content=system_content))
                messages.append(HumanMessage(content=input_json))

                #messages.append(SystemMessage(content="you are a helpful assistant."))
                #messages.append(HumanMessage(content="my name is bob."))
                #print(messages)

                result = self.chat.invoke(messages)


                # 解析输出
                try:
                    # 清理响应内容，删除 JSON 前后的所有内容
                    content = result.content
                    json_start = content.find('{')
                    json_end = content.rfind('}')
                    if json_start != -1 and json_end != -1:
                        content = content[json_start:json_end + 1]
                    
                    output = json.loads(content)
                    # 验证输出格式
                    self._validate_output_format(output)
                    # 比较输出
                    if self._compare_outputs(output, expected_output):
                        print(f"✅ 测试通过 (耗时: {time.time() - start_time:.2f}秒)")
                        return True, time.time() - start_time
                    else:
                        print(f"\n❌ 测试失败 (耗时: {time.time() - start_time:.2f}秒)")
                        print("\n测试用例:")
                        print("输入:")
                        print(json.dumps(test_case, ensure_ascii=False, indent=2))
                        print("\n期望输出:")
                        print(json.dumps(expected_output, ensure_ascii=False, indent=2))
                        print("\n实际输出:")
                        print(json.dumps(output, ensure_ascii=False, indent=2))
                        return False, time.time() - start_time
                except json.JSONDecodeError:
                    print(f"\n❌ AI响应不是有效的JSON格式:")
                    print(result.content)
                    print("\n测试用例:")
                    print("输入:")
                    print(json.dumps(test_case, ensure_ascii=False, indent=2))
                    print("\n期望输出:")
                    print(json.dumps(expected_output, ensure_ascii=False, indent=2))
                    return False, time.time() - start_time
                    
            except Exception as e:
                print(f"\n❌ API调用错误: {str(e)}")
                logger.error(f"API调用错误: {str(e)}")
                return False, time.time() - start_time
                
        except Exception as e:
            print(f"\n❌ 测试执行出错: {str(e)} (耗时: {time.time() - start_time:.2f}秒)")
            print("\n测试用例:")
            print("输入:")
            print(json.dumps(test_case, ensure_ascii=False, indent=2))
            print("\n期望输出:")
            print(json.dumps(expected_output, ensure_ascii=False, indent=2))
            return False, time.time() - start_time

    def _compare_outputs(self, actual: Dict[str, Any], expected: Dict[str, Any]) -> bool:
        """比较实际输出和预期输出只检查测试用例中存在的键值"""
        def compare_dicts(actual_dict: Dict[str, Any], expected_dict: Dict[str, Any], path: str = "") -> bool:
            for key, expected_value in expected_dict.items():
                if key not in actual_dict:
                    print(f"❌ 缺少字段 {path}{key}")
                    return False
                    
                actual_value = actual_dict[key]
                
                if isinstance(expected_value, dict):
                    if not isinstance(actual_value, dict):
                        print(f"字段类型不匹配 {path}{key}")
                        return False
                    if not compare_dicts(actual_value, expected_value, f"{path}{key}."):
                        return False
                elif isinstance(expected_value, (int, float)):
                    if not isinstance(actual_value, (int, float)):
                        print(f"❌ 数值类型不匹配 {path}{key}")
                        return False
                    if abs(actual_value - expected_value) > 0.01:  # 允许小数点误差
                        print(f"❌ 数值不匹配 {path}{key}:")
                        print(f"   期望: {expected_value}")
                        print(f"   实际: {actual_value}")
                        return False
                elif isinstance(expected_value, bool):
                    if not isinstance(actual_value, bool):
                        print(f"❌ 布尔类型不匹配 {path}{key}")
                        return False
                    if actual_value != expected_value:
                        print(f"❌ 布尔值不匹配 {path}{key}:")
                        print(f"   期望: {expected_value}")
                        print(f"   实际: {actual_value}")
                        return False
                    
            return True
            
        # 检查测试用例中存在的字段
        return compare_dicts(actual, expected)

    def _validate_output_format(self, output: Dict[str, Any]):
        """验证输出格式是否符合规范"""
        # 基本字段检查
        if not isinstance(output, dict):
            raise ValueError("Output must be a dictionary")
        
        # 检查必需字段是否存在
        required_fields = ["updated_context", "process", "botstatus", "message", "dialogue"]
        for field in required_fields:
            if field not in output:
                raise ValueError(f"Missing required field: {field}")

    def run_model_tests(self, model_name: str, test_cases: List[TestCase]) -> Dict[str, Any]:
        """运行单个模型的所有测试用例并返回结果"""
        # 设置模型
        os.environ["OPENAI_MODEL_NAME"] = model_name
        print(f"\n🔄 开始测试模型: {model_name}")
        
        # 重新初始化 chat 实例
        if "claude" in model_name.lower():
            headers = {
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            max_tokens = 4096
        else:
            headers = None
            max_tokens = None
        
        try:
            self.chat = ChatOpenAI(
                model=model_name,
                temperature=float(os.getenv("TEMPERATURE", "0.7")),
                base_url=os.getenv("OPENAI_API_BASE"),
                api_key=os.getenv("OPENAI_API_KEY"),
                streaming=True
            )
            #使用claude模型，必须强制开启 streaming=True    
            #    default_headers=headers,
            #    max_tokens=max_tokens
            #)
        except Exception as e:
            logger.error(f"初始化模型失败: {str(e)}")
            raise
        
        results = []
        total_time = 0
        test_times = []
        
        for test_case in test_cases:
            print(f"\n🔄 运行测试用例: {test_case.name}")
            result, execution_time = self.run_test(test_case.input_data, test_case.expected_output)
            results.append(result)
            test_times.append(execution_time)
            total_time += execution_time
            
        # 计算统计数据
        total = len(results)
        passed = sum(1 for r in results if r)
        pass_rate = (passed/total)*100 if total > 0 else 0
        avg_time = total_time / total if total > 0 else 0
        
        return {
            "model": model_name,
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": pass_rate,
            "total_time": total_time,
            "avg_time": avg_time,
            "test_times": test_times  # 保存每个测试用例的执行时间
        }

def main():
    # 初始化测试运行器
    runner = PromptTestRunner()
    
    # 加载测试用例
    test_file = Path(__file__).parent.parent / runner.prompt_dir / runner.test_cases_filename
    test_cases = runner.load_test_cases(str(test_file))
    
    # 如果没有测试用例，直接返回
    if not test_cases:
        print("\n❌ 没有可执行的测试用例，程序退出")
        return
    
    # 单选模型列表
    selectable_models = [
        "moonshot-v1-32k",
        "Doubao-pro-128k",
        "gpt-3.5-turbo",
        "claude-3-sonnet-20240229",
        "claude-3-5-sonnet-20240620",
        "claude-3-5-sonnet-20241022",
        "c-3-5-sonnet-20241022",
        "gpt-4-turbo",
        "qwen-max",
        "glm-4"
    ]
    
    # 完整测试模型列表（当选择"测试所有模型"时使用）
    all_test_models = [
        "moonshot-v1-32k",
        "Doubao-pro-128k",
        "claude-3-5-sonnet-20241022",
        "gpt-4-turbo",
        "glm-4"
    ]
    
    # 显示模型列表
    print("\n📋 可用的模型：")
    for i, model in enumerate(selectable_models, 1):
        print(f"{i}. {model}")
    print("0. 测试baseline模型")
    
    # 获取用户选择的模型
    while True:
        try:
            model_choice = input("\n请选择要测试的模型编号 (0-{}): ".format(len(selectable_models)))
            model_choice = int(model_choice)
            if 0 <= model_choice <= len(selectable_models):
                break
            print(f"❌ 无效的选择，请输入0-{len(selectable_models)}之间的数字")
        except ValueError:
            print("❌ 请输入有效的数字")
    
    # 显示测试用例列表
    print("\n📋 可用的测试用例：")
    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}. {test_case.name}")
    print("0. 运行所有测试用例")
    
    # 获取用户选择
    while True:
        try:
            choice = input("\n请选择要运行的测试用例编号 (0-{}): ".format(len(test_cases)))
            choice = int(choice)
            if 0 <= choice <= len(test_cases):
                break
            print(f"❌ 无效的选择，请输入0-{len(test_cases)}之间的数字")
        except ValueError:
            print("❌ 请输入有效的数字")
    
    # 准备要运行的测试用例
    selected_test_cases = test_cases if choice == 0 else [test_cases[choice - 1]]
    
    # 准备要测试的模型
    selected_models = all_test_models if model_choice == 0 else [selectable_models[model_choice - 1]]
    
    # 运行测试并集结果
    model_results = []
    for model in selected_models:
        result = runner.run_model_tests(model, selected_test_cases)
        model_results.append(result)
    
    # 输出比较结果
    print("\n📊 模型测试结果比较:")
    
    # 定义表格格式
    FORMAT = "{:<35} {:>8} {:>8} {:>8} {:>10} {:>12} {:>12}"
    
    # 打印表头和分隔线
    header_line = "=" * 95
    print(header_line)
    print(FORMAT.format(
        "模型名称", "总数", "通过", "失败", "通过率", "总耗时", "平均耗时"
    ))
    print("-" * 95)
    
    # 打印数据行
    for result in model_results:
        print(FORMAT.format(
            result['model'],
            str(result['total']),
            str(result['passed']),
            str(result['failed']),
            f"{result['pass_rate']:.1f}%",
            f"{result['total_time']:.2f}s",
            f"{result['avg_time']:.2f}s"
        ))
    
    print(header_line)
    
    # 如果只运行了一个测试用例，显示详细的时间信息
    if len(selected_test_cases) > 1:
        print("\n📊 各测试用例执行时间:")
        for i, test_case in enumerate(selected_test_cases):
            for result in model_results:
                print(f"{result['model']} - {test_case.name}: {result['test_times'][i]:.2f}秒")

if __name__ == "__main__":
    main()
