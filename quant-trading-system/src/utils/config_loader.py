"""
配置加载器
"""
import yaml
from pathlib import Path
from typing import Dict, Any

def load_config(config_path: str = "config/settings.yaml") -> Dict[str, Any]:
    """加载YAML配置"""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 合并环境变量 .env（如果有）
    # 这里简化为直接返回
    return config
