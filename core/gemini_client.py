"""
Gemini API統合クライアント
コンテキストキャッシュ対応の高性能会話システム
"""

import asyncio
from typing import List, Dict, Optional, Any
import google.generativeai as genai
from google.generativeai import caching
from datetime import datetime, timedelta
import logging

from config.settings import settings
from models.memory_record import MemoryRecord, PersonaProfile

logger = logging.getLogger(__name__)

class GeminiClient:
    """
    Gemini API統合クライアント
    コンテキストキャッシュとメモリ統合機能
    """
    
    def __init__(self):
        self.model = None
        self.context_caches: Dict[str, Any] = {}
        
    async def initialize(self) -> None:
        """Gemini APIクライアント初期化"""
        try:
            genai.configure(api_key=settings.gemini_api_key)
            self.model = genai.GenerativeModel(
                model_name=settings.gemini_model,
                system_instruction="あなたは高度なAIアシスタントです。"
            )
            logger.info(f"Gemini client initialized: {settings.gemini_model}")
        except Exception as e:
            logger.error(f"Gemini client initialization failed: {e}")
            raise
    
    async def generate_response(
        self,
        user_input: str,
        retrieved_memories: List[MemoryRecord],
        persona: Optional[PersonaProfile] = None,
        session_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        記憶とペルソナを活用した応答生成
        
        Args:
            user_input: ユーザー入力
            retrieved_memories: 検索された関連記憶
            persona: 人格プロファイル
            session_context: セッション文脈
            
        Returns:
            str: 生成された応答
        """
        try:
            # コンテキスト構築
            context = await self._build_context(
                user_input, retrieved_memories, persona, session_context
            )
            
            # Gemini APIコール
            response = await self.model.generate_content_async(
                context,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_output_tokens": 2048,
                }
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            raise
    
    async def _build_context(
        self,
        user_input: str,
        memories: List[MemoryRecord],
        persona: Optional[PersonaProfile],
        session_context: Optional[Dict[str, Any]]
    ) -> str:
        """会話コンテキストの構築"""
        
        context_parts = []
        
        # ペルソナ設定
        if persona:
            context_parts.append(f"# ペルソナ設定\n{persona.system_prompt}\n")
            if persona.behavior_guidelines:
                context_parts.append("## 行動指針")
                for guideline in persona.behavior_guidelines:
                    context_parts.append(f"- {guideline}")
                context_parts.append("")
        
        # 関連記憶の統合
        if memories:
            context_parts.append("# 関連する過去の会話")
            for i, memory in enumerate(memories[:5], 1):  # 上位5件
                timestamp = memory.timestamp.strftime("%Y-%m-%d %H:%M")
                context_parts.append(f"## 記憶{i} ({timestamp})")
                context_parts.append(f"**{memory.speaker}**: {memory.text[:200]}...")
                if memory.topics:
                    context_parts.append(f"**トピック**: {', '.join(memory.topics)}")
                context_parts.append("")
        
        # ユーザー入力
        context_parts.append("# 現在の会話")
        context_parts.append(f"**user**: {user_input}")
        context_parts.append("\n**assistant**:")
        
        return "\n".join(context_parts)

# グローバルインスタンス
gemini_client = GeminiClient()
