# 🤖 웰컴저축은행 뉴스 자동 검색 봇

매일 **06:00 ~ 20:00** 사이에 **2시간 간격**으로 "웰컴저축은행" 키워드로 네이버 뉴스를 자동 검색하여 이메일로 전송하는 봇입니다.

## ✨ 주요 기능

- 📰 네이버 뉴스 검색 API를 활용한 최신 뉴스 수집
- ⏰ 하루 8회 자동 실행 (06:00, 08:00, 10:00, 12:00, 14:00, 16:00, 18:00, 20:00)
- 🕐 최근 2시간 이내 발행된 기사만 필터링
- 🚫 중복 기사 자동 제거
- 📧 HTML 형식의 깔끔한 이메일 전송
- 🔄 GitHub Actions를 통한 완전 자동화 (서버 불필요)

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

### 1. GitHub 저장소 생성

1. GitHub에 새 저장소를 생성합니다 (public 또는 private)
2. 저장소 이름 예: `welcom-news-bot`

### 2. 코드 업로드

이 프로젝트의 모든 파일을 GitHub 저장소에 업로드합니다:

```bash
git init
git add .
git commit -m "Initial commit: 웰컴저축은행 뉴스봇"
git branch -M main
git remote add origin https://github.com/your-username/welcom-news-bot.git
git push -u origin main
```

### 3. GitHub Secrets 설정

GitHub 저장소에서 API 키와 비밀번호를 안전하게 저장합니다:

1. GitHub 저장소 페이지에서 **Settings** 클릭
2. 좌측 메뉴에서 **Secrets and variables** > **Actions** 클릭
3. **New repository secret** 버튼을 클릭하여 다음 4개의 시크릿을 추가:

| Name | Value | 설명 |
|------|-------|------|
| `NAVER_CLIENT_ID` | 네이버 Client ID | 네이버 개발자센터에서 발급받은 Client ID |
| `NAVER_CLIENT_SECRET` | 네이버 Client Secret | 네이버 개발자센터에서 발급받은 Client Secret |
| `GMAIL_USER` | Gmail 주소 | 발신자 Gmail 주소 (예: your-email@gmail.com) |
| `GMAIL_APP_PASSWORD` | Gmail 앱 비밀번호 | Gmail에서 발급받은 16자리 앱 비밀번호 (공백 제거) |

### 4. GitHub Actions 활성화

1. GitHub 저장소의 **Actions** 탭 클릭
2. **I understand my workflows, go ahead and enable them** 클릭
3. 워크플로우가 활성화되면 자동으로 스케줄에 따라 실행됩니다

## 🧪 테스트 실행

설정이 완료되면 즉시 테스트해볼 수 있습니다:

1. GitHub 저장소의 **Actions** 탭으로 이동
2. 좌측에서 **웰컴저축은행 뉴스 자동 검색** 워크플로우 클릭
3. 우측 상단의 **Run workflow** 버튼 클릭
4. **Run workflow** 확인 버튼 클릭
5. 워크플로우가 실행되고 몇 분 후 이메일이 도착합니다

## 📊 실행 스케줄

| 한국 시간 (KST) | UTC 시간 | 비고 |
|----------------|----------|------|
| 06:00 | 21:00 (전날) | 아침 첫 뉴스 |
| 08:00 | 23:00 (전날) | |
| 10:00 | 01:00 | |
| 12:00 | 03:00 | 점심 시간 |
| 14:00 | 05:00 | |
| 16:00 | 07:00 | |
| 18:00 | 09:00 | 퇴근 시간 |
| 20:00 | 11:00 | 저녁 마지막 뉴스 |

> GitHub Actions는 UTC 시간 기준으로 동작하므로 스케줄이 UTC로 설정되어 있습니다.

## 📁 프로젝트 구조

```
welcom-news-bot/
├── .github/
│   └── workflows/
│       └── news_search.yml    # GitHub Actions 워크플로우
├── news_bot.py                # 메인 Python 스크립트
├── requirements.txt           # Python 의존성 패키지
└── README.md                  # 이 파일
```

## 🛠️ 커스터마이징

### 검색 키워드 변경

`news_bot.py` 파일의 `keyword` 변수를 수정하세요:

```python
# 기본값
keyword = "웰컴저축은행"

# 변경 예시
keyword = "삼성전자"
```

### 시간 간격 변경

`news_bot.py`의 `filter_recent_news` 함수에서 `hours` 파라미터를 조정:

```python
# 기본값 (2시간)
recent_news = NewsFilter.filter_recent_news(all_news, hours=2)

# 변경 예시 (1시간)
recent_news = NewsFilter.filter_recent_news(all_news, hours=1)
```

### 실행 시간 변경

`.github/workflows/news_search.yml` 파일의 `cron` 스케줄을 수정:

```yaml
schedule:
  # 예: 매일 오전 9시 (KST) = UTC 00:00
  - cron: '0 0 * * *'
```

### 이메일 수신자 변경

`news_bot.py` 파일 또는 GitHub Actions 워크플로우의 `TO_EMAIL` 환경 변수를 수정:

```python
# news_bot.py에서 직접 변경
to_email = os.getenv("TO_EMAIL", "new-email@example.com")
```

또는 GitHub Actions 워크플로우에서:

```yaml
env:
  TO_EMAIL: "new-email@example.com"
```

## 🔍 문제 해결

### 이메일이 오지 않는 경우

1. **GitHub Actions 실행 로그 확인**
   - Actions 탭에서 워크플로우 실행 로그를 확인
   - 빨간색 X 표시가 있다면 에러 메시지 확인

2. **Secrets 확인**
   - Settings > Secrets에서 모든 값이 제대로 입력되었는지 확인
   - Gmail 앱 비밀번호에 공백이 없는지 확인

3. **스팸 메일함 확인**
   - Gmail의 스팸 메일함을 확인
   - 스팸이 아님으로 표시하여 향후 받은편지함으로 수신

### API 호출 제한

네이버 검색 API는 일일 25,000건, 초당 10건의 호출 제한이 있습니다. 이 봇은 하루 8회만 호출하므로 제한에 걸릴 걱정은 없습니다.

### GitHub Actions 실행이 안 되는 경우

1. **Public 저장소**: 무료로 무제한 사용 가능
2. **Private 저장소**: 무료 계정은 월 2,000분 제한 (이 봇은 하루에 약 5분 사용)

## 📧 이메일 형식

이메일은 다음과 같은 정보를 포함합니다:

- 📰 검색 키워드와 검색 시간
- 📊 새로운 기사 개수
- 각 기사별:
  - 제목 (클릭 가능한 링크)
  - 요약 내용
  - 발행 시간

## 📝 라이선스

이 프로젝트는 자유롭게 사용 가능합니다.

## 🙋‍♂️ 문의

문제가 발생하거나 개선 아이디어가 있다면 GitHub Issues를 통해 문의해주세요.

---

**Made with ❤️ by Claude**
