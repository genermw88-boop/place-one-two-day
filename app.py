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
st.markdown("네이버 플레이스 도구 누락 현상(1일 차)과 리뷰 평판 및 매출 성장(2일 차)을 한 번에 정밀 진단합니다.")

# 2. 통합 폼 입력 (중복되는 항목을 하나로 병합)
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
        with st.spinner("AI가 네이버 도구 누락 여부와 리뷰 평판 데이터를 종합 분석 중입니다. 잠시만 기다려주세요..."):
            
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            # ==========================================
            # [1일 차] 플레이스 진단 데이터 및 프롬프트 준비
            # ==========================================
            def get_status_html(is_used):
                return '<span style="color: #38a169; font-weight: 800;">등록</span>' if is_used else '<span style="color: #e53e3e; font-weight: 800;">미등록</span>'

            tool_status_text = f"예약({'등록' if use_booking else '미등록'}), 톡톡({'등록' if use_talktalk else '미등록'}), 쿠폰({'등록' if use_coupon else '미등록'}), 안심번호({'등록' if use_safecall else '미등록'})"
            display_status = f"예약({get_status_html(use_booking)}), 톡톡({get_status_html(use_talktalk)}), 쿠폰({get_status_html(use_coupon)}), 안심번호({get_status_html(use_safecall)})"
            
            prompt1 = f"""
            너는 10년 경력의 네이버 플레이스 마케팅 전문 컨설턴트야.
            아래 6개의 구분자(###)를 사용하여, 특수기호나 HTML 태그 없이 오직 전문적인 '순수 텍스트'로만 간결하게 작성해.

            [입력 데이터]
            - 플레이스 등록명: {place_name}
            - 상권: {target_area} / 업종: {main_menu}
            - 네이버 공식 도구 세팅 현황: {tool_status_text}
            - 리뷰: 방문자 {visit_reviews}개 / 블로그 {blog_reviews}개

            ###SEO_SCORE###
            (예: 35점)

            ###SEO_RANK###
            (예: 6~8페이지)

            ###PROBLEM###
            (현재 도구 세팅 현황({tool_status_text})을 근거로, '미등록'된 도구들 때문에 네이버 알고리즘 가산점을 못 받고 있으며 이로 인해 순위 경쟁에서 심각하게 밀리고 있다는 점을 1~2줄로 진단해)

            ###EFFECT###
            (미등록 도구들을 즉시 등록하여 알고리즘 가산점을 확보했을 때, 검색 노출 순위가 회복되고 고객 유입이 얼마나 상승할지 기대 효과를 1~2줄로 작성해)

            ###COMPETITOR_COUNT###
            ('{target_area}' 지역 내 '{main_menu}' 업종의 치열함을 고려해, 500m 반경 내 예상 경쟁 매장 수를 AI 알고리즘으로 추정해서 숫자와 '개' 단위만 출력해. 예: 약 45개)

            ###COMPETITION###
            (추정한 경쟁 매장 수 대비 현재 리뷰 수준을 고려하여, 상권 내 순위가 하위 몇 % 수준인지 등 사장님께 위기감을 주는 내용 1~2줄)
            """

            # ==========================================
            # [2일 차] 리뷰 평판 및 매출 예측 프롬프트 준비
            # ==========================================
            prompt2 = f"""
            너는 대한민국 최고의 소상공인 마케팅 전략가야.
            아래 데이터를 바탕으로 사장님께 드리는 '리뷰 평판 진단 리포트'를 작성해.
            HTML 태그를 적절히 사용해서 시각적으로 강조해줘. 오직 구분자(###)를 사용해서 답해.
            모든 문장은 쓸데없이 여러 줄로 나누지 말고, 최대한 꽉 찬 느낌이 들도록 핵심만 간결하게 한두 문단으로 작성해.

            [입력 데이터]
            - 매장명: {place_name} ({main_menu})
            - 방문자 리뷰: {visit_reviews}개
            - 블로그 리뷰: {blog_reviews}개

            ###VISIT_DIAG###
            방문자 리뷰 수에 대한 객관적 진단과 문제점을 간결하게 작성. 
            (주의: 본문에 현재 리뷰 수를 언급할 때 반드시 <span style="color: red; font-weight: bold;">{visit_reviews}개</span> 로 작성해라)

            ###VISIT_IMPROVE###
            방문자 리뷰에 꾸준히 답글을 달았을 때 얻을 수 있는 개선점 및 기대효과를 줄바꿈 없이 하나의 문단으로 꽉 차게 작성해.

            ###AI_REPLY###
            사장님이 실제 사용할 수 있는 방문자 리뷰 답글 예시 2개. 
            (주의: 1번 예시와 2번 예시 사이에 반드시 <br><br><br> 를 넣어 간격을 아주 넓게 띄워라)

            ###BLOG_DIAG###
            블로그 리뷰 데이터의 문제점 분석을 간결하게 작성.
            (주의: 본문에 현재 블로그 리뷰 수를 언급할 때 반드시 <span style="color: red; font-weight: bold;">{blog_reviews}개</span> 로 작성해라)

            ###BLOG_IMPROVE###
            블로그 리뷰 수가 증가하고 퀄리티가 높아졌을 때 얻을 수 있는 개선점 및 기대효과를 줄바꿈 없이 하나의 문단으로 꽉 차게 작성해.

            ###PROFIT_PREDICT###
            위드멤버의 10가지 마케팅 솔루션 적용 시 3개월 후 예상 매출 상승 범위를 현재 매장 상황에 맞게 AI가 진단해서 오직 "OO% ~ OO%" 형태의 퍼센트 수치만 출력해. (다른 설명 절대 금지)
            출력 예시: 30% ~ 45%

            ###CONCLUSION###
            아래 문장을 베이스로 하되, 매장명({place_name}) 부분은 <span style="color: red; font-weight: bold;">{place_name}</span> 로 처리하고, 두 문장 사이에 <br>을 넣어 2줄로 출력해라.
            출력 예시: 본 마케팅 패키지는 <span style="color: red; font-weight: bold;">{place_name}</span>의 낮은 온라인 인지도를 극복하고<br>압도적인 경쟁력을 확보하기 위한 필수적인 성공 전략입니다.
            """

            try:
                # API 호출 (1일 차, 2일 차 연속 실행)
                response1 = model.generate_content(prompt1)
                res_text1 = response1.text
                
                response2 = model.generate_content(prompt2)
                res_text2 = response2.text

                # --- 1일 차 결과 파싱 ---
                def get_val1(tag, next_tag=None):
                    try:
                        part = res_text1.split(tag)[1]
                        return part.split(next_tag)[0].strip() if next_tag else part.strip()
                    except: return "데이터 분석 중..."

                score = get_val1("###SEO_SCORE###", "###SEO_RANK###")
                rank = get_val1("###SEO_RANK###", "###PROBLEM###")
                problem = get_val1("###PROBLEM###", "###EFFECT###")
                effect = get_val1("###EFFECT###", "###COMPETITOR_COUNT###")
                competitor_count = get_val1("###COMPETITOR_COUNT###", "###COMPETITION###")
                competition = get_val1("###COMPETITION###")

                # --- 2일 차 결과 파싱 ---
                def get_val2(tag, next_tag=None):
                    try:
                        p = res_text2.split(tag)[1]
                        return p.split(next_tag)[0].strip() if next_tag else p.strip()
                    except: return "분석 중..."

                v_diag = get_val2("###VISIT_DIAG###", "###VISIT_IMPROVE###")
                v_improve = get_val2("###VISIT_IMPROVE###", "###AI_REPLY###")
                a_reply = get_val2("###AI_REPLY###", "###BLOG_DIAG###")
                b_diag = get_val2("###BLOG_DIAG###", "###BLOG_IMPROVE###")
                b_improve = get_val2("###BLOG_IMPROVE###", "###PROFIT_PREDICT###")
                p_predict = get_val2("###PROFIT_PREDICT###", "###CONCLUSION###")
                conclusion = get_val2("###CONCLUSION###")

                # ==========================================
                # HTML 디자인 리포트 생성
                # ==========================================
                
                st.success("✅ 종합 분석이 완료되었습니다. 아래에서 결과를 확인하세요.")

                # [1] 플레이스 진단 리포트 (1일차) HTML
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
                        <h2 style="text-align: center; margin-bottom: 10px; font-size: 26px; font-weight: 800;">📊 1일차: 플레이스 진단 리포트</h2>
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
                            <div class="row-box"><div class="label">순위 회복 효과 :</div><div class="value">{effect}</div></div>
                        </div>

                        <div style="margin-bottom: 0px;">
                            <h4 class="section-title">⚔️ 4. 반경 500m 상권 경쟁 진단</h4>
                            <div class="row-box"><div class="label">경쟁 매장 :</div><div class="value" style="color: #e53e3e; font-weight: 800;">{competitor_count} <span style="font-size: 12px; color:#718096;">(AI 자동 추정)</span></div></div>
                            <div class="row-box"><div class="label">상권 내 순위 진단 :</div><div class="value">{competition}</div></div>
                        </div>
                    </div>
                    <button onclick="downloadImage1()" style="margin-top: 30px; padding: 15px 30px; font-size: 16px; font-weight: bold; color: #fff; background-color: #2d3748; border: none; border-radius: 8px; cursor: pointer;">
                        📸 1일 차 보고서 이미지(.png) 다운로드
                    </button>
                </div>
                <script>
                function downloadImage1() {{
                    const element = document.getElementById('report-card-1');
                    html2canvas(element, {{scale: 2, backgroundColor: "#ffffff", useCORS: true}}).then(canvas => {{
                        let link = document.createElement('a');
                        link.download = '{place_name}_1일차_진단리포트.png';
                        link.href = canvas.toDataURL();
                        link.click();
                    }});
                }}
                </script>
                """

                # [2] 리뷰 평판 및 매출 예측 (2일차) HTML
                html_report_2 = f"""
                <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
                <div style="padding: 10px; display: flex; flex-direction: column; align-items: center; background-color: #f8fafc;">
                    <style>
                        @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
                        * {{ font-family: 'Pretendard', sans-serif; word-break: keep-all; overflow-wrap: break-word; line-height: 1.5; }}
                        .section-title-2 {{ color: #1e3a8a; font-size: 18px; font-weight: 800; margin-bottom: 8px; }}
                        .ad-list {{ list-style: none; padding: 0; margin: 0; display: grid; grid-template-columns: 1fr; gap: 8px; }}
                        .ad-list li {{ background: #ffffff; padding: 10px 15px; border-radius: 8px; color: #0369a1; font-weight: 700; font-size: 14.5px; border: 1px solid #bae6fd; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }}
                        .improve-box {{ background: #f0fdf4; padding: 15px 20px; border-radius: 8px; border: 1px dashed #4ade80; margin-top: 10px; margin-bottom: 25px; }}
                        .improve-title {{ color: #166534; margin-top: 0; margin-bottom: 6px; font-size: 15px; font-weight: 800; display: flex; align-items: center; gap: 5px; }}
                        .improve-text {{ color: #15803d; margin: 0; font-weight: 500; font-size: 14.5px; }}
                        
                        /* A4 용지 스타일의 카드 컨테이너 */
                        .report-page {{ width: 100%; max-width: 800px; padding: 45px 40px; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 15px; box-shadow: 0px 10px 25px rgba(0,0,0,0.05); margin-bottom: 30px; }}
                    </style>
                    
                    <div id="report-page-1" class="report-page">
                        <h1 style="text-align: center; color: #1e40af; font-size: 28px; font-weight: 900; margin-bottom: 5px;">📝 2일차: 맞춤형 평판 진단 리포트 (1/2)</h1>
                        <p style="text-align: center; color: #64748b; margin-bottom: 30px; font-size: 16px;">대상 매장: <strong style="color: #0f172a;">{place_name}</strong></p>

                        <div style="background: #fffbeb; border: 1px solid #fde68a; padding: 20px; border-radius: 12px; margin-bottom: 30px;">
                            <h4 style="color: #b45309; margin-top: 0; margin-bottom: 12px; font-size: 17px; font-weight: 800;">📌 네이버 플레이스 상위 노출 핵심 지표</h4>
                            <p style="color: #92400e; font-weight: 600; margin-bottom: 12px; font-size: 14.5px;">상위 노출은 다음 4가지 지표로 결정되며, 체계적인 관리가 필수입니다.</p>
                            <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                                <span style="background: white; padding: 6px 14px; border-radius: 20px; border: 1px solid #fcd34d; color: #d97706; font-weight: 800; font-size: 13.5px;">① 리뷰 활성도</span>
                                <span style="background: white; padding: 6px 14px; border-radius: 20px; border: 1px solid #fcd34d; color: #d97706; font-weight: 800; font-size: 13.5px;">② 키워드 적합도</span>
                                <span style="background: white; padding: 6px 14px; border-radius: 20px; border: 1px solid #fcd34d; color: #d97706; font-weight: 800; font-size: 13.5px;">③ 최신성 지수</span>
                                <span style="background: white; padding: 6px 14px; border-radius: 20px; border: 1px solid #fcd34d; color: #d97706; font-weight: 800; font-size: 13.5px;">④ 체류 시간</span>
                            </div>
                        </div>

                        <div style="border-left: 5px solid #3b82f6; padding-left: 15px;">
                            <h3 class="section-title-2">1. 방문자 리뷰 진단 및 문제점</h3>
                            <div style="color: #334155; font-size: 15px;">{v_diag}</div>
                        </div>
                        <div class="improve-box">
                            <h4 class="improve-title">✨ 꾸준한 답글 관리 시 개선점</h4>
                            <div class="improve-text">{v_improve}</div>
                        </div>

                        <div style="margin-bottom: 30px; background: #f1f5f9; padding: 20px 25px; border-radius: 10px;">
                            <h3 style="color: #0f172a; font-size: 16px; font-weight: 800; margin-top: 0; margin-bottom: 12px;">🤖 AI 추천 고객 감동 답글 예시</h3>
                            <div style="color: #475569; font-weight: 500; font-size: 14.5px; line-height: 1.6;">{a_reply}</div>
                        </div>

                        <div style="border-left: 5px solid #10b981; padding-left: 15px;">
                            <h3 style="color: #064e3b; font-size: 18px; font-weight: 800; margin-bottom: 8px;">2. 블로그 리뷰 분석 및 문제점</h3>
                            <div style="color: #334155; font-size: 15px;">{b_diag}</div>
                        </div>
                        <div class="improve-box" style="margin-bottom: 0;">
                            <h4 class="improve-title" style="color: #065f46;">✨ 양질의 블로그 리뷰 증가 시 개선점</h4>
                            <div class="improve-text" style="color: #065f46;">{b_improve}</div>
                        </div>
                    </div>
                    
                    <div id="report-page-2" class="report-page">
                        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #e2e8f0; padding-bottom: 15px; margin-bottom: 30px;">
                            <h2 style="color: #1e40af; font-size: 22px; font-weight: 900; margin: 0;">💡 마케팅 솔루션 제안서 (2/2)</h2>
                            <p style="color: #64748b; font-size: 14px; margin: 0;">대상 매장: <strong style="color: #0f172a;">{place_name}</strong></p>
                        </div>

                        <div style="background: #e0f2fe; padding: 25px; border-radius: 15px; border: 2px solid #7dd3fc; margin-bottom: 30px;">
                            <h3 style="color: #0284c7; font-size: 20px; font-weight: 900; margin-top: 0; margin-bottom: 15px; text-align: center;">💎 위드멤버 마케팅 솔루션 10가지</h3>
                            <ul class="ad-list">
                                <li>1. 네이버 플레이스 세팅 및 관리 (SEO 최적화)</li>
                                <li>2. 업체에 맞는 최적화 블로그 후보 검수 및 추천 리포트 제공</li>
                                <li>3. 매장 또는 업체 홍보용 영상 콘텐츠 제작</li>
                                <li>4. 제작 후 인스타그램 릴스, 유튜브 쇼츠 배포</li>
                                <li>5. Google Business Profile 신규 등록 및 리뷰 작성 10건</li>
                                <li>6. 카카오맵 리뷰 작성 10건</li>
                                <li>7. 광고 운영 결과에 대한 월간 리포트 제공</li>
                                <li>8. 네이버 플레이스 순위, 노출 변화 모니터링 및 유지 관리</li>
                                <li>9. 월 2회 기본 수정 (사진, 정보, 새소식)</li>
                                <li>10. Google, 카카오맵 정보 유지 및 관리</li>
                            </ul>
                            
                            <div style="margin-top: 20px; background-color: #ffffff; padding: 18px; border-radius: 10px; border: 2px dashed #38bdf8; text-align: center;">
                                <span style="color: #94a3b8; font-size: 18px; font-weight: 600; text-decoration: line-through;">400만원(정상가)</span>
                                <strong style="color: #e11d48; font-size: 24px; font-weight: 900; margin-left: 12px;">➔ 250만원</strong>
                                <span style="color: #e11d48; font-size: 18px; font-weight: 700;"> (프로모션가)</span>
                            </div>
                        </div>

                        <div style="background: #eff6ff; padding: 25px; border-radius: 10px; border: 1px solid #bfdbfe; text-align: center;">
                            <h3 style="color: #1e40af; font-weight: 800; margin-top:0; margin-bottom: 12px;">🚀 솔루션 적용 시 3개월 후 예상 매출</h3>
                            
                            <div style="font-size: 22px; font-weight: 800; color: #1e293b; margin-bottom: 25px; line-height: 1.5;">
                                위드멤버의 10가지 마케팅 솔루션 적용 시 3개월 후<br>
                                현재 대비 약 <span style="color: red; font-weight: 900; font-size: 28px;">{p_predict}</span> 상승 예상
                            </div>
                            
                            <div style="font-size: 17px; font-weight: 800; color: #1e293b; line-height: 1.6; padding-top: 20px; border-top: 1px dashed #93c5fd;">
                                {conclusion}
                            </div>
                        </div>
                    </div>
                    
                    <div style="display: flex; gap: 15px; margin-top: 10px; flex-wrap: wrap; justify-content: center;">
                        <button onclick="downloadPage2()" style="padding: 15px 25px; font-size: 16px; font-weight: 800; color: #fff; background-color: #059669; border: none; border-radius: 8px; cursor: pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                            📸 2일차 평판 리포트 다운로드
                        </button>
                        <button onclick="downloadPage3()" style="padding: 15px 25px; font-size: 16px; font-weight: 800; color: #fff; background-color: #2563eb; border: none; border-radius: 8px; cursor: pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                            📸 2일차 솔루션 제안서 다운로드
                        </button>
                    </div>
                </div>
                
                <script>
                function downloadPage2() {{
                    const element = document.getElementById('report-page-1');
                    html2canvas(element, {{ scale: 2, backgroundColor: "#ffffff", useCORS: true }}).then(canvas => {{
                        let link = document.createElement('a');
                        link.download = '{place_name}_2일차_평판리포트.png';
                        link.href = canvas.toDataURL();
                        link.click();
                    }});
                }}
                
                function downloadPage3() {{
                    const element = document.getElementById('report-page-2');
                    html2canvas(element, {{ scale: 2, backgroundColor: "#ffffff", useCORS: true }}).then(canvas => {{
                        let link = document.createElement('a');
                        link.download = '{place_name}_2일차_솔루션제안서.png';
                        link.href = canvas.toDataURL();
                        link.click();
                    }});
                }}
                </script>
                """

                # ==========================================
                # 화면 출력 (Streamlit Tabs 기능 활용하여 깔끔하게 분리)
                # ==========================================
                tab1, tab2 = st.tabs(["📑 1일 차: 플레이스 진단 리포트", "📑 2일 차: 평판 분석 및 매출 성장 제안서"])
                
                with tab1:
                    components.html(html_report_1, height=1250, scrolling=True)
                
                with tab2:
                    components.html(html_report_2, height=2300, scrolling=True)

            except Exception as e:
                st.error(f"분석 중 오류 발생: {e}")
