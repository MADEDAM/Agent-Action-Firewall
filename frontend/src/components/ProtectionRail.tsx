import { IconShieldCheck, IconShieldWire } from '../icons'

interface Props {
  firewallOn: boolean
  scanning: boolean
  activeStage: number
}

export default function ProtectionRail({ firewallOn, scanning }: Props) {
  const scanText = !firewallOn
    ? '보호가 꺼져 있어 검사를 쉬고 있습니다'
    : scanning
      ? '요청을 실시간으로 검사 중입니다'
      : '특이사항 없이 정상 작동 중입니다'

  return (
    <aside className="rail">
      <div className="prothead glass">
        <span className="ghost"><IconShieldWire size={130} /></span>
        <div className="hd">
          <div className="sh"><IconShieldCheck size={24} /></div>
          <div>
            <div className="t">{firewallOn ? '보안 보호 중' : '보호 비활성'}</div>
            <div className="row"><i />{firewallOn ? '시스템 정상' : '검사 중지'}</div>
          </div>
        </div>
        <div className="ds">
          Agent Action Firewall이 개인 AI 에이전트의 민감한 행동을 안전하게 보호하고 있습니다.
        </div>
      </div>

      <div className="railstatus glass">
        <div className="pulse" />
        <div>
          <div className="rt">실시간 검사 중</div>
          <div className="rd">{scanText}</div>
        </div>
      </div>

      <div className="polstat glass">
        <div className="h">정책 엔진 상태 <b>{firewallOn ? '모두 정상' : '비활성'}</b></div>
        <div className="leg">
          <span><i />개인정보</span>
          <span><i />비밀정보</span>
          <span><i />외부전송</span>
          <span><i />위험행동</span>
        </div>
      </div>
    </aside>
  )
}
