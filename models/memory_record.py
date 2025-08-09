"""
メモリレコードデータモデル
時系列・メタデータ・重要度を含む包括的記録
"""

from datetime import datetime
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

class MemoryRecord(BaseModel):
    """
    会話記憶の基本単位
    セマンティック検索と時系列管理に最適化
    """
    
    id: UUID = Field(default_factory=uuid4)
    text: str = Field(..., min_length=1, description="会話テキスト本体")
    embedding: Optional[List[float]] = Field(None, description="埋め込みベクトル")
    
    # 時系列情報
    timestamp: datetime = Field(default_factory=datetime.now)
    session_id: str = Field(..., description="セッション識別子")
    
    # 会話メタデータ
    speaker: str = Field(..., description="発話者（user/assistant）")
    message_type: str = Field(default="chat", description="メッセージタイプ")
    
    # セマンティック情報
    topics: List[str] = Field(default_factory=list, description="抽出されたトピック")
    keywords: List[str] = Field(default_factory=list, description="キーワード")
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0, description="重要度スコア")
    
    # コンテキスト情報
    project_context: Optional[str] = Field(None, description="プロジェクト文脈")
    persona_context: Optional[str] = Field(None, description="人格設定")
    
    # 関連性情報
    related_memory_ids: List[UUID] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }

class ConversationSession(BaseModel):
    """
    会話セッション管理
    長期継続対話のための統合管理
    """
    
    session_id: str
    title: str
    description: Optional[str] = None
    
    # 時系列管理
    created_at: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)
    
    # セッション統計
    message_count: int = 0
    total_tokens: int = 0
    
    # プロジェクト情報
    project_tags: List[str] = Field(default_factory=list)
    persona_id: Optional[str] = Field(None, description="使用中の人格ID")
    
    # 継続性管理
    is_active: bool = True
    auto_resume: bool = True
    
class PersonaProfile(BaseModel):
    """
    AI人格プロファイル
    専門性・口調・思考傾向の定義
    """
    
    persona_id: str
    name: str
    description: str
    
    # 専門性定義
    expertise_domains: List[str] = Field(default_factory=list)
    knowledge_base: Dict[str, Any] = Field(default_factory=dict)
    
    # 言語スタイル
    communication_style: str = "formal"
    tone: str = "professional"
    language: str = "ja"
    
    # 思考パターン
    reasoning_approach: str = "systematic"
    creativity_level: float = Field(default=0.7, ge=0.0, le=1.0)
    
    # システムプロンプト
    system_prompt: str
    behavior_guidelines: List[str] = Field(default_factory=list)
    
    # 学習・成長設定
    learning_rate: float = Field(default=0.1, ge=0.0, le=1.0)
    memory_retention: float = Field(default=0.9, ge=0.0, le=1.0)