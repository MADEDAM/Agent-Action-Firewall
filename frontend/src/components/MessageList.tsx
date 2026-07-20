import { useEffect, useRef } from 'react'
import type { ChatMessage } from '../types'
import AssistantCard from './AssistantCard'

interface Props {
  messages: ChatMessage[]
  scanningTick: unknown // 스크롤 트리거용
}

export default function MessageList({ messages, scanningTick }: Props) {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    ref.current?.scrollTo({ top: ref.current.scrollHeight, behavior: 'smooth' })
  }, [messages, scanningTick])

  return (
    <div className="chatscroll" ref={ref}>
      {messages.map((m) =>
        m.role === 'user' ? (
          <div className="ubub" key={m.id}>{m.text}</div>
        ) : (
          m.result && <AssistantCard key={m.id} result={m.result} userText={findUserBefore(messages, m.id)} />
        ),
      )}
    </div>
  )
}

function findUserBefore(messages: ChatMessage[], id: string): string {
  const idx = messages.findIndex((m) => m.id === id)
  for (let i = idx - 1; i >= 0; i--) if (messages[i].role === 'user') return messages[i].text
  return ''
}
