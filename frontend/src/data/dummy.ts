import type { RecentChat } from '../types'

// 화면 전용 더미 데이터입니다. 실제 응답은 lib/api.ts가 FastAPI /agent/message에서 받아옵니다.
export const CURRENT_USER = { name: '김연세', team: 'Personal AI', initial: '김' }

export const RECENT_CHATS: RecentChat[] = [
  { id: 'c1', title: '항공권 예약 메일 찾기', time: '14:35' },
  { id: 'c2', title: '구독 결제 내역 정리', time: '14:20' },
  { id: 'c3', title: '보험 청구서 요약', time: '13:48' },
  { id: 'c4', title: '연락처 공유 요청 검사', time: '13:30' },
  { id: 'c5', title: '캘린더 일정 추가', time: '12:15' },
]

export const QUICK_ACTIONS = [
  '내 항공권 예약 메일 찾아줘',
  '이번 달 구독 결제 내역 정리해줘',
  '보험 청구서 PDF 요약해줘',
]
