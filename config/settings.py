"""
Dr. Kagami式 設定管理システム
本格運用レベルの環境設定を実現
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """
    システム設定クラス
    環境変数の自動読み込みと型安全性を保証
    """
    
    # Gemini API設定
    gemini_api_key: str
    gemini_model: str = "gemini-2.0-flash-exp"
    
    # ベクタDB設定
    chroma_db_path: Path = Path("./chroma_db")
    collection_name: str = "gemini_memory"
    
    # 埋め込みモデル設定
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    
    # チャンク処理設定
    max_chunk_size: int = 512
    overlap_size: int = 64
    
    # 検索設定
    top_k_results: int = 10
    similarity_threshold: float = 0.7
    
    # キャッシュ設定
    context_cache_ttl: int = 3600
    max_cache_size: int = 1000
    
    # ログ設定
    log_level: str = "INFO"
    log_file: Path = Path("./logs/gemini_memory.log")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# グローバル設定インスタンス
settings = Settings()