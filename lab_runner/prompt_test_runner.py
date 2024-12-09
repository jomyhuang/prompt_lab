import json
import os
from typing import Dict, Any, List
from dataclasses import dataclass
from pathlib import Path
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

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

class PromptTestRunner:
    def __init__(self):
        load_dotenv()
        self.chat = ChatOpenAI(
            model_name=os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo"),
            temperature=float(os.getenv("TEMPERATURE", "0.7")),
            openai_api_base=os.getenv("OPENAI_API_BASE"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            default_headers={"Content-Type": "application/json"}
        )
        
        # 从文件加载系统提示词
        prompt_file = "f:/Projects/prompt_lab/prompt_engineering/bot194/01/bot_skill_build_prompt_02.md"
        print(f"Loading prompt from: {prompt_file}")
        with open(prompt_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 处理提示词中的变量标记
        content = content.replace("{", "{{").replace("}", "}}")  # 转义所有的花括号
        content = content.replace("{{{{", "{").replace("}}}}", "}")  # 恢复原有的双花括号
            
        # 系统提示词模板
        self.system_prompt = content + f"""

当前输入: {{input}}
当前上下文: {{context}}

完整输入JSON:
{{input_json}}

注意：你必须直接返回JSON格式数据，不要在JSON前后添加任何其他文本、对话或说明。
"""

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
        ])
        print("提示词加载完成，长度：", len(self.system_prompt))
        self.chain = self.prompt | self.chat

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

    def run_test(self, test_case: Dict[str, Any], expected_output: Dict[str, Any]) -> bool:
        """运行单个测试用例"""
        try:
            # 准备输入
            input_json = json.dumps(test_case, ensure_ascii=False, indent=2)
            
            # 调用chain
            result = self.chain.invoke({
                "input": test_case.get("input", ""),
                "context": json.dumps(test_case.get("context", {}), ensure_ascii=False),
                "input_json": input_json
            })
            
            # 解析输出
            try:
                output = json.loads(result.content)
                # 验证输出格式
                self._validate_output_format(output)
                # 比较输出
                if self._compare_outputs(output, expected_output):
                    print(f"✅ 测试通过")
                    return True
                else:
                    print("\n❌ 测试失败")
                    print("\n测试用例:")
                    print("输入:")
                    print(json.dumps(test_case, ensure_ascii=False, indent=2))
                    print("\n期望输出:")
                    print(json.dumps(expected_output, ensure_ascii=False, indent=2))
                    print("\n实际输出:")
                    print(json.dumps(output, ensure_ascii=False, indent=2))
                    return False
            except json.JSONDecodeError:
                print(f"\n❌ AI响应不是有效的JSON格式:")
                print(result.content)
                print("\n测试用例:")
                print("输入:")
                print(json.dumps(test_case, ensure_ascii=False, indent=2))
                print("\n期望输出:")
                print(json.dumps(expected_output, ensure_ascii=False, indent=2))
                return False
                
        except Exception as e:
            print(f"\n❌ 测试执行出错: {str(e)}")
            print("\n测试用例:")
            print("输入:")
            print(json.dumps(test_case, ensure_ascii=False, indent=2))
            print("\n期望输出:")
            print(json.dumps(expected_output, ensure_ascii=False, indent=2))
            return False

    def _compare_outputs(self, actual: Dict[str, Any], expected: Dict[str, Any]) -> bool:
        """比较实际输出和预期输出，只检查测试用例中存在的键值"""
        def compare_dicts(actual_dict: Dict[str, Any], expected_dict: Dict[str, Any], path: str = "") -> bool:
            for key, expected_value in expected_dict.items():
                if key not in actual_dict:
                    print(f"❌ 缺少字段 {path}{key}")
                    return False
                    
                actual_value = actual_dict[key]
                
                if isinstance(expected_value, dict):
                    if not isinstance(actual_value, dict):
                        print(f"❌ 字段类型不匹配 {path}{key}")
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
            
        # 只检查测试用例中存在的字段
        return compare_dicts(actual, expected)

    def _validate_output_format(self, output: Dict[str, Any]):
        """验证输出格式是否符合规范"""
        # 基本字段检查
        if not isinstance(output, dict):
            raise ValueError("Output must be a dictionary")
            
        # 检查process字段
        if "process" in output:
            process = output["process"]
            if not isinstance(process, dict):
                raise ValueError("Process must be a dictionary")
            if "action" not in process or "target" not in process:
                raise ValueError("Process must contain 'action' and 'target'")
                
        # 检查botstatus字段
        if "botstatus" in output and not isinstance(output["botstatus"], bool):
            raise ValueError("botstatus must be a boolean")
            
        # 检查对话格式
        if "dialogue" in output and not output["dialogue"].startswith("[机器人194号]"):
            raise ValueError("Dialogue must start with [机器人194号]")

def main():
    # 初始化测试运行器
    runner = PromptTestRunner()
    
    # 加载测试用例
    test_cases = runner.load_test_cases("f:/Projects/prompt_lab/prompt_engineering/bot194/01/prompt_test_cases.md")
    
    # 如果没有测试用例，直接返回
    if not test_cases:
        print("\n❌ 没有可执行的测试用例，程序退出")
        return
            
    # 运行测试
    results = []
    for test_case in test_cases:
        print(f"\n🔄 运行测试用例: {test_case.name}")
        result = runner.run_test(test_case.input_data, test_case.expected_output)
        results.append(result)
        
        if result:
            print("✅ 测试通过")
        else:
            print("❌ 测试失败")
    
    # 输出测试统计
    total = len(results)
    passed = sum(1 for r in results if r)
    print(f"\n📊 测试总结:")
    print(f"总数: {total}")
    print(f"通过: {passed}")
    print(f"失败: {total - passed}")
    if total > 0:
        print(f"通过率: {(passed/total)*100:.2f}%")

if __name__ == "__main__":
    main()
