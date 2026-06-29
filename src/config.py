"""Đọc config/config.yaml thành các dataclass tiện dùng trong toàn pipeline.

Cách dùng:
    from src.config import load_config
    cfg = load_config()              # mặc định đọc config/config.yaml
    cfg.windowing.input_window       # 30
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import yaml

# Thư mục gốc của project (…/MachineLearning-HaUI)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"


@dataclass
class PathsConfig:
    raw_dir: str = "data/raw"
    processed_dir: str = "data/processed"
    merged_file: str = "data/processed/final_merged.csv"
    model_dir: str = "models"
    figures_dir: str = "reports/figures"


@dataclass
class DataConfig:
    exchanges: Dict[str, str] = field(default_factory=lambda: {"HOSE": "VNINDEX"})
    from_date: str = "2023-01-01"
    fields: List[str] = field(
        default_factory=lambda: ["open", "high", "low", "close", "volume",
                                 "bu", "sd", "fn", "fs", "fb"]
    )
    adjusted: bool = True
    by: str = "1d"
    max_tickers: Optional[int] = None


@dataclass
class FeaturesConfig:
    cols: List[str] = field(default_factory=lambda: ["open", "high", "low", "close", "volume"])
    target_col: str = "close"


@dataclass
class WindowingConfig:
    input_window: int = 30
    output_window: int = 1


@dataclass
class SplitConfig:
    train_ratio: float = 0.70
    val_ratio: float = 0.15
    test_ratio: float = 0.15


@dataclass
class ModelConfig:
    emb_dim: int = 16
    hidden_dim: int = 128
    n_heads: int = 8
    n_layers: int = 3
    dropout: float = 0.1


@dataclass
class TrainConfig:
    batch_size: int = 64
    num_epochs: int = 150
    lr: float = 1e-4
    weight_decay: float = 1e-4
    grad_clip: float = 1.0
    seed: int = 42
    use_cuda: bool = True


@dataclass
class SelectConfig:
    top_n: int = 10


@dataclass
class Config:
    paths: PathsConfig = field(default_factory=PathsConfig)
    data: DataConfig = field(default_factory=DataConfig)
    features: FeaturesConfig = field(default_factory=FeaturesConfig)
    windowing: WindowingConfig = field(default_factory=WindowingConfig)
    split: SplitConfig = field(default_factory=SplitConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    train: TrainConfig = field(default_factory=TrainConfig)
    select: SelectConfig = field(default_factory=SelectConfig)

    # ---- Helpers trả về đường dẫn tuyệt đối ----
    def abs_path(self, rel: str) -> str:
        """Chuyển path tương đối (so với gốc project) thành tuyệt đối."""
        p = Path(rel)
        return str(p if p.is_absolute() else PROJECT_ROOT / p)


def _section(cls, data: dict):
    """Khởi tạo dataclass `cls` chỉ với các khoá có trong định nghĩa của nó."""
    if not data:
        return cls()
    valid = {f.name for f in cls.__dataclass_fields__.values()}
    return cls(**{k: v for k, v in data.items() if k in valid})


def load_config(path: str | os.PathLike | None = None) -> Config:
    """Đọc YAML và dựng Config. Thiếu khoá nào dùng default của khoá đó."""
    cfg_path = Path(path) if path else DEFAULT_CONFIG_PATH
    raw: dict = {}
    if cfg_path.exists():
        with open(cfg_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
    return Config(
        paths=_section(PathsConfig, raw.get("paths", {})),
        data=_section(DataConfig, raw.get("data", {})),
        features=_section(FeaturesConfig, raw.get("features", {})),
        windowing=_section(WindowingConfig, raw.get("windowing", {})),
        split=_section(SplitConfig, raw.get("split", {})),
        model=_section(ModelConfig, raw.get("model", {})),
        train=_section(TrainConfig, raw.get("train", {})),
        select=_section(SelectConfig, raw.get("select", {})),
    )


if __name__ == "__main__":
    import json
    from dataclasses import asdict

    cfg = load_config()
    print(json.dumps(asdict(cfg), indent=2, ensure_ascii=False))
