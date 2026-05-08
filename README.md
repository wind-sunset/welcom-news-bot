# 🤖 웰컴저축은행 뉴스 자동 검색 봇

매일 **06:00 ~ 20:00** (KST) 사이에 **30분 간격**으로 "웰컴저축은행" 키워드로 네이버 뉴스를 자동 검색하여 이메일로 전송합니다.

## ✨ 주요 기능

- 📰 네이버 뉴스 검색 API를 활용한 최신 뉴스 수집
- ⏰ 하루 29회 자동 실행 (06:00 ~ 20:00, 30분 간격)
- 🕐 최근 1시간 이내 발행된 기사만 필터링 (`FILTER_HOURS` 환경 변수로 조정 가능)
- 🤖 AI 기반 카테고리 자동 분류 및 요약
- 🔑 TF-IDF 기반 주요 키워드 자동 추출
- 🚫 코사인 유사도 기반 중복 기사 자동 제거
- 📧 HTML 형식의 깔끔한 이메일 전송
- 🔄 GitHub Actions를 통한 완전 자동화 (서버 불필요)
- 🔁 API 장애 시 지수 백오프 자동 재시도 (최대 4회)

## 📋 사전 준비사항

### 1. 네이버 검색 API 키 발급

1. [네이버 개발자 센터](https://developers.naver.com/main/) 접속
2. 로그인 후 **애플리케이션 등록**
3. **애플리케이션 이름**: 원하는 이름 입력 (예: 뉴스검색봇)
4. **사용 API**: **검색** 선택
5. **비로그인 오픈API 서비스 환경**:
   - 웹 서비스 URL: `http://localhost` (임의로 입력 가능)
6. 등록 완료 후 **Client ID**와 **Client Secret** 복사

### 2. Gmail 앱 비밀번호 발급

Gmail에서 2단계 인증이 활성화되어 있어야 합니다.

1. [Google 계정 관리](https://myaccount.google.com/) 접속
2. **보안** 메뉴 클릭
3. **Google에 로그인** 섹션에서 **앱 비밀번호** 클릭
4. 앱 선택: **메일**, 기기 선택: **기타** (사용자 지정 이름 입력 가능)
5. **생성** 클릭 후 16자리 비밀번호 복사 (공백 제거)

> **참고**: 앱 비밀번호가 보이지 않는다면 2단계 인증을 먼저 활성화해야 합니다.

## 🚀 설정 방법

### 1. GitHub Secrets 설정

GitHub 저장소의 **Settings → Secrets and variables → Actions**에서 아래 5개의 Secret을 추가합니다.

| Name | Value | 설명 |
|------|-------|------|
| `NAVER_CLIENT_ID` | 네이버 Client ID | 네이버 개발자센터에서 발급 |
| `NAVER_CLIENT_SECRET` | 네이버 Client Secret | 네이버 개발자센터에서 발급 |
| `GMAIL_USER` | Gmail 주소 | 발신자 Gmail 주소 |
| `GMAIL_APP_PASSWORD` | Gmail 앱 비밀번호 | 16자리 앱 비밀번호 (공백 제거) |
| `TO_EMAIL` | 수신자 이메일 | 쉼표로 구분하여 여러 명 입력 가능 (예: `a@gmail.com,b@gmail.com`) |

### 2. GitHub Actions 활성화

1. GitHub 저장소의 **Actions** 탭 클릭
2. **I understand my workflows, go ahead and enable them** 클릭
3. 워크플로우가 활성화되면 스케줄에 따라 자동 실행됩니다

## 🧪 테스트 실행

1. GitHub 저장소의 **Actions** 탭으로 이동
2. 좌측에서 **웰컴저축은행 뉴스 자동 검색** 워크플로우 클릭
3. 우측 상단의 **Run workflow** 버튼 클릭
4. 몇 분 후 이메일이 도착합니다

## 📊 실행 스케줄

30분 간격, KST 06:00 ~ 20:00 (하루 29회)

| 구간 (KST) | cron (UTC) |
|------------|------------|
| 06:00 ~ 08:30 | `0,30 21-23 * * *` |
| 09:00 ~ 19:30 | `0,30 0-10 * * *` |
| 20:00 | `0 11 * * *` |

> GitHub Actions는 UTC 기준으로 동작합니다.

## 📁 프로젝트 구조

```
welcom-news-bot/
├── .github/
│   └── workflows/
│       └── news_search.yml    # GitHub Actions 워크플로우
├── .backup/                   # 원본 파일 백업
├── news_bot.py                # 메인 Python 스크립트
├── requirements.txt           # Python 의존성 패키지
└── README.md                  # 이 파일
```

## 🛠️ 커스터마이징

### 검색 키워드 변경

`news_bot.py`의 `keyword` 변수를 수정하세요:

```python
keyword = "웰컴저축은행"  # 원하는 키워드로 변경
```

### 필터 시간 범위 변경

워크플로우 파일의 `FILTER_HOURS` 값을 조정합니다 (기본값: `1`시간):

```yaml
env:
  FILTER_HOURS: '1'   # 최근 1시간 이내 기사만 수집
```

### 수신자 변경

GitHub Secrets의 `TO_EMAIL` 값을 수정합니다. 쉼표로 구분하면 여러 명에게 동시 발송됩니다:

```
a@gmail.com,b@company.com
```

## 🔍 문제 해결

### 이메일이 오지 않는 경우

1. **Actions 실행 로그 확인** — Actions 탭에서 빨간 X가 있으면 에러 메시지 확인
2. **Secrets 확인** — 5개 Secret이 모두 올바르게 입력되었는지 확인
3. **스팸 메일함 확인** — Gmail 스팸함을 확인하고 스팸 아님으로 표시

### API 호출 제한

네이버 검색 API는 일일 25,000건 제한입니다. 이 봇은 하루 29회 호출하므로 제한에 걸리지 않습니다.

### GitHub Actions 실행 제한

- **Public 저장소**: 무료 무제한
- **Private 저장소**: 무료 계정 월 2,000분 제한 (이 봇은 하루 약 15분 사용)

## 📧 이메일 형식

각 이메일에는 다음 정보가 포함됩니다:

- 검색 시각 및 필터 시간 범위
- 수집된 기사 건수
- 🔑 AI 추출 주요 키워드
- 각 기사별: 제목(링크), AI 카테고리, AI 요약, 원문 설명, 발행 시간

## 📝 라이선스

이 프로젝트는 자유롭게 사용 가능합니다.

---

**Made with ❤️ by Claude**
