"""
Dr. Kagami式 メモリ管理システム
ChromaDBベースのセマンティック記憶基盤
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
import chromadb
from chromadb.config import Settings as ChromaSettings
import uuid
import logging

from config.settings import settings
from models.memory_record import MemoryRecord, ConversationSession
from core.embedding_service import embedding_service

logger = logging.getLogger(__name__)

class MemoryManager:
    """
    セマンティックメモリの中央管理システム
    ChromaDBを使用した高性能ベクトル検索
    """
    
    def __init__(self):
        self.client = None
        self.collection = None
        self.sessions: Dict[str, ConversationSession] = {}
        self.session_file = settings.chroma_db_path.parent / "data" / "cache" / "sessions.json"
        
    async def initialize(self) -> None:
        """メモリシステムの初期化"""
        try:
            # ChromaDB設定
            chroma_settings = ChromaSettings(
                persist_directory=str(settings.chroma_db_path),
                anonymized_telemetry=False
            )
            
            self.client = chromadb.PersistentClient(
                path=str(settings.chroma_db_path),
                settings=chroma_settings
            )
            
            # コレクション取得または作成
            try:
                self.collection = self.client.get_or_create_collection(
                    name=settings.collection_name
                )
                logger.info(f"Existing collection loaded: {settings.collection_name}")
            except ValueError:
                self.collection = self.client.create_collection(
                    name=settings.collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info(f"New collection created: {settings.collection_name}")
            
            # 埋め込みサービス初期化
            await embedding_service.initialize()
            
            # セッション復元
            await self._restore_sessions()
            
            logger.info("Memory system initialized successfully")
            
        except Exception as e:
            logger.error(f"Memory system initialization failed: {e}")
            raise
    
    async def store_memory(self, memory: MemoryRecord) -> str:
        """
        記憶の保存
        
        Args:
            memory: 保存対象の記憶レコード
            
        Returns:
            str: 保存されたメモリのID
        """
        try:
            # 埋め込み生成
            if memory.embedding is None:
                memory.embedding = await embedding_service.embed_text(memory.text)
            
            # ChromaDBに保存
            memory_id = str(memory.id)
            
            self.collection.add(
                embeddings=[memory.embedding],
                documents=[memory.text],
                metadatas=[{
                    "session_id": memory.session_id,
                    "speaker": memory.speaker,
                    "timestamp": memory.timestamp.isoformat(),
                    "importance_score": memory.importance_score,
                    "topics": ",".join(memory.topics),
                    "keywords": ",".join(memory.keywords),
                    "project_context": memory.project_context or "",
                    "persona_context": memory.persona_context or ""
                }],
                ids=[memory_id]
            )
            
            # セッション情報更新
            await self._update_session_stats(memory.session_id)
            
            logger.info(f"Memory stored successfully: {memory_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            raise
    
    async def retrieve_memories(
        self,
        query: str,
        session_id: Optional[str] = None,
        top_k: int = None,
        similarity_threshold: float = None,
        time_range: Optional[Tuple[datetime, datetime]] = None,
        topics: Optional[List[str]] = None
    ) -> List[MemoryRecord]:
        """
        セマンティック記憶検索
        
        Args:
            query: 検索クエリ
            session_id: セッション限定検索
            top_k: 取得件数上限
            similarity_threshold: 類似度閾値
            time_range: 時間範囲フィルタ
            topics: トピックフィルタ
            
        Returns:
            List[MemoryRecord]: 関連記憶リスト
        """
        try:
            # パラメータデフォルト値設定
            top_k = top_k or settings.top_k_results
            similarity_threshold = similarity_threshold or settings.similarity_threshold
            
            # クエリ埋め込み生成
            query_embedding = await embedding_service.embed_text(query)
            
            # メタデータフィルタ構築
            where_conditions = {}
            if session_id:
                where_conditions["session_id"] = session_id
            
            if time_range:
                # 時間範囲フィルタ（ISO形式文字列比較）
                start_time, end_time = time_range
                where_conditions["timestamp"] = {
                    "$gte": start_time.isoformat(),
                    "$lte": end_time.isoformat()
                }
            
            # ChromaDB検索実行
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_conditions if where_conditions else None
            )
            
            # 結果をMemoryRecordに変換
            memories = []
            for i, (doc, metadata, distance) in enumerate(zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            )):
                # 類似度閾値チェック（距離は小さいほど類似）
                similarity = 1 - distance
                if similarity < similarity_threshold:
                    continue
                
                memory = MemoryRecord(
                    id=uuid.UUID(results["ids"][0][i]),
                    text=doc,
                    session_id=metadata["session_id"],
                    speaker=metadata["speaker"],
                    timestamp=datetime.fromisoformat(metadata["timestamp"]),
                    importance_score=metadata["importance_score"],
                    topics=metadata["topics"].split(",") if metadata["topics"] else [],
                    keywords=metadata["keywords"].split(",") if metadata["keywords"] else [],
                    project_context=metadata.get("project_context"),
                    persona_context=metadata.get("persona_context")
                )
                memories.append(memory)
            
            logger.info(f"Retrieved {len(memories)} memories for query: {query[:50]}...")
            return memories
            
        except Exception as e:
            logger.error(f"Memory retrieval failed: {e}")
            raise
    
    async def create_session(
        self,
        session_id: str,
        title: str,
        description: Optional[str] = None,
        persona_id: Optional[str] = None
    ) -> ConversationSession:
        """新しい会話セッション作成"""
        session = ConversationSession(
            session_id=session_id,
            title=title,
            description=description,
            persona_id=persona_id
        )
        
        self.sessions[session_id] = session
        await self._save_sessions()
        logger.info(f"New session created and saved: {session_id}")
        return session
    
    async def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """セッション情報取得"""
        return self.sessions.get(session_id)
    
    async def list_sessions(self, active_only: bool = True) -> List[ConversationSession]:
        """セッションリスト取得"""
        sessions = list(self.sessions.values())
        if active_only:
            sessions = [s for s in sessions if s.is_active]
        
        # 最終活動時間でソート
        sessions.sort(key=lambda x: x.last_activity, reverse=True)
        return sessions
    
    async def cleanup_old_memories(self, days_to_keep: int = 90) -> int:
        """
        古いメモリの自動クリーンアップ
        
        Args:
            days_to_keep: 保持日数
            
        Returns:
            int: 削除されたメモリ数
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # 古いメモリを検索
            results = self.collection.query(
                query_embeddings=[[0.0] * settings.embedding_dimension],  # ダミークエリ
                n_results=1000,  # 大きな値を設定
                where={"timestamp": {"$lt": cutoff_date.isoformat()}}
            )
            
            if results["ids"]:
                # 低重要度メモリのみ削除
                ids_to_delete = []
                for i, metadata in enumerate(results["metadatas"][0]):
                    if metadata["importance_score"] < 0.3:  # 重要度閾値
                        ids_to_delete.append(results["ids"][0][i])
                
                if ids_to_delete:
                    self.collection.delete(ids=ids_to_delete)
                    logger.info(f"Cleaned up {len(ids_to_delete)} old memories")
                    return len(ids_to_delete)
            
            return 0
            
        except Exception as e:
            logger.error(f"Memory cleanup failed: {e}")
            return 0
    
    async def _update_session_stats(self, session_id: str) -> None:
        """セッション統計情報更新"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.message_count += 1
            session.last_activity = datetime.now()
            await self._save_sessions()

    async def _save_sessions(self) -> None:
        """セッション情報をJSONファイルに永続化"""
        try:
            sessions_to_save = {
                session_id: session.dict()
                for session_id, session in self.sessions.items()
            }
            self.session_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.session_file, "w", encoding="utf-8") as f:
                json.dump(sessions_to_save, f, ensure_ascii=False, indent=4, default=str)
            logger.info(f"Successfully saved {len(self.sessions)} sessions.")
        except Exception as e:
            logger.error(f"Failed to save sessions: {e}")

    async def _restore_sessions(self) -> None:
        """保存されたセッション情報の復元"""
        try:
            if self.session_file.exists():
                with open(self.session_file, "r", encoding="utf-8") as f:
                    sessions_data = json.load(f)
                    self.sessions = {
                        session_id: ConversationSession(**data)
                        for session_id, data in sessions_data.items()
                    }
                logger.info(f"Restored {len(self.sessions)} sessions from file.")
            else:
                logger.info("Session file not found. Starting with empty sessions.")
        except Exception as e:
            logger.error(f"Session restoration failed: {e}")

# グローバルインスタンス
memory_manager = MemoryManager()