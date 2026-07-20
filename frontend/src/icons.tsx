// 공용 인라인 SVG 아이콘 (외부 라이브러리 없이). 전부 JSX — 문자로 노출되지 않습니다.
type P = { size?: number; className?: string }
const b = (size: number, className?: string) => ({
  width: size, height: size, viewBox: '0 0 24 24', fill: 'none',
  stroke: 'currentColor', strokeWidth: 2, strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const, className,
})

export const IconShieldMark = ({ size = 21, className }: P) => (
  <svg {...b(size, className)} strokeWidth={1.5} stroke="#9DBBFF">
    <path d="M12 2.5l7.5 3.2v6.1c0 5.2-3.4 8.9-7.5 10.2-4.1-1.3-7.5-5-7.5-10.2V5.7L12 2.5z" fill="rgba(59,107,255,.18)" />
    <path d="M8.5 12.3l2.4 2.4 4.6-4.8" stroke="#2FE6F5" strokeWidth={1.9} />
  </svg>
)
export const IconShieldCheck = ({ size = 20, className }: P) => (
  <svg {...b(size, className)} strokeWidth={1.85}><path d="M12 3l7 3v5c0 4.5-3 7.8-7 9-4-1.2-7-4.5-7-9V6l7-3z" /><path d="M9 12l2 2 4-4" /></svg>
)
export const IconShieldWire = ({ size = 130, className }: P) => (
  <svg {...b(size, className)} strokeWidth={0.5}><path d="M12 3l7 3v5c0 4.5-3 7.8-7 9-4-1.2-7-4.5-7-9V6z" /><path d="M12 3v18M5 8h14M5 14h14" /></svg>
)
export const IconPlus = ({ size = 15, className }: P) => (<svg {...b(size, className)} strokeWidth={2.3}><path d="M12 5v14M5 12h14" /></svg>)
export const IconSearch = ({ size = 14, className }: P) => (<svg {...b(size, className)}><circle cx="11" cy="11" r="7" /><path d="M20 20l-3-3" /></svg>)
export const IconChevron = ({ size = 15, className }: P) => (<svg {...b(size, className)}><path d="M9 6l6 6-6 6" /></svg>)
export const IconDots = ({ size = 16, className }: P) => (<svg {...b(size, className)} fill="currentColor" stroke="none"><circle cx="12" cy="5" r="1.6" /><circle cx="12" cy="12" r="1.6" /><circle cx="12" cy="19" r="1.6" /></svg>)
export const IconBolt = ({ size = 13, className }: P) => (<svg {...b(size, className)}><path d="M13 2L4 14h7l-1 8 9-12h-7z" /></svg>)
export const IconActivity = ({ size = 15, className }: P) => (<svg {...b(size, className)}><path d="M3 12h4l2 6 4-14 2 8h6" /></svg>)
export const IconDeploy = ({ size = 14, className }: P) => (<svg {...b(size, className)}><path d="M5 19l7-14 7 14-7-4z" /></svg>)
export const IconAttach = ({ size = 16, className }: P) => (<svg {...b(size, className)} strokeWidth={1.9}><path d="M21 12.5l-8.5 8.5a5 5 0 01-7-7l9-9a3.3 3.3 0 015 5l-9 9a1.7 1.7 0 01-2.4-2.4l8.5-8.5" /></svg>)
export const IconWave = ({ size = 16, className }: P) => (<svg {...b(size, className)}><path d="M6 10v4M10 6v12M14 8v8M18 10v4" /></svg>)
export const IconSend = ({ size = 17, className }: P) => (<svg {...b(size, className)} strokeWidth={2.4}><path d="M12 19V5M5 12l7-7 7 7" /></svg>)
export const IconWarnTri = ({ size = 16, className }: P) => (<svg {...b(size, className)}><path d="M12 3.5l9 15.5H3z" /><path d="M12 10v4" /><circle cx="12" cy="16.6" r=".6" fill="currentColor" /></svg>)
export const IconCheck = ({ size = 16, className }: P) => (<svg {...b(size, className)} strokeWidth={2.4}><path d="M5 12l5 5L20 7" /></svg>)

// recent-chat / chip / pipeline / rail 아이콘
export const IconChat = ({ size = 13, className }: P) => (<svg {...b(size, className)}><path d="M4 5h16v10H8l-4 4z" /></svg>)
export const IconDoc = ({ size = 13, className }: P) => (<svg {...b(size, className)}><path d="M7 3h7l4 4v14H7z" /></svg>)
export const IconBoxCheck = ({ size = 13, className }: P) => (<svg {...b(size, className)}><path d="M5 12l5 5L20 6" /></svg>)
export const IconReturn = ({ size = 13, className }: P) => (<svg {...b(size, className)}><path d="M7 11V6a3 3 0 016 0M5 11h11l-1 9H6z" /></svg>)
export const IconPerson = ({ size = 13, className }: P) => (<svg {...b(size, className)}><circle cx="9" cy="8" r="3" /><path d="M4 20a5 5 0 0110 0" /></svg>)
export const IconCart = ({ size = 14, className }: P) => (<svg {...b(size, className)}><circle cx="9" cy="20" r="1.4" /><circle cx="18" cy="20" r="1.4" /><path d="M3 4h2l2 12h11l2-8H6" /></svg>)
export const IconChart = ({ size = 14, className }: P) => (<svg {...b(size, className)}><path d="M4 20V10M10 20V4M16 20v-7M22 20H2" /></svg>)
export const IconBox = ({ size = 14, className }: P) => (<svg {...b(size, className)}><path d="M4 8l8-4 8 4-8 4z" /><path d="M4 8v8l8 4 8-4V8" /></svg>)
export const IconLock = ({ size = 20, className }: P) => (<svg {...b(size, className)} strokeWidth={1.9}><rect x="5" y="11" width="14" height="9" rx="2" /><path d="M8 11V8a4 4 0 018 0v3" /></svg>)
export const IconWrench = ({ size = 15, className }: P) => (<svg {...b(size, className)} strokeWidth={1.9}><path d="M14 7l-1.5-1.5a2 2 0 00-3 0L4 11l4 4 5.5-5.5a2 2 0 000-3z" /></svg>)
export const IconEye = ({ size = 15, className }: P) => (<svg {...b(size, className)} strokeWidth={1.9}><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z" /><circle cx="12" cy="12" r="2.5" /></svg>)
export const IconGear = ({ size = 15, className }: P) => (<svg {...b(size, className)} strokeWidth={1.9}><circle cx="12" cy="12" r="3" /><path d="M12 4v3M12 17v3M4 12h3M17 12h3" /></svg>)
