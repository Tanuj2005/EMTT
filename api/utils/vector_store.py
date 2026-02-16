import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any
import uuid


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