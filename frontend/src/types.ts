// AI Client 공용 타입 (STEP2: 더미 데이터 전용 — 백엔드 계약과 필드명은 맞춰둠)

export type Decision = 'ALLOW' | 'MASK' | 'BLOCK' | 'NEED_APPROVAL'
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | 'OFF'

/** 하단 실시간 검사 파이프라인 5단계 */
export const SCAN_STAGES = [
  { key: 'prompt', label: '입력 프롬프트 검사', sub: '위험 탐지' },
  { key: 'policy', label: '정책 및 권한 검토', sub: '접근 제어' },
  { key: 'tool', label: '외부 도구 실행 통제', sub: '도구 검증' },
  { key: 'content', label: 'AI 응답 콘텐츠 검사', sub: '응답 검증' },
  { key: 'safe', label: '안전한 응답 제공', sub: '완료 대기' },
] as const

/** 우측 Protection 레일 검사 항목 */
export const RAIL_STAGES = [
  { key: 'prompt', name: '입력 프롬프트 검사', desc: '위험 키워드, 악성 패턴, 인젝션 탐지', lat: '12ms' },
  { key: 'policy', name: '정책 매칭', desc: '정책 규칙 매칭, R0-RB 검증', lat: '18ms' },
  { key: 'permission', name: '권한 확인', desc: '사용자 권한, RBAC 검증', lat: '9ms' },
  { key: 'tool', name: '도구 실행 통제', desc: '도구 사용 적합성 검증', lat: '21ms' },
  { key: 'output', name: '출력 검사', desc: '응답 유해성, 개인정보, 데이터 유출 검사', lat: '15ms' },
] as const

/** 한 요청의 검사 결과(더미). 실제 연동 STEP에서 /agent/message 응답으로 교체 예정. */
export interface ScanResult {
  decision: Decision
  riskLevel: RiskLevel
  riskScore: number
  reason: string
  body: string
  reachedStage: number       // 파이프라인에서 마지막으로 도달한 단계 index (0~4)
  blockedAtReached: boolean   // 마지막 단계가 '차단'으로 멈춤 → 빨강
  injection?: boolean
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  text: string
  result?: ScanResult
}

export interface RecentChat {
  id: string
  title: string
  time: string
}
