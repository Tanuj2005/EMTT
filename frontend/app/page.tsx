
"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { PlayCircle, Send } from "lucide-react";
import Header from "@/components/header";
import ChatMessages from "@/components/chat-messages";
import { askQuestion, indexVideo, SourceChunk } from "@/lib/api";

type Msg = {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: SourceChunk[];
};

interface VideoInfo {
  title: string;
  videoId: string;
  segmentsIndexed: number;
}

export default function Page() {
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [videoInfo, setVideoInfo] = useState<VideoInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<Msg[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [sendingMessage, setSendingMessage] = useState(false);

  const handleFetchVideo = async () => {
    if (!youtubeUrl.trim()) return;

    setLoading(true);
    try {
      const data = await indexVideo(youtubeUrl);
      setVideoInfo({
        title: `Video — ${data.video_id}`,
        videoId: data.video_id,
        segmentsIndexed: data.segments_indexed,
      });
      setMessages([
        {
          id: "0",
          role: "assistant",
          content: `I've loaded the transcript (${data.segments_indexed} segments indexed). What would you like to know about this video?`,
        },
      ]);
    } catch (e: any) {
      console.error("Error indexing video:", e);
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || !videoInfo) return;

    const userMessage: Msg = {
      id: Date.now().toString(),
      role: "user",
      content: inputValue,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setSendingMessage(true);

    try {
      const data = await askQuestion(videoInfo.videoId, userMessage.content);
      const assistantMessage: Msg = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.answer,
        sources: data.sources || [],
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (e: any) {
      const errorMessage: Msg = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: e.message || "Failed to get an answer. Please try again.",
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setSendingMessage(false);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Header />

      <main className="max-w-7xl mx-auto px-4 py-8">
        {!videoInfo ? (
          <div className="flex items-center justify-center min-h-[60vh]">
            <Card className="w-full max-w-2xl bg-card border-border p-8">
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold mb-2 text-pretty">
                    Paste Your YouTube Video Link
                  </h2>
                  <p className="text-muted-foreground">
                    Enter a YouTube URL to fetch the transcript and start chatting
                  </p>
                </div>

                <div className="space-y-4">
                  <Input
                    type="url"
                    placeholder="https://www.youtube.com/watch?v=..."
                    value={youtubeUrl}
                    onChange={(e) => setYoutubeUrl(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === "Enter") handleFetchVideo();
                    }}
                    className="bg-input border-border text-foreground placeholder:text-muted-foreground"
                    disabled={loading}
                  />

                  <Button
                    onClick={handleFetchVideo}
                    disabled={!youtubeUrl.trim() || loading}
                    className="w-full bg-primary text-primary-foreground hover:bg-primary/90 font-semibold h-11"
                  >
                    {loading ? (
                      <>
                        <div className="animate-spin mr-2 h-4 w-4 border-2 border-current border-t-transparent rounded-full" />
                        Loading transcript...
                      </>
                    ) : (
                      <>
                        <PlayCircle className="w-5 h-5 mr-2" />
                        Load Video
                      </>
                    )}
                  </Button>
                </div>

                <div className="bg-secondary/30 border border-border rounded-lg p-4">
                  <p className="text-sm text-muted-foreground">
                    💡 <span className="font-semibold">Tip:</span> Use any
                    public YouTube video URL. The transcript will be fetched
                    automatically.
                  </p>
                </div>
              </div>
            </Card>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Video Info Sidebar */}
            <div className="lg:col-span-1">
              <Card className="bg-card border-border sticky top-8 p-4">
                <div className="space-y-3">
                  <h3 className="font-semibold line-clamp-3">
                    {videoInfo.title}
                  </h3>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <span>{videoInfo.segmentsIndexed} segments indexed</span>
                  </div>
                  <Button
                    onClick={() => {
                      setVideoInfo(null);
                      setMessages([]);
                      setYoutubeUrl("");
                    }}
                    variant="outline"
                    className="w-full border-border text-foreground hover:bg-secondary"
                  >
                    Load Different Video
                  </Button>
                </div>
              </Card>
            </div>

            {/* Chat Interface */}
            <div className="lg:col-span-2 flex flex-col h-[calc(100vh-12rem)]">
              <Card className="flex-1 bg-card border-border flex flex-col overflow-hidden">
                {/* Messages */}
                <ChatMessages messages={messages} />

                {/* Input Area */}
                <div className="border-t border-border p-4 bg-card">
                  <div className="flex gap-3">
                    <Textarea
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                      onKeyPress={(e) => {
                        if (e.key === "Enter" && !e.shiftKey) {
                          e.preventDefault();
                          handleSendMessage();
                        }
                      }}
                      placeholder="Ask something about the video..."
                      disabled={sendingMessage}
                      className="resize-none bg-input border-border text-foreground placeholder:text-muted-foreground focus-visible:ring-primary"
                      rows={3}
                    />
                    <Button
                      onClick={handleSendMessage}
                      disabled={!inputValue.trim() || sendingMessage}
                      className="bg-primary text-primary-foreground hover:bg-primary/90 self-end"
                    >
                      {sendingMessage ? (
                        <div className="animate-spin h-5 w-5 border-2 border-current border-t-transparent rounded-full" />
                      ) : (
                        <Send className="w-5 h-5" />
                      )}
                    </Button>
                  </div>
                </div>
              </Card>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}