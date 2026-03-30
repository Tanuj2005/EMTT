const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000/api";

export type SourceChunk = {
  text: string;
  metadata: Record<string, unknown>;
  distance?: number;
  score?: number;
  citation?: string;
};

export async function indexVideo(youtube_url: string) {
  const res = await fetch(`${API_BASE}/rag/index`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ youtube_url, force_reindex: true }),
  });
  if (!res.ok) throw new Error((await res.json()).detail || "Failed to index video");
  return res.json() as Promise<{ success: boolean; video_id: string; segments_indexed: number }>;
}

export async function askQuestion(video_id: string, question: string) {
  const res = await fetch(`${API_BASE}/rag/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ video_id, question, top_k: 6 }),
  });
  if (!res.ok) throw new Error((await res.json()).detail || "Failed to get answer");
  return res.json() as Promise<{ answer: string; sources: SourceChunk[]; count: number }>;
}