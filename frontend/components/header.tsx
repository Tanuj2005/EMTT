import { Youtube } from 'lucide-react'

export default function Header() {
  return (
    <header className="border-b border-border bg-card">
      <div className="max-w-7xl mx-auto px-4 py-4 flex items-center">
        <div className="flex items-center gap-3">
          <div className="bg-primary rounded-lg p-2">
            <Youtube className="w-6 h-6 text-primary-foreground" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-foreground">TranscriptChat</h1>
            <p className="text-xs text-muted-foreground">Chat with video transcripts</p>
          </div>
        </div>
      </div>
    </header>
  )
}
