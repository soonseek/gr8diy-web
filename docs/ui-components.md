# UI 컴포넌트 (UI Components)

## 개요
shadcn/ui 패턴을 기반으로 CVA(class-variance-authority)를 사용하여 변형 시스템을 구현한 재사용 가능한 컴포넌트들입니다.

## Button 컴포넌트
```typescript
variants: {
  variant: {
    default: "bg-primary text-primary-foreground",
    destructive: "bg-destructive text-destructive-foreground",
    outline: "border border-input",
    ghost: "hover:bg-accent",
    link: "text-primary underline-offset-4"
  },
  size: {
    default: "h-10 px-4 py-2",
    sm: "h-9 px-3",
    lg: "h-11 px-8",
    icon: "h-10 w-10"
  }
}
```

## Card 컴포넌트
- Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter
- 조합 가능한 하위 컴포넌트 구조
- 일관된 padding과 border radius

## Input 컴포넌트
- 기본 HTML input의 래퍼
- Tailwind 클래스로 스타일링
- file, number 등 타입 지원

## 홈페이지 컴포넌트
### Header
- 고정 포지션, 블러 배경
- 로고, 네비게이션, CTA 버튼
- 모바일 햄버거 메뉴

### Hero
- 프롬프트 입력 폼
- 예시 프롬프트 버튼 (배송, 맛집, 투자)
- 그라데이션 배경 애니메이션

### HowItWorks
- 4단계 카드 레이아웃
- 아이콘 + 제목 + 설명
- 데스크톱 연결선 애니메이션

### Gallery
- 카테고리 탭 (전체, 모멘텀, 평균 회귀 등)
- 알고리즘 카드 (차트, 수익률, 작성자)
- Mock 데이터 6개

## 주요 파일
- `apps/web/src/components/ui/button.tsx`
- `apps/web/src/components/ui/card.tsx`
- `apps/web/src/components/home/`
