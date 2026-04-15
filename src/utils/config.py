"""Configuration management for Personal Knowledge System.

配置管理模块，负责加载 wiki 配置和获取 API 密钥。
"""

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


class Config:
    """Load and manage configuration from YAML and environment variables.

    从 YAML 文件和环境变量加载并管理配置信息。
    """

    def __init__(self, config_dir: str | None = None):
        """Initialize configuration.

        Args:
            config_dir: Directory containing config files. Defaults to project config/.
        """
        load_dotenv()

        if config_dir is None:
            project_root = Path(__file__).parent.parent.parent
            config_dir = project_root / "config"

        self.config_dir = Path(config_dir)
        self.wiki_config = self._load_yaml("wiki_config.yaml")
        self.user_profile = self._load_yaml("user_profile.yaml")

    def _load_yaml(self, filename: str) -> dict[str, Any]:
        """Load a YAML configuration file."""
        filepath = self.config_dir / filename
        if not filepath.exists():
            return {}
        with open(filepath, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    @property
    def bailian_api_key(self) -> str:
        """Get Bailian API key from environment."""
        api_key = os.getenv("BAILOU_API_KEY")
        if not api_key:
            raise ValueError(
                "BAILOU_API_KEY not set. Please copy .env.example to .env and configure it."
            )
        return api_key

    @property
    def models(self) -> dict[str, str]:
        """Get model routing configuration from wiki_config.yaml."""
        return self.wiki_config.get("model", {}).get("tasks", {})

    @property
    def default_model(self) -> str:
        """Get default model name."""
        return self.wiki_config.get("model", {}).get("default", "qwen3.6-plus")

    @property
    def paths(self) -> dict[str, str]:
        """Get path configuration from wiki_config."""
        return self.wiki_config.get("paths", {})

    def get_model_for_task(self, task_type: str) -> str:
        """Get the appropriate model for a given task type."""
        models = self.models
        return models.get(task_type, self.default_model)

    def get_context_budget(self, task_type: str = "query") -> int:
        """Get token budget for a task type."""
        return self.wiki_config.get("context", {}).get(f"{task_type}_budget", 100000)

    def get_compilation_config(self) -> dict:
        """Get compilation configuration."""
        return self.wiki_config.get("compilation", {})

    def get_health_check_config(self) -> dict:
        """Get health check configuration."""
        return self.wiki_config.get("health_check", {})


# Global config instance
_config: Config | None = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config
