import { useMemo } from 'react'

// 은은한 파티클 필드 (배경). 위치/속도는 최초 1회만 계산.
export default function Particles({ count = 44 }: { count?: number }) {
  const dots = useMemo(
    () =>
      Array.from({ length: count }, () => ({
        left: Math.random() * 100,
        top: Math.random() * 100,
        delay: Math.random() * 9,
        opacity: 0.2 + Math.random() * 0.6,
        scale: 0.6 + Math.random() * 1.4,
      })),
    [count],
  )
  return (
    <div className="particles" aria-hidden>
      {dots.map((d, i) => (
        <i
          key={i}
          style={{
            left: `${d.left}%`,
            top: `${d.top}%`,
            animationDelay: `${d.delay}s`,
            opacity: d.opacity,
            transform: `scale(${d.scale})`,
          }}
        />
      ))}
    </div>
  )
}
