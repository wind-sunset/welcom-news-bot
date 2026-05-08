#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
웰컴저축은행 뉴스 자동 검색 및 이메일 전송 봇 (AI 강화 버전)
30분 간격으로 최신 뉴스를 검색하여 이메일로 전송합니다.
- 자동 키워드 추출
- 스마트 요약
- 개선된 중복 제거
"""

import html
import logging
import os
import sys
import requests
import smtplib
import re
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Tuple, Optional
import json

# AI/ML 라이브러리
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class NaverNewsSearcher:
    """네이버 뉴스 검색 API 클라이언트"""

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_url = "https://openapi.naver.com/v1/search/news.json"

    def search_news(self, keyword: str, display: int = 100, sort: str = "date") -> List[Dict]:
        """
        뉴스 검색 수행 (실패 시 지수 백오프 재시도)

        Args:
            keyword: 검색 키워드
            display: 검색 결과 수 (최대 100)
            sort: 정렬 방식 (date: 날짜순, sim: 유사도순)

        Returns:
            검색된 뉴스 리스트
        """
        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret
        }

        params = {
            "query": keyword,
            "display": display,
            "sort": sort
        }

        max_retries = 4
        delay = 2
        for attempt in range(1, max_retries + 1):
            try:
                response = requests.get(self.api_url, headers=headers, params=params, timeout=10)
                response.raise_for_status()
                return response.json().get("items", [])
            except requests.exceptions.RequestException as e:
                logger.warning("API 요청 실패 (시도 %d/%d): %s", attempt, max_retries, e)
                if attempt < max_retries:
                    time.sleep(delay)
                    delay *= 2

        logger.error("API 요청 최대 재시도 초과. 빈 결과 반환.")
        return []


class NewsAI:
    """AI 기반 뉴스 분석 클래스"""

    # 카테고리별 키워드 정의
    CATEGORY_KEYWORDS = {
        "💰 금융": ["금융", "은행", "대출", "적금", "예금", "금리", "이자", "저축", "투자", "펀드", "주식", "채권"],
        "🏢 기업": ["기업", "회사", "사업", "경영", "CEO", "임원", "지점", "영업", "매출", "실적"],
        "💳 금융상품": ["상품", "카드", "보험", "연금", "ISA", "CMA", "청약", "통장"],
        "📊 부동산": ["부동산", "아파트", "주택", "건물", "분양", "입주", "임대"],
        "⚖️ 규제": ["금감원", "규제", "제재", "법원", "판결", "소송", "처벌", "과징금", "검찰", "경찰"],
        "🔧 IT": ["IT", "디지털", "앱", "모바일", "시스템", "플랫폼", "AI", "빅데이터"],
        "👥 인사": ["인사", "임명", "발령", "승진", "신임", "취임"],
        "📈 실적": ["실적", "수익", "손실", "영업이익", "순이익", "매출", "분기"],
    }

    @staticmethod
    def clean_text(text: str) -> str:
        """HTML 태그 제거 및 엔티티 디코딩"""
        tag_removed = re.sub(r'<[^>]+>', '', text)
        return html.unescape(tag_removed)

    @staticmethod
    def categorize_news(news: Dict) -> str:
        """
        뉴스 카테고리 자동 분류

        Args:
            news: 뉴스 딕셔너리

        Returns:
            카테고리 문자열
        """
        title = NewsAI.clean_text(news.get("title", "")).lower()
        description = NewsAI.clean_text(news.get("description", "")).lower()
        full_text = f"{title} {description}"

        scores = {}
        for category, keywords in NewsAI.CATEGORY_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword.lower() in full_text)
            if score > 0:
                scores[category] = score

        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        return "📰 일반"

    @staticmethod
    def extract_keywords(news_list: List[Dict], top_n: int = 5) -> List[Tuple[str, float]]:
        """
        TF-IDF를 사용한 키워드 추출

        Args:
            news_list: 뉴스 리스트
            top_n: 추출할 상위 키워드 개수

        Returns:
            (키워드, 점수) 튜플 리스트
        """
        if not news_list:
            return []

        texts = [
            f"{NewsAI.clean_text(n.get('title', ''))} {NewsAI.clean_text(n.get('description', ''))}"
            for n in news_list
        ]

        try:
            vectorizer = TfidfVectorizer(
                max_features=100,
                token_pattern=r'(?u)\b\w+\b',
                min_df=1,
                max_df=0.8
            )

            tfidf_matrix = vectorizer.fit_transform(texts)
            feature_names = vectorizer.get_feature_names_out()
            avg_scores = np.asarray(tfidf_matrix.mean(axis=0)).flatten()

            top_indices = avg_scores.argsort()[-top_n * 2:][::-1]
            keywords = [(feature_names[i], float(avg_scores[i])) for i in top_indices if len(feature_names[i]) > 1]

            return keywords[:top_n]

        except Exception as e:
            logger.warning("키워드 추출 실패: %s", e)
            return []

    @staticmethod
    def simple_summarize(text: str, max_sentences: int = 2) -> str:
        """
        간단한 문장 추출 기반 요약

        Args:
            text: 요약할 텍스트
            max_sentences: 최대 문장 수

        Returns:
            요약된 텍스트
        """
        if not text:
            return ""

        sentences = re.split(r'[.!?]\s+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

        if not sentences:
            return text[:100] + "..." if len(text) > 100 else text

        summary_sentences = sentences[:max_sentences]
        result = " ".join(summary_sentences)
        if not result.endswith('.'):
            result += "."
        return result

    @staticmethod
    def calculate_similarity_matrix(news_list: List[Dict]) -> np.ndarray:
        """
        뉴스 간 유사도 매트릭스 계산

        Args:
            news_list: 뉴스 리스트

        Returns:
            유사도 매트릭스 (n x n)
        """
        if not news_list:
            return np.array([])

        texts = [
            f"{NewsAI.clean_text(n.get('title', ''))} {NewsAI.clean_text(n.get('description', ''))}"
            for n in news_list
        ]

        try:
            vectorizer = TfidfVectorizer(token_pattern=r'(?u)\b\w+\b')
            tfidf_matrix = vectorizer.fit_transform(texts)
            return cosine_similarity(tfidf_matrix)

        except Exception as e:
            logger.warning("유사도 계산 실패: %s", e)
            return np.eye(len(news_list))


class NewsFilter:
    """뉴스 필터링 및 중복 제거"""

    @staticmethod
    def filter_recent_news(news_list: List[Dict], hours: int = 2) -> List[Dict]:
        """
        최근 N시간 이내의 뉴스만 필터링

        Args:
            news_list: 뉴스 리스트
            hours: 필터링할 시간 범위

        Returns:
            필터링된 뉴스 리스트
        """
        KST = timezone(timedelta(hours=9))
        cutoff_time = datetime.now(KST) - timedelta(hours=hours)

        filtered_news = []

        for news in news_list:
            pub_date_str = news.get("pubDate", "")
            title = NewsAI.clean_text(news.get("title", ""))[:50]

            try:
                pub_date = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %z")
                if pub_date >= cutoff_time:
                    filtered_news.append(news)
                else:
                    logger.debug("오래된 기사 제외: %s... (%s)", title, pub_date_str)
            except (ValueError, AttributeError) as e:
                logger.warning("날짜 파싱 실패로 제외: %s / 오류: %s", pub_date_str, e)
                continue

        return filtered_news

    @staticmethod
    def remove_duplicates_smart(news_list: List[Dict], similarity_threshold: float = 0.7) -> List[Dict]:
        """
        유사도 기반 중복 제거

        Args:
            news_list: 뉴스 리스트
            similarity_threshold: 유사도 임계값 (0.0 ~ 1.0)

        Returns:
            중복이 제거된 뉴스 리스트
        """
        if not news_list:
            return []

        similarity_matrix = NewsAI.calculate_similarity_matrix(news_list)

        if similarity_matrix.size == 0:
            return news_list

        unique_indices = []
        removed_indices: set = set()

        for i in range(len(news_list)):
            if i in removed_indices:
                continue

            unique_indices.append(i)

            for j in range(i + 1, len(news_list)):
                if j in removed_indices:
                    continue
                if similarity_matrix[i][j] >= similarity_threshold:
                    removed_indices.add(j)
                    logger.debug("유사 기사 제거: '%s...'", NewsAI.clean_text(news_list[j]['title'][:30]))

        return [news_list[i] for i in unique_indices]


class EmailSender:
    """이메일 전송 클래스"""

    def __init__(self, gmail_user: str, gmail_password: str):
        self.gmail_user = gmail_user
        self.gmail_password = gmail_password
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587

    def send_news_email(
        self,
        to_email: str,
        news_list: List[Dict],
        keyword: str,
        keywords: Optional[List[Tuple[str, float]]] = None,
    ):
        """
        뉴스 결과를 이메일로 전송

        Args:
            to_email: 수신자 이메일 (쉼표로 구분 가능)
            news_list: 뉴스 리스트
            keyword: 검색 키워드
            keywords: 추출된 키워드 리스트
        """
        subject = f"[뉴스봇] {keyword} 최신 뉴스 ({len(news_list)}건)"
        body = self._create_email_body(news_list, keyword, keywords)

        msg = MIMEMultipart('alternative')
        msg['From'] = self.gmail_user
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'html', 'utf-8'))

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.gmail_user, self.gmail_password)
                server.send_message(msg)
            logger.info("이메일 전송 완료: %s", to_email)
        except Exception as e:
            logger.error("이메일 전송 실패: %s", e)
            raise

    def _render_keywords_section(self, keywords: Optional[List[Tuple[str, float]]]) -> str:
        if not keywords:
            return ""
        badges = " ".join(
            f'<span class="keyword-badge">{html.escape(kw)}</span>'
            for kw, _ in keywords[:5]
        )
        return f"""
        <div class="keywords-section">
            <strong>🔑 주요 키워드:</strong>
            <div style="margin-top: 10px;">{badges}</div>
        </div>
        """

    def _render_news_item(self, idx: int, news: Dict) -> str:
        title = NewsAI.clean_text(news.get("title", "제목 없음"))
        description = NewsAI.clean_text(news.get("description", ""))
        pub_date = NewsAI.clean_text(news.get("pubDate", "날짜 미상"))

        raw_link = news.get("link", "")
        link = raw_link if raw_link.startswith(("http://", "https://")) else "#"

        category = NewsAI.categorize_news(news)
        summary = NewsAI.simple_summarize(f"{title}. {description}", max_sentences=2)

        return f"""
        <div class="news-item">
            <div class="news-title">
                <strong>{idx}.</strong>
                <a href="{html.escape(link)}" target="_blank" rel="noopener noreferrer">{html.escape(title)}</a>
                <span class="category-badge">{category}</span>
            </div>
            <div class="news-summary">
                💡 <strong>AI 요약:</strong> {html.escape(summary)}
            </div>
            <div class="news-description">{html.escape(description)}</div>
            <div class="news-meta">
                <span>🕐 {html.escape(pub_date)}</span>
            </div>
        </div>
        """

    def _create_email_body(
        self,
        news_list: List[Dict],
        keyword: str,
        keywords: Optional[List[Tuple[str, float]]] = None,
    ) -> str:
        """이메일 본문 생성 (HTML 형식)"""
        KST = timezone(timedelta(hours=9))
        now = datetime.now(KST).strftime("%Y년 %m월 %d일 %H시 %M분")

        keywords_html = self._render_keywords_section(keywords)

        if news_list:
            news_html = "\n".join(self._render_news_item(i, n) for i, n in enumerate(news_list, 1))
        else:
            news_html = """
            <div class="no-news">
                <p>😴 최근 동안 새로운 기사가 없습니다.</p>
            </div>
            """

        filter_hours = int(os.getenv("FILTER_HOURS", "1"))

        return f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px;
                    margin-bottom: 20px;
                }}
                .header h1 {{ margin: 0; font-size: 28px; }}
                .header p {{ margin: 10px 0 0 0; opacity: 0.9; }}
                .summary {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                    border-left: 4px solid #667eea;
                }}
                .keywords-section {{
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                    border-left: 4px solid #ffa726;
                }}
                .keyword-badge {{
                    display: inline-block;
                    background: linear-gradient(135deg, #ffa726, #fb8c00);
                    color: white;
                    padding: 6px 14px;
                    border-radius: 20px;
                    font-size: 13px;
                    font-weight: 500;
                    margin: 4px;
                }}
                .news-item {{
                    background: white;
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    padding: 20px;
                    margin-bottom: 20px;
                }}
                .news-title {{
                    font-size: 18px;
                    font-weight: 600;
                    margin-bottom: 12px;
                    color: #1a1a1a;
                }}
                .news-title a {{
                    color: #667eea;
                    text-decoration: none;
                }}
                .news-title a:hover {{ text-decoration: underline; }}
                .news-summary {{
                    background: #f0f4ff;
                    padding: 12px;
                    border-radius: 6px;
                    color: #444;
                    margin-bottom: 10px;
                    font-size: 14px;
                    line-height: 1.6;
                    border-left: 3px solid #667eea;
                }}
                .news-description {{
                    color: #666;
                    margin-bottom: 10px;
                    line-height: 1.5;
                }}
                .news-meta {{ font-size: 13px; color: #999; }}
                .no-news {{
                    text-align: center;
                    padding: 60px 20px;
                    color: #999;
                    background: white;
                    border-radius: 8px;
                }}
                .footer {{
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #e0e0e0;
                    text-align: center;
                    color: #999;
                    font-size: 13px;
                }}
                .ai-badge {{
                    display: inline-block;
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    color: white;
                    padding: 4px 10px;
                    border-radius: 12px;
                    font-size: 11px;
                    font-weight: 600;
                    margin-left: 8px;
                }}
                .category-badge {{
                    display: inline-block;
                    background: #e3f2fd;
                    color: #1976d2;
                    padding: 4px 10px;
                    border-radius: 12px;
                    font-size: 12px;
                    font-weight: 500;
                    margin-left: 10px;
                    border: 1px solid #bbdefb;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📰 {html.escape(keyword)} 뉴스 알림 <span class="ai-badge">AI 강화</span></h1>
                <p>{now} 기준 최근 {filter_hours}시간 이내 뉴스</p>
            </div>

            <div class="summary">
                <strong>📊 검색 결과:</strong> 총 {len(news_list)}건의 새로운 기사가 발견되었습니다.
            </div>

            {keywords_html}
            {news_html}

            <div class="footer">
                <p>🤖 이 메일은 AI 기능이 강화된 뉴스봇이 자동으로 발송했습니다.</p>
                <p>매일 06:00 ~ 20:00 (KST), 30분 간격으로 뉴스를 검색합니다.</p>
            </div>
        </body>
        </html>
        """


def main():
    """메인 실행 함수"""
    logger.info("=" * 60)
    logger.info("웰컴저축은행 뉴스 검색 봇 시작 (AI 강화 버전)")
    logger.info("=" * 60)

    naver_client_id = os.getenv("NAVER_CLIENT_ID")
    naver_client_secret = os.getenv("NAVER_CLIENT_SECRET")
    gmail_user = os.getenv("GMAIL_USER")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD")
    to_email = os.getenv("TO_EMAIL")

    missing_vars = [
        name for name, val in [
            ("NAVER_CLIENT_ID", naver_client_id),
            ("NAVER_CLIENT_SECRET", naver_client_secret),
            ("GMAIL_USER", gmail_user),
            ("GMAIL_APP_PASSWORD", gmail_password),
            ("TO_EMAIL", to_email),
        ] if not val
    ]

    if missing_vars:
        logger.error("필수 환경 변수가 설정되지 않았습니다: %s", ", ".join(missing_vars))
        sys.exit(1)

    keyword = "웰컴저축은행"
    filter_hours = int(os.getenv("FILTER_HOURS", "1"))

    logger.info("검색 키워드: %s", keyword)
    logger.info("수신 이메일: %s", to_email)
    logger.info("실행 시간: %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    logger.info("필터 시간 범위: 최근 %d시간", filter_hours)

    # 1. 네이버 뉴스 검색
    logger.info("1️⃣  네이버 뉴스 검색 중...")
    searcher = NaverNewsSearcher(naver_client_id, naver_client_secret)
    all_news = searcher.search_news(keyword, display=100)
    logger.info("   API에서 %d건 조회", len(all_news))

    # 2. 최근 N시간 이내 뉴스 필터링
    logger.info("2️⃣  최근 %d시간 이내 뉴스 필터링 중...", filter_hours)
    recent_news = NewsFilter.filter_recent_news(all_news, hours=filter_hours)
    logger.info("   %d건의 최근 뉴스 발견", len(recent_news))

    # 3. AI 기반 중복 제거
    logger.info("3️⃣  AI 기반 중복 기사 제거 중...")
    unique_news = NewsFilter.remove_duplicates_smart(recent_news, similarity_threshold=0.7)
    logger.info("   중복 제거 후 %d건", len(unique_news))

    # 4. AI 키워드 추출
    logger.info("4️⃣  AI 키워드 추출 중...")
    keywords = NewsAI.extract_keywords(unique_news, top_n=5)
    if keywords:
        logger.info("   추출된 키워드: %s", ", ".join(kw for kw, _ in keywords))
    else:
        logger.warning("   키워드 추출 실패 (기사 없음)")

    # 5. 이메일 전송
    if not unique_news:
        logger.info("새로운 기사가 없어 이메일 전송을 건너뜁니다.")
    else:
        logger.info("5️⃣  이메일 전송 중...")
        sender = EmailSender(gmail_user, gmail_password)
        sender.send_news_email(to_email, unique_news, keyword, keywords)

    logger.info("=" * 60)
    logger.info("작업 완료!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
