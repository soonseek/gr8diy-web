# 사용자 관리 (User Management)

관리자의 사용자 관리 기능 명세입니다.

---

## 1. 개요

### 1.1 기능

- **가입 승인** (개발 서버)
- **사용자 활성/비활성**
- **권한 변경 (Superuser 부여)**
- **사용자 정보 조회**

### 1.2 환경별 동작

| 환경 | 가입 승인 | 설명 |
|------|-----------|------|
| **개발 서버** | 필요 (MANUAL_APPROVAL) | 관리자 승인 후 로그인 가능 |
| **운영 서버** | 불필요 (PUBLIC) | 즉시 가입 가능 |

---

## 2. 데이터 모델

### 2.1 users 테이블 관련 컬럼

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID | PK |
| email | VARCHAR(255) | 이메일 |
| full_name | VARCHAR(100) | 이름 |
| is_active | BOOLEAN | 활성화 여부 |
| is_superuser | BOOLEAN | 관리자 여부 |
| is_approved | BOOLEAN | **가입 승인 여부** (개발 서버 전용) |
| created_at | TIMESTAMPTZ | 생성 일시 |

---

## 3. API 명세

### 3.1 사용자 목록 조회

```python
# apps/api/app/api/v1/admin/users.py
@router.get("/users", response_model=list[schemas.UserOut])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
    is_active: bool | None = None,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    사용자 목록 조회

    Query Parameters:
    - skip: 건너뛸 레코드 수 (페이지네이션)
    - limit: 최대 반환 레코드 수
    - search: 이메일/이름 검색
    - is_active: 활성 사용자 필터

    Returns:
    - list[UserOut]: 사용자 목록
    """
```

### 3.2 사용자 상세 조회

```python
@router.get("/users/{user_id}", response_model=schemas.UserOut)
async def get_user(
    user_id: UUID,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    사용자 상세 조회

    Path Parameters:
    - user_id: 사용자 ID

    Returns:
    - UserOut: 사용자 상세 정보
    """
```

### 3.3 사용자 활성/비활성

```python
@router.patch("/users/{user_id}/activate")
async def toggle_user_active(
    user_id: UUID,
    is_active: bool,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    사용자 활성/비활성 토글

    Path Parameters:
    - user_id: 사용자 ID

    Request Body:
    - is_active: True (활성), False (비활성)

    Returns:
    - {success: bool, message: str}
    """
```

### 3.4 가입 승인 (개발 서버)

```python
@router.post("/users/{user_id}/approve")
async def approve_user(
    user_id: UUID,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    가입 승인 (개발 서버 전용)

    Path Parameters:
    - user_id: 사용자 ID

    Environment:
    - DEVELOPMENT: 작동
    - PRODUCTION: 무시 (항상 True)

    Returns:
    - {success: bool, message: str}
    """
    user = await user_service.get_user(db, user_id)

    if settings.ENVIRONMENT == "development":
        user.is_approved = True
        await db.commit()

        # 승인 이메일 발송
        await email_service.send_approval_email(user.email)

    return {"success": True, "message": "User approved"}
```

### 3.5 Superuser 권한 부여

```python
@router.post("/users/{user_id}/promote")
async def promote_to_superuser(
    user_id: UUID,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Superuser 권한 부여

    Path Parameters:
    - user_id: 사용자 ID

    Returns:
    - {success: bool, message: str}
    """
    user = await user_service.get_user(db, user_id)
    user.is_superuser = True
    await db.commit()

    return {"success": True, "message": "User promoted to superuser"}
```

---

## 4. 프론트엔드 연동

### 4.1 페이지 구조

```typescript
// app/admin/users/page.tsx
export default function AdminUsersPage() {
  return (
    <div className="container">
      <h1>사용자 관리</h1>

      {/* 검색 필터 */}
      <UserFilters />

      {/* 사용자 목록 테이블 */}
      <UserTable />

      {/* 페이지네이션 */}
      <Pagination />
    </div>
  );
}
```

### 4.2 사용자 목록 컴포넌트

```typescript
// components/admin/UserTable.tsx
"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function UserTable() {
  const { data: users, isLoading } = useQuery({
    queryKey: ["admin-users"],
    queryFn: () => api.get("/admin/users").then(r => r.data),
  });

  if (isLoading) return <div>Loading...</div>;

  return (
    <table>
      <thead>
        <tr>
          <th>이메일</th>
          <th>이름</th>
          <th>활성</th>
          <th>승인</th>
          <th>관리자</th>
          <th> actions</th>
        </tr>
      </thead>
      <tbody>
        {users?.map(user => (
          <tr key={user.id}>
            <td>{user.email}</td>
            <td>{user.full_name}</td>
            <td>{user.is_active ? "O" : "X"}</td>
            <td>{user.is_approved ? "O" : "X"}</td>
            <td>{user.is_superuser ? "O" : "X"}</td>
            <td>
              <ToggleButton
                checked={user.is_active}
                onChange={() => toggleActive(user.id)}
              />
              {" "}
              <ApproveButton
                userId={user.id}
                isApproved={user.is_approved}
              />
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

### 4.3 승인 버튼 (개발 서버)

```typescript
// components/admin/ApproveButton.tsx
"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function ApproveButton({
  userId,
  isApproved
}: {
  userId: string;
  isApproved: boolean;
}) {
  const queryClient = useQueryClient();

  const approveMutation = useMutation({
    mutationFn: () =>
      api.post(`/admin/users/${userId}/approve`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
    },
  });

  // 개발 서버에서만 표시
  if (process.env.NEXT_PUBLIC_APP_ENV !== "development") {
    return null;
  }

  return (
    <button
      onClick={() => approveMutation.mutate()}
      disabled={isApproved || approveMutation.isPending}
    >
      {isApproved ? "승인 완료" : "승인"}
    </button>
  );
}
```

---

## 5. 이메일 알림

### 5.1 승인 이메일

```python
# apps/api/app/services/email.py
async def send_approval_email(email: str):
    """
    가입 승인 이메일 발송

    Subject: [Great DIY] 가입 승인 완료

    Content:
    안녕하세요, {full_name}님!

    귀하의 가입이 승인되었습니다.
    아래 링크에서 로그인하실 수 있습니다:

    [로그인 버튼]

    감사합니다.
    Great DIY 팀
    """
    template = "email/approval.html"
    subject = "[Great DIY] 가입 승인 완료"

    await send_email(
        to=email,
        subject=subject,
        template=template,
        context={"login_url": f"{settings.FRONTEND_URL}/login"}
    )
```

---

## 6. 상위/관련 문서

- **[../index.md](../index.md)** - 관리자 기능 개요
- **[../../02-authentication/](../../02-authentication/)** - 인증 시스템
- **[../../06-data/specs/table-schemas.md](../../06-data/specs/table-schemas.md)** - users 테이블

---

*최종 업데이트: 2025-12-29*
