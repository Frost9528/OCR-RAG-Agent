"""
Application Configuration
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List
import os
from pathlib import Path

class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )

    # 阿里云百炼配置
    dashscope_api_key: str = ""
    qwen_model_name: str = "qwen-max"
    temperature: float = 0.7
    top_p: float = 0.8
    max_tokens: int = 2000

    # 向量数据库配置
    chroma_persist_dir: str = "./data/chroma_db"
    embedding_model: str = "text-embedding-v3"  # Qwen embedding 模型

    # RAG 配置
    chunk_size: int = 512
    chunk_overlap: int = 50
    retrieval_top_k: int = 5

    # OCR 模式: cloud 或 local
    ocr_mode: str = "cloud"

    # 飞桨云端 OCR API（cloud 模式）
    paddleocr_api_token: str = ""
    paddleocr_api_url: str = "https://t7leseh0b8e85b24.aistudio-app.com/layout-parsing"

    # PaddleOCR 本地模型路径（local 模式）
    paddleocr_vl_model_dir: str = "/home/MuyuWorkSpace/02_OcrRag/PaddleOCR-VL-0.9B"
    layout_detection_model_dir: str = "/home/MuyuWorkSpace/02_OcrRag/PP-DocLayoutV2"

    # 文件上传配置
    upload_dir: str = "./uploads"
    max_upload_size: int = 50  # MB
    allowed_extensions: List[str] = ["pdf", "png", "jpg", "jpeg"]

    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8100
    server_base_url: str = "http://localhost:8100"  # 用于生成图片等资源的对外 URL
    debug: bool = True
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:5173"]

    # 日志配置
    log_level: str = "INFO"

    @field_validator('allowed_extensions', 'cors_origins', mode='before')
    @classmethod
    def parse_list_from_str(cls, v):
        """将逗号分隔的字符串转换为列表"""
        if isinstance(v, str):
            return [item.strip() for item in v.split(',') if item.strip()]
        return v

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 确保必要的目录存在
        Path(self.upload_dir).mkdir(parents=True, exist_ok=True)
        Path(self.chroma_persist_dir).mkdir(parents=True, exist_ok=True)


# 全局设置实例
settings = Settings()
