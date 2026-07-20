import owlGuardian from '../assets/owl-guardian.png'
import owlGuardianOff from '../assets/owl-guardian-off.png'

// 중앙 홀로그램 컴포지션 — AI 경비 올빼미 + 플로팅 라벨 노드 + 오빗 + 플랫폼 dais + 연결선.
// 전부 JSX 요소이며 문자로 노출되지 않습니다.
const NODES = [
  { style: { left: 56, top: 96 }, t: 'AI GUARD', s: '실시간 위험 탐지' },
  { style: { left: 56, top: 230 }, t: 'POLICY ENGINE', s: '정책 기반 검증' },
  { style: { right: 56, top: 110 }, t: 'EXECUTION CONTROL', s: '도구 실행 통제' },
  { style: { right: 56, top: 242 }, t: 'OUTPUT FILTER', s: '응답 안전성 검사' },
]

export default function HoloStage() {
  return (
    <div className="holo">
      <svg className="wires" viewBox="0 0 660 400" preserveAspectRatio="none">
        <defs>
          <linearGradient id="aaf-wg" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0" stopColor="rgba(90,140,255,.1)" /><stop offset="1" stopColor="rgba(47,230,245,.7)" />
          </linearGradient>
        </defs>
        <line x1="180" y1="118" x2="280" y2="168" stroke="url(#aaf-wg)" strokeWidth={1.2} />
        <line x1="180" y1="248" x2="285" y2="205" stroke="url(#aaf-wg)" strokeWidth={1.2} />
        <line x1="480" y1="132" x2="378" y2="172" stroke="url(#aaf-wg)" strokeWidth={1.2} />
        <line x1="470" y1="258" x2="375" y2="210" stroke="url(#aaf-wg)" strokeWidth={1.2} />
        <circle cx="280" cy="168" r="3" fill="#2FE6F5" /><circle cx="285" cy="205" r="3" fill="#2FE6F5" />
        <circle cx="378" cy="172" r="3" fill="#2FE6F5" /><circle cx="375" cy="210" r="3" fill="#2FE6F5" />
      </svg>

      {NODES.map((n) => (
        <div className="lnode" key={n.t} style={n.style}>
          <div className="lt">{n.t}</div><div className="ls">{n.s}</div>
        </div>
      ))}

      <div className="holocenter">
        <div className="aura" /><div className="beam" />
        <div className="orbit o1"><span className="sat" /></div>
        <div className="orbit o2"><span className="sat" /></div>
        <div className="dais"><div className="glow" /><div className="ring r1" /><div className="ring r2" /><div className="ring r3" /></div>
        <div className="guardianwrap" aria-hidden="true">
          <div className="guardian-hud hud-a">
            <i /><span /><span /><b />
          </div>
          <div className="guardian-hud hud-b">
            <i /><span /><span /><b />
          </div>
          <div className="guardian-hud hud-c">
            <i /><span /><span /><b />
          </div>
          <img className="guardian-img guardian-img-on" src={owlGuardian} alt="" />
          <img className="guardian-img guardian-img-off" src={owlGuardianOff} alt="" />
        </div>
      </div>
    </div>
  )
}
