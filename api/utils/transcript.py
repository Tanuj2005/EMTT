import re
from youtube_transcript_api import YouTubeTranscriptApi
from vector_store import TranscriptVectorStore


def extract_video_id(url: str) -> str | None:
    """Extract the video ID from various YouTube URL formats."""
    patterns = [
        r"(?:v=|\/v\/|youtu\.be\/|\/embed\/)([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def chunk_segments(segments: list, max_chunk_size: int = 500, overlap_size: int = 50) -> list:
    """
    Combine small transcript segments into larger chunks for better RAG retrieval.
    
    Args:
        segments: List of {text, start, duration} dicts from transcript
        max_chunk_size: Maximum characters per chunk
        overlap_size: Number of characters to overlap between chunks
    
    Returns:
        List of chunked segments with combined text and timing metadata
    """
    if not segments:
        return []
    
    chunks = []
    current_chunk_text = ""
    current_chunk_start = segments[0]["start"]
    current_chunk_segments = []
    
    for segment in segments:
        segment_text = segment["text"].strip()
        
        # Check if adding this segment would exceed max size
        if len(current_chunk_text) + len(segment_text) + 1 > max_chunk_size and current_chunk_text:
            # Save current chunk
            chunks.append({
                "text": current_chunk_text.strip(),
                "start": current_chunk_start,
                "duration": sum(s["duration"] for s in current_chunk_segments),
                "end": current_chunk_segments[-1]["start"] + current_chunk_segments[-1]["duration"]
            })
            
            # Start new chunk with overlap (include last few segments)
            overlap_text = ""
            overlap_segments = []
            for prev_seg in reversed(current_chunk_segments):
                if len(overlap_text) + len(prev_seg["text"]) < overlap_size:
                    overlap_text = prev_seg["text"] + " " + overlap_text
                    overlap_segments.insert(0, prev_seg)
                else:
                    break
            
            current_chunk_text = overlap_text
            current_chunk_start = overlap_segments[0]["start"] if overlap_segments else segment["start"]
            current_chunk_segments = overlap_segments.copy()
        
        # Add segment to current chunk
        current_chunk_text += " " + segment_text
        current_chunk_segments.append(segment)
    
    # Don't forget the last chunk
    if current_chunk_text.strip():
        chunks.append({
            "text": current_chunk_text.strip(),
            "start": current_chunk_start,
            "duration": sum(s["duration"] for s in current_chunk_segments),
            "end": current_chunk_segments[-1]["start"] + current_chunk_segments[-1]["duration"]
        })
    
    return chunks



def get_youtube_transcript(video_url: str) -> dict:
    """
    Fetch the transcript of a YouTube video given its URL.

    Args:
        video_url: Full YouTube video URL.

    Returns:
        A dict with:
          - "success" (bool)
          - "transcript" (str | None): Full transcript text if available.
          - "segments" (list | None): List of {text, start, duration} dicts.
          - "error" (str | None): Error message if transcript is unavailable.
    """
    video_id = extract_video_id(video_url)
    if not video_id:
        return {
            "success": False,
            "transcript": None,
            "segments": None,
            "error": "Invalid YouTube URL. Could not extract video ID.",
        }

    try:
        ytt_api = YouTubeTranscriptApi()
        fetched_transcript = ytt_api.fetch(video_id)

        # Use .to_raw_data() to get list of dicts
        segments = fetched_transcript.to_raw_data()

        full_text = " ".join(segment["text"] for segment in segments)

        return {
            "success": True,
            "transcript": full_text,
            "segments": segments,
            "error": None,
        }

    except Exception as e:
        error_msg = str(e).lower()

        if "disabled" in error_msg:
            return {
                "success": False,
                "transcript": None,
                "segments": None,
                "error": "Transcripts are disabled for this video.",
            }
        elif "no transcript" in error_msg or "not found" in error_msg:
            return {
                "success": False,
                "transcript": None,
                "segments": None,
                "error": "No transcript found for this video. It may not have captions available.",
            }
        elif "unavailable" in error_msg:
            return {
                "success": False,
                "transcript": None,
                "segments": None,
                "error": "The video is unavailable. It may have been removed or is private.",
            }
        else:
            return {
                "success": False,
                "transcript": None,
                "segments": None,
                "error": f"An unexpected error occurred: {str(e)}",
            }


def store_transcript_for_rag(video_url: str, vector_store: TranscriptVectorStore = None, chunk_size: int = 500) -> dict:
    """
    Fetch and store a YouTube transcript in the vector database for RAG.
    
    Args:
        video_url: Full YouTube video URL
        vector_store: Optional existing vector store instance
        chunk_size: Maximum characters per chunk (default 500)
    
    Returns:
        Dict with success status and metadata
    """
    result = get_youtube_transcript(video_url)
    
    if not result["success"]:
        return result
    
    video_id = extract_video_id(video_url)
    store = vector_store or TranscriptVectorStore()
    
    # Chunk the segments into larger pieces
    chunked_segments = chunk_segments(result["segments"], max_chunk_size=chunk_size)
    
    success = store.store_transcript(
        video_id=video_id,
        segments=chunked_segments,
        video_url=video_url
    )
    
    return {
        "success": success,
        "video_id": video_id,
        "segments_stored": len(chunked_segments) if success else 0,
        "original_segments": len(result["segments"]),
        "error": None if success else "Failed to store in vector database"
    }


# --- Example usage ---
if __name__ == "__main__":
    result = store_transcript_for_rag("https://www.youtube.com/watch?v=ssYt09bCgUY")

# Search for relevant content
    store = TranscriptVectorStore()
    matches = store.search("moltbot", n_results=5)

    for match in matches:
        print(f"[{match['metadata']['start']:.1f}s]: {match['text']}")