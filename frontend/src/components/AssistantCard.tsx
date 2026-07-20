import { useState } from 'react'
import type { ScanResult } from '../types'
import { DECISION_META } from '../lib/decisions'
import { IconChevron } from '../icons'

export default function AssistantCard({ result, userText }: { result: ScanResult; userText: string }) {
  const [open, setOpen] = useState(false)
  const meta = DECISION_META[result.decision]
  const rawJson = {
    request_id: 'req-preview', user_input: userText, decision: result.decision,
    risk_level: result.riskLevel, risk_score: result.riskScore, reasons: [result.reason], output: result.body,
  }
  return (
    <div className="acard glass">
      <div>
        <span className={'chip ' + meta.chip}><span className="d" />{meta.label}</span>
        <span className="arisk">{result.riskLevel} · {result.riskScore}점</span>
      </div>
      <div className="abody">{result.body}</div>
      <div className="areason">사유: {result.reason}</div>
      <button className="ajson" onClick={() => setOpen((v) => !v)}>
        <IconChevron size={12} /> 원본 JSON 보기 (실제 주고받은 데이터)
      </button>
      {open && <pre>{JSON.stringify(rawJson, null, 2)}</pre>}
    </div>
  )
}
