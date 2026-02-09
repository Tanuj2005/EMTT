import re
from youtube_transcript_api import YouTubeTranscriptApi


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


# --- Example usage ---
if __name__ == "__main__":
    test_url = "https://www.youtube.com/watch?v=ssYt09bCgUY"

    result = get_youtube_transcript(test_url)

    if result["success"]:
        print("Transcript fetched successfully!\n")
        print(result["transcript"][:])  # Print first 500 chars
        print(f"\n... ({len(result['segments'])} segments total)")
    else:
        print(f"Failed to get transcript: {result['error']}")