from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from utils.vector_store import TranscriptVectorStore
from utils.transcript import extract_video_id, fetch_transcript_segments
from utils.gemini import generate_answer_with_gemini

router = APIRouter(prefix="/rag", tags=["rag"])
store = TranscriptVectorStore()

class IndexRequest(BaseModel):
    youtube_url: str = Field(..., min_length=5)
    force_reindex: bool = True

class AskRequest(BaseModel):
    video_id: str = Field(..., min_length=11, max_length=11)
    question: str = Field(..., min_length=2)
    top_k: int = 6

@router.post("/index")
def index_video(req: IndexRequest) -> Dict[str, Any]:
    try:
        video_id = extract_video_id(req.youtube_url)
        segments = fetch_transcript_segments(video_id)

        if req.force_reindex:
            store.delete_video(video_id)

        ok = store.store_transcript(video_id=video_id, segments=segments, video_url=req.youtube_url)
        if not ok:
            raise RuntimeError("Vector store insert failed.")

        return {"success": True, "video_id": video_id, "segments_indexed": len(segments)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/ask")
def ask_video(req: AskRequest) -> Dict[str, Any]:
    try:
        rag = store.fetch_for_rag(
            query=req.question,
            video_id=req.video_id,
            top_k=req.top_k,
            max_context_chars=4000
        )

        if rag["count"] == 0:
            return {"answer": "I could not find relevant transcript context for this question.", "sources": [], "count": 0}

        answer = generate_answer_with_gemini(
            question=req.question,
            context=rag["context"],
            sources=rag["chunks"]
        )

        return {"answer": answer, "sources": rag["chunks"], "count": rag["count"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))