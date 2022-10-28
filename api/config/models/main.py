from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from db.config.models.db import DBConfig, RedisConfig
from db.config.models.storage import StorageConfig


@dataclass
class Config:
    paths: Paths
    db: DBConfig
    storage: StorageConfig
    redis: RedisConfig

    @property
    def app_dir(self) -> Path:
        return self.paths.app_dir

    @property
    def config_path(self) -> Path:
        return self.paths.config_path

    @property
    def log_path(self) -> Path:
        return self.paths.log_path


@dataclass
class Paths:
    app_dir: Path

    @property
    def config_path(self) -> Path:
        return self.app_dir / "config"

    @property
    def logging_config_file(self) -> Path:
        return self.config_path / "logging.yml"

    @property
    def log_path(self) -> Path:
        return self.app_dir / "log"
