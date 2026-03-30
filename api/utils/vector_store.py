import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any, Optional
import uuid
from pathlib import Path

class TranscriptVectorStore:
    """Store and retrieve transcript segments using ChromaDB."""
    
    def __init__(self, collection_name: str = "youtube_transcripts", persist_directory: str = "./chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function
        )
    
    def store_transcript(self, video_id: str, segments: List[Dict[str, Any]], video_url: str = None) -> bool:
        """
        Store transcript segments in the vector database.
        
        Args:
            video_id: YouTube video ID
            segments: List of {text, start, duration} dicts from transcript
            video_url: Optional full video URL for metadata
        
        Returns:
            True if successful, False otherwise
        """
        try:
            documents = []
            metadatas = []
            ids = []
            
            for i, segment in enumerate(segments):
                documents.append(segment["text"])
                metadatas.append({
                    "video_id": video_id,
                    "video_url": video_url or "",
                    "start": segment["start"],
                    "duration": segment["duration"],
                    "segment_index": i
                })
                ids.append(f"{video_id}_{i}_{uuid.uuid4().hex[:8]}")
            
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            return True
        except Exception as e:
            print(f"Error storing transcript: {e}")
            return False
    
    def search(self, query: str, n_results: int = 5, video_id: str = None) -> List[Dict[str, Any]]:
        """
        Search for relevant transcript segments.
        
        Args:
            query: Search query
            n_results: Number of results to return
            video_id: Optional filter by specific video
        
        Returns:
            List of matching segments with metadata
        """
        where_filter = {"video_id": video_id} if video_id else None
        
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter
        )
        
        matches = []
        for i in range(len(results["documents"][0])):
            matches.append({
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if results["distances"] else None
            })
        
        return matches
    
    def delete_video(self, video_id: str) -> bool:
        """Delete all segments for a specific video."""
        try:
            self.collection.delete(where={"video_id": video_id})
            return True
        except Exception as e:
            print(f"Error deleting video: {e}")
            return False
        
    def fetch_for_rag(
        self,
        query: str,
        video_id: Optional[str] = None,
        top_k: int = 6,
        max_context_chars: int = 3500,
        max_distance: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Fetch semantically relevant chunks and return LLM-ready context + sources.

        Args:
            query: User question
            video_id: Optional filter for one video
            top_k: Number of chunks to retrieve
            max_context_chars: Stop adding chunks after this context size
            max_distance: Optional distance cutoff (lower is better in Chroma)

        Returns:
            {
              "context": str,
              "chunks": [ {text, metadata, distance, score, citation} ],
              "count": int
            }
        """
        where_filter = {"video_id": video_id} if video_id else None

        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )

        docs = (results.get("documents") or [[]])[0]
        metas = (results.get("metadatas") or [[]])[0]
        dists = (results.get("distances") or [[]])[0]

        chunks: List[Dict[str, Any]] = []
        context_parts: List[str] = []
        current_len = 0

        for i, text in enumerate(docs):
            metadata = metas[i] if i < len(metas) else {}
            distance = dists[i] if i < len(dists) else None

            if max_distance is not None and distance is not None and distance > max_distance:
                continue

            citation = self._build_citation(metadata)
            score = (1.0 / (1.0 + distance)) if distance is not None else None

            block = f"[{citation}]\n{text}"
            next_len = current_len + len(block) + 2
            if next_len > max_context_chars:
                break

            context_parts.append(block)
            current_len = next_len

            chunks.append({
                "text": text,
                "metadata": metadata,
                "distance": distance,
                "score": score,
                "citation": citation
            })

        return {
            "context": "\n\n".join(context_parts),
            "chunks": chunks,
            "count": len(chunks)
        }

    def _build_citation(self, metadata: Dict[str, Any]) -> str:
        video_id = metadata.get("video_id", "unknown_video")
        start = metadata.get("start", 0)
        ts = self._format_seconds(start)
        return f"{video_id} @ {ts}"

    @staticmethod
    def _format_seconds(seconds: float) -> str:
        s = int(seconds or 0)
        h, rem = divmod(s, 3600)
        m, sec = divmod(rem, 60)
        if h > 0:
            return f"{h:02}:{m:02}:{sec:02}"
        return f"{m:02}:{sec:02}"