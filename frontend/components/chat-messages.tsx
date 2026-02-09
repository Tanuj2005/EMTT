'use client'

import { useEffect, useRef } from 'react'
import { Bot, User } from 'lucide-react'

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
}

interface ChatMessagesProps {
  messages: ChatMessage[]
}

export default function ChatMessages({ messages }: ChatMessagesProps) {
  const scrollContainerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight
    }
  }, [messages])

  return (
    <div
      ref={scrollContainerRef}
      className="flex-1 overflow-y-auto p-6 space-y-4 bg-background"
    >
      {messages.length === 0 ? (
        <div className="h-full flex items-center justify-center">
          <div className="text-center">
            <Bot className="w-12 h-12 text-muted-foreground mx-auto mb-3 opacity-50" />
            <p className="text-muted-foreground">
              No messages yet. Ask something to get started!
            </p>
          </div>
        </div>
      ) : (
        messages.map((message) => (
          <div
            key={message.id}
            className={`flex gap-4 animate-in fade-in slide-in-from-bottom-2 ${
              message.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            {message.role === 'assistant' && (
              <div className="flex-shrink-0 flex items-start pt-1">
                <div className="bg-primary rounded-full p-2">
                  <Bot className="w-4 h-4 text-primary-foreground" />
                </div>
              </div>
            )}

            <div
              className={`max-w-xs lg:max-w-md px-4 py-3 rounded-lg ${
                message.role === 'user'
                  ? 'bg-primary text-primary-foreground rounded-br-none'
                  : 'bg-secondary text-foreground rounded-bl-none'
              }`}
            >
              <p className="text-sm leading-relaxed break-words">{message.content}</p>
            </div>

            {message.role === 'user' && (
              <div className="flex-shrink-0 flex items-start pt-1">
                <div className="bg-accent rounded-full p-2">
                  <User className="w-4 h-4 text-accent-foreground" />
                </div>
              </div>
            )}
          </div>
        ))
      )}
    </div>
  )
}
