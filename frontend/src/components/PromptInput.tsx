import { useState } from 'react'
import { IconAttach, IconWave, IconSend } from '../icons'

interface Props {
  disabled: boolean
  onSend: (text: string) => void
}

export default function PromptInput({ disabled, onSend }: Props) {
  const [text, setText] = useState('')
  const submit = () => {
    const t = text.trim()
    if (!t || disabled) return
    onSend(t)
    setText('')
  }
  return (
    <div className="pinput">
      <div className="pinner">
        <input
          value={text}
          placeholder="AI에게 요청하세요…"
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit() } }}
        />
        <div className="bt">
          <button className="iconbtn" aria-label="첨부"><IconAttach size={16} /></button>
          <span className="rt">
            <button className="iconbtn" aria-label="음성"><IconWave size={16} /></button>
            <button className="send" onClick={submit} disabled={disabled} aria-label="전송"><IconSend size={17} /></button>
          </span>
        </div>
      </div>
    </div>
  )
}
