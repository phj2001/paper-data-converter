"""
大模型配置管理模块
支持多种主流大模型的统一配置管理
"""

import os
import json
from typing import Optional, Dict, List, Any
from pathlib import Path
from dataclasses import dataclass, asdict


# ==================== 主流大模型配置 ====================

# 预定义的模型提供商配置
LLM_PROVIDERS = {
    "openai": {
        "name": "OpenAI",
        "base_url": "https://api.openai.com/v1/chat/completions",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        "api_key_env": "OPENAI_API_KEY",
        "supports_vision": True
    },
    "anthropic": {
        "name": "Anthropic",
        "base_url": "https://api.anthropic.com/v1/messages",
        "models": ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"],
        "api_key_env": "ANTHROPIC_API_KEY",
        "supports_vision": True
    },
    "doubao": {
        "name": "豆包(字节跳动)",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
        "models": [],  # 使用自定义endpoint_id
        "api_key_env": "ARK_API_KEY",
        "supports_vision": True,
        "use_endpoint_id": True
    },
    "qwen": {
        "name": "通义千问(阿里)",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        "models": ["qwen-vl-max", "qwen-vl-plus", "qwen-vl-v1"],
        "api_key_env": "DASHSCOPE_API_KEY",
        "supports_vision": True
    },
    "zhipu": {
        "name": "智谱AI",
        "base_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "models": ["glm-4v", "glm-4v-plus", "glm-4"],
        "api_key_env": "ZHIPU_API_KEY",
        "supports_vision": True
    },
    "baidu": {
        "name": "百度文心",
        "base_url": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat",
        "models": [],  # 百度使用不同的端点
        "api_key_env": "BAIDU_API_KEY",
        "supports_vision": False
    },
    "tencent": {
        "name": "腾讯混元",
        "base_url": "https://hunyuan.tencentcloudapi.com/v1/chat/completions",
        "models": ["hunyuan-vision", "hunyuan-pro", "hunyuan-standard"],
        "api_key_env": "TENCENT_API_KEY",
        "supports_vision": True
    },
    "deepseek": {
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1/chat/completions",
        "models": ["deepseek-chat", "deepseek-coder"],
        "api_key_env": "DEEPSEEK_API_KEY",
        "supports_vision": False
    },
    "moonshot": {
        "name": "Moonshot(Kimi)",
        "base_url": "https://api.moonshot.cn/v1/chat/completions",
        "models": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
        "api_key_env": "MOONSHOT_API_KEY",
        "supports_vision": False
    },
    "custom": {
        "name": "自定义",
        "base_url": "",
        "models": [],
        "api_key_env": "",
        "supports_vision": True
    }
}


@dataclass
class LLMConfig:
    """大模型配置数据类"""
    provider: str  # 提供商ID (openai, anthropic, doubao等)
    model: str  # 模型名称或endpoint_id
    api_key: str  # API密钥
    base_url: Optional[str] = None  # 自定义API地址（用于自定义提供商）
    temperature: float = 0.01  # 温度参数
    max_tokens: int = 4096  # 最大token数
    timeout: int = 180  # 请求超时时间（秒）

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LLMConfig':
        """从字典创建实例"""
        return cls(**data)

    def get_api_url(self) -> str:
        """获取实际的API地址"""
        if self.base_url:
            return self.base_url
        provider_info = LLM_PROVIDERS.get(self.provider, {})
        return provider_info.get("base_url", "")

    def validate(self) -> tuple[bool, str]:
        """验证配置是否有效"""
        if not self.provider:
            return False, "未选择提供商"

        if self.provider not in LLM_PROVIDERS:
            return False, f"不支持的提供商: {self.provider}"

        if not self.api_key:
            return False, "API密钥不能为空"

        if not self.model:
            return False, "模型名称不能为空"

        if not self.get_api_url():
            return False, "API地址不能为空"

        provider_info = LLM_PROVIDERS.get(self.provider, {})
        if not provider_info.get("supports_vision", False):
            return False, f"{provider_info.get('name', self.provider)} 暂不支持视觉能力"

        return True, ""


class LLMConfigManager:
    """大模型配置管理器"""

    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_file: 配置文件路径，默认为 backend/config.json
        """
        if config_file is None:
            # 默认配置文件路径 - 使用项目根目录的config.json
            self.config_file = Path(__file__).parent.parent / "config.json"
        else:
            self.config_file = Path(config_file)

        self.config: Optional[LLMConfig] = None
        self.load_config()

    def load_config(self) -> LLMConfig:
        """
        从配置文件加载配置

        Returns:
            LLMConfig实例
        """
        # 如果配置文件存在，从文件加载
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.config = LLMConfig.from_dict(data)
                    return self.config
            except Exception as e:
                print(f"加载配置文件失败: {e}")

        # 否则使用环境变量或默认配置
        self.config = self._get_default_config()
        return self.config

    def save_config(self, config: LLMConfig) -> bool:
        """
        保存配置到文件

        Args:
            config: LLMConfig实例

        Returns:
            是否保存成功
        """
        try:
            # 确保目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            # 保存配置
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, ensure_ascii=False, indent=2)

            # 更新当前配置（如果是全局单例，会自动更新全局状态）
            self.config = config

            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False

    def get_config(self) -> LLMConfig:
        """获取当前配置"""
        if self.config is None:
            self.config = self.load_config()
        return self.config

    def _get_default_config(self) -> LLMConfig:
        """
        获取默认配置（从环境变量或硬编码默认值）

        Returns:
            LLMConfig实例
        """
        # 默认使用豆包（与原有代码兼容）
        provider = os.environ.get("LLM_PROVIDER", "doubao")

        # 根据提供商获取对应的API密钥
        api_key = ""
        if provider == "doubao":
            api_key = os.environ.get("ARK_API_KEY", "f56d7c74-5e13-4a71-8973-d4cebd7aece1")
            model = os.environ.get("ARK_ENDPOINT_ID", "ep-20260104183112-7c7dt")
        elif provider == "openai":
            api_key = os.environ.get("OPENAI_API_KEY", "")
            model = os.environ.get("OPENAI_MODEL", "gpt-4o")
        elif provider == "anthropic":
            api_key = os.environ.get("ANTHROPIC_API_KEY", "")
            model = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
        elif provider == "qwen":
            api_key = os.environ.get("DASHSCOPE_API_KEY", "")
            model = os.environ.get("QWEN_MODEL", "qwen-vl-max")
        elif provider == "zhipu":
            api_key = os.environ.get("ZHIPU_API_KEY", "")
            model = os.environ.get("ZHIPU_MODEL", "glm-4v")
        else:
            # 自定义提供商
            api_key = os.environ.get("CUSTOM_API_KEY", "")
            model = os.environ.get("CUSTOM_MODEL", "")

        return LLMConfig(
            provider=provider,
            model=model,
            api_key=api_key,
            temperature=0.01,
            max_tokens=4096,
            timeout=180
        )

    @staticmethod
    def get_providers() -> Dict[str, Dict[str, Any]]:
        """获取所有支持的提供商列表"""
        return LLM_PROVIDERS

    @staticmethod
    def get_provider_info(provider_id: str) -> Optional[Dict[str, Any]]:
        """获取指定提供商的信息"""
        return LLM_PROVIDERS.get(provider_id)

    @staticmethod
    def list_providers() -> List[Dict[str, Any]]:
        """
        列出所有支持的提供商（用于前端展示）

        Returns:
            提供商信息列表
        """
        result = []
        for provider_id, info in LLM_PROVIDERS.items():
            result.append({
                "id": provider_id,
                "name": info.get("name", provider_id),
                "models": info.get("models", []),
                "supports_vision": info.get("supports_vision", False),
                "use_endpoint_id": info.get("use_endpoint_id", False)
            })
        return result


# ==================== 全局配置管理器实例 ====================

# 全局配置管理器
_config_manager: Optional[LLMConfigManager] = None


def get_config_manager() -> LLMConfigManager:
    """获取全局配置管理器实例（单例模式）"""
    global _config_manager
    if _config_manager is None:
        _config_manager = LLMConfigManager()
    return _config_manager


def get_config() -> LLMConfig:
    """快捷方法：获取当前配置"""
    return get_config_manager().get_config()


def update_config(config: LLMConfig) -> bool:
    """快捷方法：更新配置"""
    return get_config_manager().save_config(config)
