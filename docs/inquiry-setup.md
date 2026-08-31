# 문의 게시판 — Cloudflare 설정

문의 API는 **Pages Functions + D1** 을 사용합니다. 아래를 한 번만 설정하면 됩니다.

## 1. D1 데이터베이스 생성

Cloudflare 대시보드 → **Workers & Pages** → **D1** → **Create database**

- 이름: `jdmedical-inquiries`
- Database ID: `3b224df5-1c5d-4858-a5b3-5b881bdf4468`

생성 후 **Database ID**를 복사해 `wrangler.toml`의 `database_id`에 넣습니다.

또는 터미널:

```bash
npx wrangler d1 create jdmedical-inquiries
npx wrangler d1 execute jdmedical-inquiries --remote --file=./migrations/0001_inquiries.sql
```

(테이블은 API 첫 호출 시 자동 생성되므로 migrate는 선택 사항입니다.)

## 2. Pages 프로젝트에 D1 바인딩

**Workers & Pages** → **jdmedical-site** → **Settings** → **Bindings** → **Add** → **D1 database**

| Variable name | Database        |
|---------------|-----------------|
| `DB`          | jdmedical-inquiries |

저장 후 재배포합니다.

## 3. 관리자 비밀번호

**Settings** → **Environment variables** (Production)

| Name             | Value              |
|------------------|--------------------|
| `ADMIN_PASSWORD` | 원하는 관리자 비번 |

- 비밀글 열람·삭제(X 버튼)에 사용됩니다.
- 사이트 코드에는 포함되지 않습니다.

## 4. 스팸 방지 (기본 적용됨)

별도 설정 없이 아래가 동작합니다.

- 숨김 필드(허니팟) — 봇이 채우면 무시
- 작성 시간 검증 — 페이지 로드 후 3초 미만 제출 차단
- IP 기준 속도 제한 — 1시간에 최대 5건

### (선택) Cloudflare Turnstile

더 강한 봇 차단이 필요하면 **Turnstile** 위젯을 추가합니다.

**Settings** → **Environment variables**

| Name | Value |
|------|-------|
| `TURNSTILE_SITE_KEY` | Turnstile 사이트 키 |
| `TURNSTILE_SECRET_KEY` | Turnstile 비밀 키 |

Turnstile은 Cloudflare 대시보드 → **Turnstile** → **Add site** → 도메인 `jdmedical.co.kr` 로 생성합니다.

## 5. 배포

```bash
cd site
npx wrangler pages deploy . --project-name=jdmedical-site
```

## API

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/inquiries` | 목록 (비밀글은 제목·이름만) |
| POST | `/api/inquiries` | 글 등록 |
| POST | `/api/inquiries/:id` | 비밀글 비밀번호 확인 |
| DELETE | `/api/inquiries/:id` | 관리자 비번으로 삭제 |
