import streamlit as st
import google.generativeai as genai
import streamlit.components.v1 as components

# 1. 🚨 보안 시스템: 금고(Secrets)에서 API 키 불러오기
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except Exception:
    st.error("보안 금고(Secrets)에 API 키가 설정되지 않았습니다. 관리자 설정에서 키를 입력해주세요.")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY)

# 페이지 기본 설정
st.set_page_config(page_title="위드멤버 종합 진단기", page_icon="📊", layout="wide")

st.title("📊 위드멤버 종합 플레이스 & 리뷰 진단기")
st.markdown("네이버 플레이스 도구 누락 현상과 리뷰 평판 및 매출 성장을 한 번에 정밀 진단합니다.")

# 2. 통합 폼 입력
with st.form("comprehensive_diagnostic_form"):
    st.subheader("📋 1. 매장 종합 정보")
    col1, col2 = st.columns(2)
    with col1:
        place_name = st.text_input("매장명 (플레이스 등록 이름)", placeholder="예: 정가네 부평점")
        target_area = st.text_input("타겟 지역명", placeholder="예: 부평동")
        visit_reviews = st.number_input("현재 방문자 리뷰 수", min_value=0, step=1)
    with col2:
        main_menu = st.text_input("핵심 메뉴/업종", placeholder="예: 삼겹살, 정육식당")
        current_keywords = st.text_input("현재 등록된 키워드(태그)", placeholder="예: 부평맛집, 고기집")
        blog_reviews = st.number_input("현재 블로그 리뷰 수", min_value=0, step=1)
    
    st.markdown("---")
    st.subheader("🛠️ 2. 네이버 플레이스 도구 세팅 여부 (체크)")
    st.caption("현재 사장님 매장에 활성화되어 있는 도구만 체크해 주세요.")
    col_t1, col_t2, col_t3, col_t4 = st.columns(4)
    with col_t1: use_booking = st.checkbox("📅 네이버 예약")
    with col_t2: use_talktalk = st.checkbox("💬 네이버 톡톡")
    with col_t3: use_coupon = st.checkbox("🎟️ 네이버 쿠폰")
    with col_t4: use_safecall = st.checkbox("📞 안심번호(스마트콜)")
    
    submitted = st.form_submit_button("🚀 종합 정밀 진단 및 리포트 생성")

# 3. 진단 실행 및 리포트 생성
if submitted:
    if not place_name or not target_area or not main_menu:
        st.error("매장명, 타겟 지역명, 핵심 메뉴는 필수입니다.")
    else:
        with st.spinner("AI가 데이터를 종합 분석 중입니다..."):
            
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            # [기존 로직 1] 플레이스 진단 데이터 준비
            def get_status_html(is_used):
                return '<span style="color: #38a169; font-weight: 800;">등록</span>' if is_used else '<span style="color: #e53e3e; font-weight: 800;">미등록</span>'

            tool_status_text = f"예약({'등록' if use_booking else '미등록'}), 톡톡({'등록' if use_talktalk else '미등록'}), 쿠폰({'등록' if use_coupon else '미등록'}), 안심번호({'등록' if use_safecall else '미등록'})"
            display_status = f"예약({get_status_html(use_booking)}), 톡톡({get_status_html(use_talktalk)}), 쿠폰({get_status_html(use_coupon)}), 안심번호({get_status_html(use_safecall)})"
            
            prompt1 = f"""
            너는 10년 경력의 네이버 플레이스 마케팅 전문 컨설턴트야.
            아래 6개의 구분자(###)를 사용하여, 특수기호나 HTML 태그 없이 오직 전문적인 '순수 텍스트'로만 간결하게 작성해.
            ###SEO_SCORE###, ###SEO_RANK###, ###PROBLEM###, ###EFFECT###, ###COMPETITOR_COUNT###, ###COMPETITION### 순서대로 작성해.

            [입력 데이터]
            - 플레이스 등록명: {place_name}
            - 상권: {target_area} / 업종: {main_menu}
            - 네이버 공식 도구 세팅 현황: {tool_status_text}
            - 리뷰: 방문자 {visit_reviews}개 / 블로그 {blog_reviews}개
            """

            # [기존 로직 2] 리뷰 평판 및 매출 예측 준비
            prompt2 = f"""
            너는 대한민국 최고의 소상공인 마케팅 전략가야.
            아래 데이터를 바탕으로 사장님께 드리는 '리뷰 평판 진단 리포트'를 작성해.
            HTML 태그를 적절히 사용해서 시각적으로 강조해줘. 오직 구분자(###)를 사용해서 답해.

            ###VISIT_DIAG###, ###VISIT_IMPROVE###, ###AI_REPLY###, ###BLOG_DIAG###, ###BLOG_IMPROVE###, ###PROFIT_PREDICT###, ###CONCLUSION### 순서대로 작성해.

            [입력 데이터]
            - 매장명: {place_name} ({main_menu})
            - 방문자 리뷰: {visit_reviews}개
            - 블로그 리뷰: {blog_reviews}개
            """

            try:
                # API 호출
                response1 = model.generate_content(prompt1)
                res_text1 = response1.text
                
                response2 = model.generate_content(prompt2)
                res_text2 = response2.text

                # 결과 파싱 함수
                def get_val1(tag, next_tag=None):
                    try:
                        part = res_text1.split(tag)[1]
                        return part.split(next_tag)[0].strip() if next_tag else part.strip()
                    except: return "분석 중..."

                def get_val2(tag, next_tag=None):
                    try:
                        p = res_text2.split(tag)[1]
                        return p.split(next_tag)[0].strip() if next_tag else p.strip()
                    except: return "분석 중..."

                # 1번 리포트 데이터
                score = get_val1("###SEO_SCORE###", "###SEO_RANK###")
                rank = get_val1("###SEO_RANK###", "###PROBLEM###")
                problem = get_val1("###PROBLEM###", "###EFFECT###")
                effect = get_val1("###EFFECT###", "###COMPETITOR_COUNT###")
                competitor_count = get_val1("###COMPETITOR_COUNT###", "###COMPETITION###")
                competition = get_val1("###COMPETITION###")

                # 2번 리포트 데이터
                v_diag = get_val2("###VISIT_DIAG###", "###VISIT_IMPROVE###")
                v_improve = get_val2("###VISIT_IMPROVE###", "###AI_REPLY###")
                a_reply = get_val2("###AI_REPLY###", "###BLOG_DIAG###")
                b_diag = get_val2("###BLOG_DIAG###", "###BLOG_IMPROVE###")
                b_improve = get_val2("###BLOG_IMPROVE###", "###PROFIT_PREDICT###")
                p_predict = get_val2("###PROFIT_PREDICT###", "###CONCLUSION###")
                conclusion = get_val2("###CONCLUSION###")

                # ---------------------------------------------------------
                # [HTML] 플레이스 진단 리포트 (제목에서 1일차 제거)
                # ---------------------------------------------------------
                html_report_1 = f"""
                <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
                <div style="padding: 10px; display: flex; flex-direction: column; align-items: center; font-family: 'Malgun Gothic', sans-serif;">
                    <style>
                        .section-title {{ color: #1a202c; font-size: 18px; font-weight: 800; margin-bottom: 15px; border-bottom: 2px solid #edf2f7; }}
                        .row-box {{ display: flex; margin-bottom: 12px; align-items: flex-start; }}
                        .label {{ width: 140px; font-size: 15px; font-weight: 700; color: #4a5568; }}
                        .value {{ font-size: 15px; font-weight: 600; color: #2d3748; flex: 1; word-break: keep-all; }}
                        .highlight-box {{ background-color: #f7fafc; padding: 20px; border-radius: 8px; margin-bottom: 30px; border-left: 5px solid #3182ce; }}
                    </style>
                    <div id="report-card-1" style="width: 100%; max-width: 680px; padding: 50px 40px; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; box-shadow: 0px 10px 25px rgba(0,0,0,0.05);">
                        <h2 style="text-align: center; margin-bottom: 10px; font-size: 26px; font-weight: 800;">📊 플레이스 진단 리포트</h2>
                        <p style="text-align: center; color: #718096; margin-bottom: 40px;">대상 매장: <strong>{place_name}</strong></p>
                        
                        <div class="highlight-box">
                            <h4 class="section-title" style="border:none; color:#2b6cb0;">1. 현재 점수 및 예상 순위</h4>
                            <div class="row-box"><div class="label">등록 키워드 :</div><div class="value">{current_keywords if current_keywords else "미등록"}</div></div>
                            <div class="row-box"><div class="label">플레이스 점수 :</div><div class="value" style="color: #e53e3e; font-size: 17px; font-weight: 800;">{score}</div></div>
                            <div class="row-box"><div class="label">예상 노출 순위 :</div><div class="value" style="color: #e53e3e; font-size: 17px; font-weight: 800;">{rank}</div></div>
                        </div>

                        <div style="margin-bottom: 35px;">
                            <h4 class="section-title">📌 2. 네이버 도구 누락 및 알고리즘 진단</h4>
                            <div class="row-box"><div class="label">현재 세팅 현황 :</div><div class="value" style="font-size: 14px;">{display_status}</div></div>
                            <div class="row-box"><div class="label">알고리즘 진단 :</div><div class="value">{problem}</div></div>
                        </div>

                        <div style="margin-bottom: 35px;">
                            <h4 class="section-title">💡 3. 도구 최적화 시 기대효과</h4>
                            <div class="row-box"><div class="label">순
