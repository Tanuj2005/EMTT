'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { PlayCircle, Send } from 'lucide-react'
import Header from '@/components/header'
import ChatMessages from '@/components/chat-messages'

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
}

interface VideoInfo {
  title: string
  duration: string
}

export default function Home() {
  const [videoUrl, setVideoUrl] = useState('')
  const [videoInfo, setVideoInfo] = useState<VideoInfo | null>(null)
  const [loading, setLoading] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputValue, setInputValue] = useState('')
  const [sendingMessage, setSendingMessage] = useState(false)

  const handleFetchVideo = async () => {
    if (!videoUrl.trim()) return
    
    setLoading(true)
    try {
      // Simulated API call - Replace with actual YouTube API call
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      setVideoInfo({
        title: 'Sample YouTube Video',
        duration: '12:34'
      })

      // Add initial assistant message
      setMessages([{
        id: '0',
        role: 'assistant',
        content: 'I have loaded the transcript. What would you like to know about this video?'
      }])
    } catch (error) {
      console.error('Error fetching video:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSendMessage = async () => {
    if (!inputValue.trim() || !videoInfo) return

    // Add user message
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setSendingMessage(true)

    try {
      // Simulated API call - Replace with actual LLM API call
      await new Promise(resolve => setTimeout(resolve, 1000))

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'This is a sample response based on the video transcript. In a real implementation, this would be a response from your LLM API.'
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Error sending message:', error)
    } finally {
      setSendingMessage(false)
    }
  }

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
                    value={videoUrl}
                    onChange={(e) => setVideoUrl(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') handleFetchVideo()
                    }}
                    className="bg-input border-border text-foreground placeholder:text-muted-foreground"
                    disabled={loading}
                  />

                  <Button
                    onClick={handleFetchVideo}
                    disabled={!videoUrl.trim() || loading}
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
                    💡 <span className="font-semibold">Tip:</span> Use any public YouTube video URL. The transcript will be fetched automatically.
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
                  <h3 className="font-semibold line-clamp-3">{videoInfo.title}</h3>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <span>Duration: {videoInfo.duration}</span>
                  </div>
                  <Button
                    onClick={() => {
                      setVideoInfo(null)
                      setMessages([])
                      setVideoUrl('')
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
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault()
                          handleSendMessage()
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
  )
}
