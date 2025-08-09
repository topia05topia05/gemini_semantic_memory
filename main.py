
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uuid

from core.memory_manager import memory_manager, ConversationSession
from core.gemini_client import gemini_client
from models.memory_record import MemoryRecord

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Dr. Aria's Semantic Memory API",
    description="A sophisticated API to interact with a persistent, semantic memory system.",
    version="2.0.0"  # Version up!
)

# --- Pydantic Models for API (Modified) ---
class ChatRequest(BaseModel):
    user_input: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    assistant_response: str
    session_id: str
    retrieved_memory_count: int

class SessionCreateRequest(BaseModel):
    title: str
    description: Optional[str] = None
    persona_id: Optional[str] = None

# --- Event Handlers ---
@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時にメモリシステムを初期化"""
    print("Initializing memory systems...")
    await memory_manager.initialize()
    await gemini_client.initialize()
    print("Initialization complete. Dr. Aria's Semantic Memory API is ready.")

# --- API Endpoints (Modified) ---

@app.post("/chat", response_model=ChatResponse)
async def chat_with_assistant(request: ChatRequest):
    """
    アシスタントと会話を行います。
    session_idが指定されていない場合、新しいセッションが自動的に作成されます。
    """
    session_id = request.session_id
    
    # セッションIDがない場合、新しいセッションを自動作成
    if not session_id:
        new_session_id = str(uuid.uuid4())
        # 最初のユーザー入力から簡単なタイトルを生成
        title = f"Conversation started at {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        await memory_manager.create_session(session_id=new_session_id, title=title)
        session_id = new_session_id
    elif not await memory_manager.get_session(session_id):
        raise HTTPException(status_code=404, detail=f"Session with id {session_id} not found.")

    # 1. 関連記憶の検索
    retrieved_memories = await memory_manager.retrieve_memories(
        query=request.user_input,
        session_id=session_id
    )

    # 2. Geminiによる応答生成
    assistant_response = await gemini_client.generate_response(
        user_input=request.user_input,
        retrieved_memories=retrieved_memories
    )

    # 3. 今回の対話を記憶に保存
    user_memory = MemoryRecord(
        session_id=session_id,
        speaker="user",
        text=request.user_input
    )
    assistant_memory = MemoryRecord(
        session_id=session_id,
        speaker="assistant",
        text=assistant_response
    )
    await asyncio.gather(
        memory_manager.store_memory(user_memory),
        memory_manager.store_memory(assistant_memory)
    )

    return ChatResponse(
        assistant_response=assistant_response,
        session_id=session_id,
        retrieved_memory_count=len(retrieved_memories)
    )

@app.post("/sessions/", response_model=ConversationSession, summary="Manually create a new session")
async def create_new_session(request: SessionCreateRequest):
    """新しい会話セッションを手動で作成します。"""
    session_id = str(uuid.uuid4())
    session = await memory_manager.create_session(
        session_id=session_id,
        title=request.title,
        description=request.description,
        persona_id=request.persona_id
    )
    return session

@app.get("/sessions/", response_model=List[ConversationSession], summary="List all active sessions")
async def get_all_sessions():
    """アクティブな全セッションのリストを取得します。"""
    return await memory_manager.list_sessions()


@app.get("/")
def read_root():
    return {"message": "Dr. Aria's Semantic Memory API v2 is running."}
