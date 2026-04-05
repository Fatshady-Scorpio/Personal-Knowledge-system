"""Configuration management for Personal Knowledge Base."""

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


class Config:
    """Load and manage configuration from YAML and environment variables."""

    def __init__(self, config_dir: str | None = None):
        """Initialize configuration.

        Args:
            config_dir: Directory containing config files. Defaults to project config/.
        """
        # Load environment variables
        load_dotenv()

        # Determine config directory
        if config_dir is None:
            project_root = Path(__file__).parent.parent.parent
            config_dir = project_root / "config"

        self.config_dir = Path(config_dir)
        self.settings = self._load_yaml("settings.yaml")
        self.sources = self._load_yaml("sources.yaml")

        # Expand environment variables in settings
        self.settings = self._expand_env(self.settings)

    def _load_yaml(self, filename: str) -> dict[str, Any]:
        """Load a YAML configuration file."""
        filepath = self.config_dir / filename
        with open(filepath, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _expand_env(self, config: dict[str, Any]) -> dict[str, Any]:
        """Expand environment variables in configuration values."""
        result = {}
        for key, value in config.items():
            if isinstance(value, dict):
                result[key] = self._expand_env(value)
            elif isinstance(value, str):
                # Expand ${VAR} syntax
                result[key] = os.path.expandvars(value)
            else:
                result[key] = value
        return result

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
        """Get model configuration."""
        return self.settings.get("bailian", {}).get("models", {})

    @property
    def paths(self) -> dict[str, str]:
        """Get path configuration."""
        return self.settings.get("paths", {})

    def get_model_for_task(self, task_type: str) -> str:
        """Get the appropriate model for a given task type."""
        models = self.models
        return models.get(task_type, models.get("text_summary", "qwen-max"))

    def get_knowledge_path(self, category: str) -> Path:
        """Get the path for a knowledge base category."""
        root = self.paths.get("knowledge_root", "./knowledge")
        category_path = self.paths.get(category, category)
        return Path(root) / category_path


# Global config instance
_config: Config | None = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config
