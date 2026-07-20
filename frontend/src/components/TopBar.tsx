import { IconBolt, IconActivity, IconDeploy } from '../icons'

interface Props {
  firewallOn: boolean
  onToggleFirewall: () => void
}

export default function TopBar({ firewallOn, onToggleFirewall }: Props) {
  return (
    <div className="mtop">
      <div className="gw">
        <span className="z"><IconBolt size={13} /></span>AGENT SECURITY GATEWAY <span className="d" /><b>{firewallOn ? 'ON' : 'OFF'}</b>
      </div>
      <div className="r">
        <span className="toggle">
          Firewall
          <button className="sw" role="switch" aria-checked={firewallOn} aria-label="Firewall 토글" onClick={onToggleFirewall} />
        </span>
        <span className="lat"><IconActivity size={15} />{firewallOn ? '10ms' : '--'}</span>
        <button className="deploy"><IconDeploy size={14} /> Deploy</button>
      </div>
    </div>
  )
}
