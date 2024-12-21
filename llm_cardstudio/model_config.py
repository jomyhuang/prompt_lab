from dataclasses import dataclass
from typing import List, Optional
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_ollama import ChatOllama

# 确保加载环境变量
load_dotenv()

@dataclass
class ModelVendorConfig:
    name: str                    # 模型商名称
    models: List[str]           # 该商家提供的模型列表
    baseline_models: List[str]  # 该商家的基线模型列表
    api_key_env: str           # 环境变量中API KEY的名称
    base_url: str              # API基础URL
    model_class: Optional[str] = None  # 模型基类名称，可选

# 卡牌测试使用的模型配置
CARD_TEST_MODELS = {
    "SMALLAI": ModelVendorConfig(
        name="SmallAI",
        models=["gemini-2.0-flash-exp", "claude-3-5-sonnet-20241022"],
        baseline_models=["gemini-2.0-flash-exp"],
        api_key_env="SMALLAI_API_KEY",
        base_url="https://ai98.vip/v1",
        model_class="ChatOpenAI"
    ),
    "GoogleAPI": ModelVendorConfig(
        name="GoogleAPI",
        models=["gemini-1.5-pro", "gemini-2.0-flash-exp"],
        baseline_models=["gemini-2.0-flash-exp"],
        api_key_env="GOOGLE_API_KEY",
        base_url=None,
        model_class="ChatGoogleGenerativeAI"
    ),
    "LLMStudio": ModelVendorConfig(
        name="LLMStudio",
        models=["qwen2.5-coder-32b-instruct"],
        baseline_models=["qwen2.5-coder-32b-instruct"],
        api_key_env="API_KEY",
        base_url="http://localhost:1234/v1",
        model_class="ChatOpenAI"
    )
}

# 默认的模型配置
DEFAULT_VENDOR = "SMALLAI"
DEFAULT_MODEL = "gemini-2.0-flash-exp"

def get_available_models(use_default: bool = True):
    """获取可用的模型配置
    
    Args:
        use_default: 如果为True，在没有可用配置时返回默认配置
    """
    available_vendors = {}
    
    for vendor_name, config in CARD_TEST_MODELS.items():
        # 如果不需要API密钥（本地模型）或者有API密钥
        if config.api_key_env is None:
            available_vendors[vendor_name] = config
            print(f"添加无需API密钥的供应商: {vendor_name}")
        else:
            api_key = os.getenv(config.api_key_env)
            if api_key:
                available_vendors[vendor_name] = config
                print(f"添加已配置API密钥的供应商: {vendor_name}")
            else:
                print(f"跳过未配置API密钥的供应商: {vendor_name}")
    
    # 如果没有可用配置且use_default为True，返回默认配置
    if not available_vendors and use_default and DEFAULT_VENDOR in CARD_TEST_MODELS:
        print(f"警告: 没有可用的模型配置，使用默认配置 {DEFAULT_VENDOR}/{DEFAULT_MODEL}")
        if os.getenv(CARD_TEST_MODELS[DEFAULT_VENDOR].api_key_env):
            return {DEFAULT_VENDOR: CARD_TEST_MODELS[DEFAULT_VENDOR]}
        else:
            print(f"错误: 默认供应商 {DEFAULT_VENDOR} 的API密钥未配置")
            return {}
    
    return available_vendors

def get_default_model():
    """获取默认的模型配置"""
    if DEFAULT_VENDOR not in CARD_TEST_MODELS:
        raise ValueError(f"默认供应商 {DEFAULT_VENDOR} 不存在")
    
    config = CARD_TEST_MODELS[DEFAULT_VENDOR]
    api_key = os.getenv(config.api_key_env)
    if not api_key:
        raise ValueError(f"默认供应商 {DEFAULT_VENDOR} 的API密钥未配置")
    
    if DEFAULT_MODEL not in config.models:
        raise ValueError(f"默认模型 {DEFAULT_MODEL} 不在供应商 {DEFAULT_VENDOR} 的模型列表中")
    
    return DEFAULT_VENDOR, DEFAULT_MODEL

def create_model_instance(vendor_name: str, model_name: str):
    """创建模型实例"""
    config = CARD_TEST_MODELS.get(vendor_name)
    if not config:
        raise ValueError(f"未找到供应商配置: {vendor_name}")
        
    if model_name not in config.models:
        raise ValueError(f"模型 {model_name} 不在供应商 {vendor_name} 的模型列表中")
    
    api_key = os.getenv(config.api_key_env)
    if not api_key:
        raise ValueError(f"供应商 {vendor_name} 的API密钥未配置")
    
    print(f"正在创建模型实例: {vendor_name}/{model_name}")
    print(f"使用API基础URL: {config.base_url}")
    
    # 根据模型类型创建实例
    if config.model_class == "ChatOpenAI":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model_name,
            openai_api_key=api_key,
            openai_api_base=config.base_url,
            temperature=0,
            streaming=True
        )
    elif config.model_class == "ChatGoogleGenerativeAI":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0,
            streaming=True
        )
    else:
        raise ValueError(f"不支持的模型类型: {config.model_class}")
