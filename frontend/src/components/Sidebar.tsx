import type { ReactNode } from 'react'
import { CURRENT_USER, RECENT_CHATS } from '../data/dummy'
import {
  IconShieldMark, IconPlus, IconSearch, IconChevron, IconDots, IconShieldCheck,
  IconChat, IconDoc, IconBoxCheck, IconReturn, IconPerson,
} from '../icons'

const RC_ICONS: ReactNode[] = [<IconChat />, <IconDoc />, <IconBoxCheck />, <IconReturn />, <IconPerson />]

interface Props {
  firewallOn: boolean
  activeChatId: string | null
  onNewChat: () => void
  onSelectChat: (id: string) => void
}

export default function Sidebar({ firewallOn, activeChatId, onNewChat, onSelectChat }: Props) {
  return (
    <aside className="side glass">
      <div className="brand">
        <div className="mk"><IconShieldMark size={21} /></div>
        <div><div className="nm">AGENT ACTION FIREWALL</div><div className="sub">Personal AI Guard</div></div>
      </div>

      <button className="newchat" onClick={onNewChat}><IconPlus size={15} /> 새 채팅</button>

      <div className="lblrow">
        <span className="lbl">최근 대화</span>
        <button className="sr" aria-label="검색"><IconSearch size={14} /></button>
      </div>

      <div className="reclist">
        {RECENT_CHATS.map((c, i) => (
          <button
            key={c.id}
            className={'rc' + (activeChatId === c.id ? ' active' : '')}
            onClick={() => onSelectChat(c.id)}
          >
            <span className="ci">{RC_ICONS[i % RC_ICONS.length]}</span>
            <span className="ct">{c.title}</span>
            <span className="cm">{c.time}</span>
          </button>
        ))}
        <button className="more">기록 더 보기 <IconChevron size={15} /></button>
      </div>

      <div className="spacer" />

      <div className="fwcard">
        <div className="lb">Firewall Status</div>
        <div className="st"><span className="ico"><IconShieldCheck size={14} /></span>{firewallOn ? 'PROTECTION ON' : 'PROTECTION OFF'}</div>
        <div className="desc">
          {firewallOn ? '개인 AI 요청을 실시간으로 보호 중입니다.' : '보호 비활성 - 요청이 검사 없이 실행됩니다.'}
        </div>
        <svg className="spark" width="100%" height={40} viewBox="0 0 240 40" preserveAspectRatio="none">
          <defs>
            <linearGradient id="aaf-sp" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor="rgba(47,224,166,.4)" /><stop offset="1" stopColor="rgba(47,224,166,0)" />
            </linearGradient>
          </defs>
          <path d="M0 30 L30 26 L55 30 L80 18 L105 24 L130 12 L160 22 L185 14 L210 20 L240 10 L240 40 L0 40Z" fill="url(#aaf-sp)" />
          <path d="M0 30 L30 26 L55 30 L80 18 L105 24 L130 12 L160 22 L185 14 L210 20 L240 10" fill="none" stroke="#2FE0A6" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>

      <div className="prof">
        <div className="av">{CURRENT_USER.initial}</div>
        <div>
          <div className="pn">{CURRENT_USER.name}님</div>
          <div className="pr"><i />{CURRENT_USER.team} · 온라인</div>
        </div>
        <button className="mm" aria-label="메뉴"><IconDots size={16} /></button>
      </div>
    </aside>
  )
}
