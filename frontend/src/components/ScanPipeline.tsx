import { SCAN_STAGES } from '../types'
import { IconSearch, IconShieldCheck, IconPerson, IconChat, IconLock } from '../icons'

const STAGE_ICONS = [
  <IconSearch size={20} />, <IconShieldCheck size={20} />, <IconPerson size={20} />,
  <IconChat size={20} />, <IconLock size={20} />,
]

interface Props {
  firewallOn: boolean
  live: boolean            // 검사 진행 중이면 true
  activeStage: number      // 진행 중 현재 단계
  reachedStage: number     // 최종 도달 단계
  blockedAtReached: boolean
}

type St = 'idle' | 'on' | 'ok' | 'bad'

export default function ScanPipeline({ firewallOn, live, activeStage, reachedStage, blockedAtReached }: Props) {
  const stateOf = (i: number): St => {
    if (!firewallOn) return 'idle'
    if (live) {
      if (i < activeStage) return 'ok'
      if (i === activeStage) return (i === reachedStage && blockedAtReached) ? 'bad' : 'on'
      return 'idle'
    }
    return i === 0 ? 'on' : 'idle' // 대기(welcome) 시 첫 노드만 점등(장식)
  }

  return (
    <div className="pipe glass">
      <div className="ph">
        <span className="sh"><IconShieldCheck size={15} /></span>실시간 보안 검사 진행 중
        <span className="tag">SECURITY SCAN</span>
      </div>
      <div className="pnodes">
        {SCAN_STAGES.map((s, i) => {
          const st = stateOf(i)
          return (
            <div key={s.key} style={{ display: 'contents' }}>
              <div className={'pn ' + st}>
                <div className="nd">{STAGE_ICONS[i]}</div>
                <div className="pl">{s.label}</div>
                <div className="ps">{s.sub}</div>
              </div>
              {i < SCAN_STAGES.length - 1 && (
                <div className={'pc' + (st === 'ok' ? ' on' : '')} />
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
