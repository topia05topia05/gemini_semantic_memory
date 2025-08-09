"""
Dr. Kagami式 埋め込みサービス
高性能セマンティックベクトル生成システム
"""

import asyncio
from typing import List, Optional, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    埋め込み生成の統合サービス
    複数のモデルに対応し、効率的なベクトル化を実現
    """
    
    def __init__(self):
        self.model = None
        self.model_type = "sentence_transformers"  # or "gemini"
        self.cache = {}  # 簡易キャッシュ
        
    async def initialize(self) -> None:
        """
        埋め込みモデルの初期化
        非同期処理で起動時間を最適化
        """
        try:
            if self.model_type == "sentence_transformers":
                self.model = SentenceTransformer(settings.embedding_model)
                logger.info(f"SentenceTransformer loaded: {settings.embedding_model}")
            elif self.model_type == "gemini":
                genai.configure(api_key=settings.gemini_api_key)
                logger.info("Gemini Embedding API configured")
            else:
                raise ValueError(f"Unsupported embedding model type: {self.model_type}")
                
        except Exception as e:
            logger.error(f"Failed to initialize embedding service: {e}")
            raise
    
    async def embed_text(self, text: str) -> List[float]:
        """
        テキストから埋め込みベクトル生成
        
        Args:
            text: 埋め込み対象テキスト
            
        Returns:
            List[float]: 正規化済み埋め込みベクトル
        """
        if not text.strip():
            raise ValueError("Empty text cannot be embedded")
            
        # キャッシュチェック
        cache_key = hash(text)
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            if self.model_type == "sentence_transformers":
                embedding = await self._embed_with_sentence_transformers(text)
            elif self.model_type == "gemini":
                embedding = await self._embed_with_gemini(text)
            else:
                raise ValueError(f"Unknown model type: {self.model_type}")
            
            # L2正規化
            normalized_embedding = self._normalize_vector(embedding)
            
            # キャッシュ保存（メモリ制限あり）
            if len(self.cache) < settings.max_cache_size:
                self.cache[cache_key] = normalized_embedding
            
            return normalized_embedding
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        バッチ埋め込み生成
        大量テキストの効率的処理
        
        Args:
            texts: テキストリスト
            
        Returns:
            List[List[float]]: 埋め込みベクトルリスト
        """
        if not texts:
            return []
        
        # 空文字列フィルタリング
        valid_texts = [t for t in texts if t.strip()]
        
        try:
            if self.model_type == "sentence_transformers":
                embeddings = self.model.encode(valid_texts, convert_to_tensor=False)
                return [self._normalize_vector(emb.tolist()) for emb in embeddings]
            elif self.model_type == "gemini":
                # Gemini APIのレート制限を考慮した逐次処理
                embeddings = []
                for text in valid_texts:
                    emb = await self._embed_with_gemini(text)
                    embeddings.append(self._normalize_vector(emb))
                    await asyncio.sleep(0.1)  # レート制限対策
                return embeddings
            else:
                raise ValueError(f"Unknown model type: {self.model_type}")
                
        except Exception as e:
            logger.error(f"Batch embedding failed: {e}")
            raise
    
    async def _embed_with_sentence_transformers(self, text: str) -> List[float]:
        """SentenceTransformersによる埋め込み生成"""
        if self.model is None:
            await self.initialize()
        
        embedding = self.model.encode([text], convert_to_tensor=False)[0]
        return embedding.tolist()
    
    async def _embed_with_gemini(self, text: str) -> List[float]:
        """Gemini APIによる埋め込み生成"""
        try:
            result = genai.embed_content(
                model="models/embedding-001",
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Gemini embedding API error: {e}")
            raise
    
    def _normalize_vector(self, vector: List[float]) -> List[float]:
        """
        ベクトル正規化（L2ノルム）
        コサイン類似度計算の前処理
        """
        np_vector = np.array(vector)
        norm = np.linalg.norm(np_vector)
        if norm == 0:
            return vector
        return (np_vector / norm).tolist()
    
    def similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        コサイン類似度計算
        正規化済みベクトル前提で内積計算
        """
        return float(np.dot(vec1, vec2))

# グローバルインスタンス
embedding_service = EmbeddingService()