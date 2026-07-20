import type { ReactNode } from 'react'
import { QUICK_ACTIONS } from '../data/dummy'
import { IconCart, IconChart, IconBox } from '../icons'

const ICONS: ReactNode[] = [<IconCart />, <IconChart />, <IconBox />]

export default function QuickChips({ onPick }: { onPick: (text: string) => void }) {
  return (
    <div className="chips">
      {QUICK_ACTIONS.map((a, i) => (
        <button className="chip2" key={a} onClick={() => onPick(a)}>
          {ICONS[i % ICONS.length]}{a}
        </button>
      ))}
    </div>
  )
}
