# JD Medical Site

주식회사 제이디메디컬 공식 웹사이트 및 브랜드 작업 저장소입니다.

## 구조

| 경로 | 설명 |
|------|------|
| `site/` | Cloudflare Pages에 배포되는 웹사이트 (KO / EN / CN) |
| `logo/` | 로고 벡터·PNG 원본 |
| `print/` | 간판·시트지 출력 PDF |
| `sign/` | 제품/모토 카탈로그 PDF 원본 |
| `tools/` | 로고·인쇄 제작용 스크립트 및 임시 산출물 |
| `docs/` | 작업 계획 문서 |

## 로컬 미리보기

```bash
npx serve site -l 5173
```

## 배포

```bash
npx wrangler pages deploy site --project-name=jdmedical-site
```

사이트: https://jdmedical.co.kr/

## SEO

- `site/robots.txt`
- `site/sitemap.xml`
- Open Graph 이미지: `site/images/og-cover.jpg`
