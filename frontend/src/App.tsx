import { useEffect, useRef, useState } from 'react'
import type { ChatMessage, ScanResult } from './types'
import { CURRENT_USER } from './data/dummy'
import { sendAgentMessage, fetchFirewallStatus, setFirewallStatus, ApiError } from './lib/api'
import Particles from './components/Particles'
import Sidebar from './components/Sidebar'
import TopBar from './components/TopBar'
import HoloStage from './components/HoloStage'
import PromptInput from './components/PromptInput'
import ScanPipeline from './components/ScanPipeline'
import MessageList from './components/MessageList'
import ProtectionRail from './components/ProtectionRail'
import { IconWarnTri } from './icons'

interface ScanningState {
  active: boolean
  activeStage: number
  result: ScanResult | null
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms))

export default function App() {
  const [firewallOn, setFirewallOn] = useState(true) // 서버 상태를 받아올 때까지의 기본값
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [scanning, setScanning] = useState<ScanningState | null>(null)
  const [activeChatId, setActiveChatId] = useState<string | null>(null)
  const idc = useRef(0)
  const nextId = () => `m${++idc.current}`

  // 연동 STEP — 관제 대시보드(streamlit_app.py)와 같은 kill-switch 상태(SQLite flags 테이블)를
  // 공유하기 위해, 화면을 열 때 서버(GET /firewall)에서 실제 상태를 받아옵니다.
  useEffect(() => {
    fetchFirewallStatus()
      .then(setFirewallOn)
      .catch(() => {
        // 백엔드가 아직 안 켜져 있으면 조용히 기본값(ON)을 유지합니다.
      })
  }, [])

  // 연동 STEP — 실제 FastAPI 백엔드(POST /agent/message)를 호출합니다. 방화벽 ON/OFF는
  // 서버(control_service)가 최종 판단하므로, 클라이언트는 항상 같은 API를 호출하고
  // 응답의 riskLevel === 'OFF' 여부로 "검사 없이 통과됨"을 표시합니다.
  async function handleSend(text: string) {
    if (scanning?.active) return
    setMessages((m) => [...m, { id: nextId(), role: 'user', text }])
    setScanning({ active: true, activeStage: firewallOn ? 0 : -1, result: null })

    try {
      const result = await sendAgentMessage(CURRENT_USER.name, text)
      const live = firewallOn && result.riskLevel !== 'OFF'
      if (live) {
        for (let i = 0; i <= result.reachedStage; i++) {
          setScanning((s) => (s ? { ...s, activeStage: i, result } : s))
          await sleep(260)
        }
        await sleep(360)
      } else {
        setScanning((s) => (s ? { ...s, result } : s))
        await sleep(500)
      }
      setMessages((m) => [...m, { id: nextId(), role: 'assistant', text: '', result }])
    } catch (e) {
      const message = e instanceof ApiError ? e.message : '알 수 없는 오류가 발생했습니다.'
      const errorResult: ScanResult = {
        decision: 'BLOCK', riskLevel: 'OFF', riskScore: 0,
        reason: '백엔드 연결 오류 (보안 판정이 아닙니다)', body: message,
        reachedStage: 0, blockedAtReached: true,
      }
      setMessages((m) => [...m, { id: nextId(), role: 'assistant', text: '', result: errorResult }])
    } finally {
      setScanning(null)
    }
  }

  // 연동 STEP — Firewall 토글이 실제로 서버(POST /firewall)의 kill-switch를 바꾸도록 연결.
  async function handleToggleFirewall() {
    const next = !firewallOn
    setFirewallOn(next) // 낙관적 업데이트
    try {
      const confirmed = await setFirewallStatus(next)
      setFirewallOn(confirmed)
    } catch {
      setFirewallOn(next)
    }
  }

  const handleNewChat = () => {
    if (scanning?.active) return
    setMessages([])
    setActiveChatId(null)
  }

  const welcome = messages.length === 0 && !scanning?.active
  const scanActive = !!scanning?.active
  const activeStage = scanning?.activeStage ?? -1
  const reachedStage = scanning?.result?.reachedStage ?? 4
  const blockedAtReached = scanning?.result?.blockedAtReached ?? false
  const liveScan = scanActive && scanning?.result?.riskLevel !== 'OFF'

  return (
    <>
      <div className="bgfx" aria-hidden />
      <Particles />
      <div className={'app' + (firewallOn ? '' : ' off')}>
        <Sidebar
          firewallOn={firewallOn}
          activeChatId={activeChatId}
          onNewChat={handleNewChat}
          onSelectChat={setActiveChatId}
        />

        <main className="main">
          <TopBar firewallOn={firewallOn} onToggleFirewall={handleToggleFirewall} />
          {!firewallOn && (
            <div className="offbanner">
              <IconWarnTri size={16} />
              방화벽이 꺼져 있습니다 — AI 행동이 검사 없이 실행됩니다.
            </div>
          )}

          <div className="center">
            {welcome ? (
              <div className="stage">
                <div className="hero">
                  <h1>안녕하세요, <span className="u">{CURRENT_USER.name}</span>님</h1>
                  <p>AI Agent가 안전하게 도와드릴게요.</p>
                </div>
                <HoloStage />
              </div>
            ) : (
              <MessageList messages={messages} scanningTick={activeStage} />
            )}
          </div>

          <PromptInput disabled={scanActive} onSend={handleSend} />
          <ScanPipeline
            firewallOn={firewallOn}
            live={liveScan}
            activeStage={activeStage}
            reachedStage={reachedStage}
            blockedAtReached={blockedAtReached}
          />
        </main>

        <ProtectionRail firewallOn={firewallOn} scanning={liveScan} activeStage={activeStage} />
      </div>
    </>
  )
}
