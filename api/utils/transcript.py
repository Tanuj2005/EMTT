import re
from youtube_transcript_api import YouTubeTranscriptApi

# ← REMOVED: from utils.vector_store import TranscriptVectorStore
#   (only needed by store_transcript_for_rag; import it lazily there instead)


def extract_video_id(url: str) -> str:
    """Extract the video ID from various YouTube URL formats.
    Raises ValueError on invalid URL instead of returning None,
    so callers don't need to null-check.
    """
    patterns = [
        r"(?:v=|\/v\/|youtu\.be\/|\/embed\/)([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract video ID from URL: {url}")


def chunk_segments(segments: list, max_chunk_size: int = 500, overlap_size: int = 50) -> list:
    # ← NO CHANGES, keep exactly as you had it
    if not segments:
        return []

    chunks = []
    current_chunk_text = ""
    current_chunk_start = segments[0]["start"]
    current_chunk_segments = []

    for segment in segments:
        segment_text = segment["text"].strip()

        if len(current_chunk_text) + len(segment_text) + 1 > max_chunk_size and current_chunk_text:
            chunks.append({
                "text": current_chunk_text.strip(),
                "start": current_chunk_start,
                "duration": sum(s["duration"] for s in current_chunk_segments),
                "end": current_chunk_segments[-1]["start"] + current_chunk_segments[-1]["duration"]
            })

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

        current_chunk_text += " " + segment_text
        current_chunk_segments.append(segment)

    if current_chunk_text.strip():
        chunks.append({
            "text": current_chunk_text.strip(),
            "start": current_chunk_start,
            "duration": sum(s["duration"] for s in current_chunk_segments),
            "end": current_chunk_segments[-1]["start"] + current_chunk_segments[-1]["duration"]
        })

    return chunks


def get_youtube_transcript(video_url: str) -> dict:
    # ← NO CHANGES, keep exactly as you had it
    video_id = extract_video_id(video_url)  # now raises instead of returning None

    try:
        ytt_api = YouTubeTranscriptApi()
        fetched_transcript = ytt_api.fetch(video_id)
        segments = fetched_transcript.to_raw_data()
        full_text = " ".join(segment["text"] for segment in segments)
        return {"success": True, "transcript": full_text, "segments": segments, "error": None}

    except Exception as e:
        error_msg = str(e).lower()
        if "disabled" in error_msg:
            return {"success": False, "transcript": None, "segments": None, "error": "Transcripts are disabled for this video."}
        elif "no transcript" in error_msg or "not found" in error_msg:
            return {"success": False, "transcript": None, "segments": None, "error": "No transcript found for this video."}
        elif "unavailable" in error_msg:
            return {"success": False, "transcript": None, "segments": None, "error": "The video is unavailable."}
        else:
            return {"success": False, "transcript": None, "segments": None, "error": f"An unexpected error occurred: {str(e)}"}


# ← NEW FUNCTION: this is what rag.py imports and was missing
def fetch_transcript_segments(video_id: str, chunk_size: int = 500) -> list:
    """
    Fetch and chunk transcript segments by video ID, ready for vector storage.
    Raises ValueError or RuntimeError on failure (so rag.py can return HTTP 400).
    """
    try:
        ytt_api = YouTubeTranscriptApi()
        fetched = ytt_api.fetch(video_id)
        raw_segments = fetched.to_raw_data()
    except Exception as e:
        msg = str(e).lower()
        if "disabled" in msg:
            raise ValueError("Transcripts are disabled for this video.")
        if "no transcript" in msg or "not found" in msg:
            raise ValueError("No transcript found — the video may not have captions.")
        if "unavailable" in msg:
            raise ValueError("Video is unavailable (removed or private).")
        raise RuntimeError(f"Unexpected error fetching transcript: {e}")

    chunks = chunk_segments(raw_segments, max_chunk_size=chunk_size)
    if not chunks:
        raise ValueError("Transcript was empty after chunking.")
    return chunks


def store_transcript_for_rag(video_url: str, vector_store=None, chunk_size: int = 500) -> dict:
    # ← Lazy import to avoid circular dependency
    from utils.vector_store import TranscriptVectorStore

    result = get_youtube_transcript(video_url)
    if not result["success"]:
        return result

    video_id = extract_video_id(video_url)
    store = vector_store or TranscriptVectorStore()
    chunked_segments = chunk_segments(result["segments"], max_chunk_size=chunk_size)
    success = store.store_transcript(video_id=video_id, segments=chunked_segments, video_url=video_url)

    return {
        "success": success,
        "video_id": video_id,
        "segments_stored": len(chunked_segments) if success else 0,
        "original_segments": len(result["segments"]),
        "error": None if success else "Failed to store in vector database"
    }