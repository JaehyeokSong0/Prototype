import streamlit as st
from openai import OpenAI
import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import re

# 페이지 설정
st.set_page_config(
    page_title="AI 학습 로드맵 생성기",
    page_icon="🗺️",
    layout="wide"
)

# OpenAI API 키 설정
if 'openai_api_key' not in st.session_state:
    st.session_state.openai_api_key = ""
if 'openai_client' not in st.session_state:
    st.session_state.openai_client = None

def init_openai():
    if st.session_state.openai_api_key:
        st.session_state.openai_client = OpenAI(api_key=st.session_state.openai_api_key)
        return True
    return False

def generate_roadmap(topic, level, detailed_level, duration, model="gpt-4o-mini", temperature=0.7, max_tokens=2000):
    """AI를 사용해 기본 로드맵 생성"""
    
    # 현재 날짜 정보
    current_date = datetime.now().strftime("%Y년 %m월")
    
    # 상세 수준 정보 처리
    level_info = f"기본 수준: {level}"
    if detailed_level.strip():
        level_info += f"\n상세 설명: {detailed_level}"
    
    prompt = f"""
    **중요: 반드시 유효한 JSON 형식으로만 응답하세요. {current_date} 기준 최신 정보만 사용하세요.**
    
    학습 주제: {topic}
    {level_info}
    학습 기간: {duration}
    
    위 정보를 바탕으로 **{current_date} 현재 최신 버전 기준**으로 체계적이고 구체적인 학습 로드맵을 생성해주세요.
    
    **필수 요구사항:**
    1. 반드시 유효한 JSON 형식으로만 응답
    2. 각 주차별로 구체적이고 실행 가능한 학습 내용 제시
    3. 실제 완성할 수 있는 프로젝트나 실습 과제 포함
    4. 학습 후 달성할 수 있는 명확한 기술적 목표 설정
    5. 각 주차별로 서로 다른 심화 내용으로 진행
    6. 모든 정보는 2024년 말 ~ 2025년 최신 버전 기준
    
    **예시 (Unity ML-Agents의 경우):**
    - 모호함: "ML-Agents 기초 학습" ❌
    - 구체적: "간단한 공 굴리기 에이전트 구현하여 목표 지점 도달 학습" ✅
    
    정확히 다음 JSON 형식으로만 응답하세요:
    {{
        "roadmap": [
            {{
                "week": 1,
                "title": "구체적인 주차 제목",
                "topics": ["구체적인 기술이나 개념", "실제 구현할 기능"],
                "practical_tasks": ["실제로 만들 프로젝트", "완성할 코드나 기능"],
                "resources": ["구체적인 학습 방법 (예: Unity 공식 튜토리얼 3장)", "특정 GitHub 저장소 분석"],
                "goals": "이번 주 완료 후 정확히 할 수 있게 되는 것",
                "deliverables": ["제출하거나 완성할 구체적인 결과물"],
                "week_specific_keywords": ["이번 주차에만 해당하는 검색 키워드"]
            }}
        ],
        "prerequisites": ["구체적인 사전 지식이나 설치할 도구"],
        "final_goals": ["최종적으로 만들 수 있게 되는 구체적인 프로젝트나 기능"],
        "version_info": "최신 버전 정보",
        "last_updated": "{current_date}",
        "difficulty_progression": "난이도 진행 설명"
    }}
    
    **중요**: 모든 내용은 실제로 실행 가능하고 측정 가능한 구체적인 내용으로만 작성하세요.
    다른 설명 없이 오직 JSON만 응답하세요.
    """
    
    try:
        if not st.session_state.openai_client:
            st.error("OpenAI 클라이언트가 초기화되지 않았습니다.")
            return None
            
        response = st.session_state.openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "당신은 개발자를 위한 학습 로드맵 전문가입니다. 항상 JSON 형식으로 응답하세요."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        content = response.choices[0].message.content
        
        # JSON 추출 및 정제
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        # 앞뒤 공백 제거
        content = content.strip()
        
        # JSON 파싱 시도
        try:
            return json.loads(content)
        except json.JSONDecodeError as json_error:
            st.error(f"JSON 파싱 오류: {str(json_error)}")
            st.error("AI 응답 내용:")
            st.code(content)
            
            # 간단한 JSON 수정 시도
            try:
                # 흔한 JSON 오류들 수정
                fixed_content = content
                # 마지막 쉼표 제거
                fixed_content = re.sub(r',(\s*[}\]])', r'\1', fixed_content)
                # 잘못된 따옴표 수정
                fixed_content = fixed_content.replace('"', '"').replace('"', '"')
                fixed_content = fixed_content.replace(''', "'").replace(''', "'")
                
                return json.loads(fixed_content)
            except:
                st.error("JSON 자동 수정도 실패했습니다. 다시 시도해주세요.")
                return None
    except Exception as e:
        st.error(f"로드맵 생성 중 오류 발생: {str(e)}")
        return None

def verify_resources(resources):
    """리소스 링크들의 유효성 검증"""
    verified_resources = []
    
    for resource in resources:
        if not resource.startswith('http'):
            verified_resources.append({
                "url": resource,
                "status": "검증 불가",
                "last_checked": datetime.now().strftime("%Y-%m-%d")
            })
            continue
            
        try:
            response = requests.head(resource, timeout=5, allow_redirects=True)
            if response.status_code == 200:
                status = "✅ 활성"
            else:
                status = f"❌ 오류 ({response.status_code})"
        except requests.RequestException:
            status = "❌ 접근 불가"
        
        verified_resources.append({
            "url": resource,
            "status": status,
            "last_checked": datetime.now().strftime("%Y-%m-%d")
        })
        
        time.sleep(0.5)  # 요청 간격 조절
    
    return verified_resources

def generate_full_app_pdf():
    """전체 앱 상태를 PDF로 생성"""
    try:
        from reportlab.lib.pagesizes import A4, letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from io import BytesIO
        
        # PDF 버퍼 생성
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch)
        styles = getSampleStyleSheet()
        story = []
        
        # 제목
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            spaceAfter=30,
            textColor=colors.darkblue
        )
        story.append(Paragraph("🗺️ AI 학습 로드맵 생성기 - 전체 앱 상태", title_style))
        story.append(Spacer(1, 20))
        
        # 사이드바 설정 정보
        story.append(Paragraph("⚙️ 설정 정보", styles['Heading2']))
        
        settings_data = [
            ["설정 항목", "값"],
            ["개발자 모드", "활성화" if dev_mode else "비활성화"],
            ["API 키", "설정됨" if st.session_state.openai_api_key else "없음"],
        ]
        
        if dev_mode:
            settings_data.extend([
                ["선택된 모델", model_choice],
                ["Temperature", str(temperature)],
                ["Max Tokens", str(max_tokens)]
            ])
        
        settings_table = Table(settings_data)
        settings_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(settings_table)
        story.append(Spacer(1, 20))
        
        # 입력 정보
        story.append(Paragraph("📚 입력 정보", styles['Heading2']))
        
        input_data = [
            ["입력 항목", "값"],
            ["학습 주제", topic if 'topic' in locals() and topic else "없음"],
            ["현재 수준", level if 'level' in locals() and level else "없음"],
            ["상세 설명", (detailed_level[:100] + "...") if 'detailed_level' in locals() and detailed_level and len(detailed_level) > 100 else (detailed_level if 'detailed_level' in locals() else "없음")],
            ["학습 기간", duration if 'duration' in locals() and duration else "없음"],
            ["리소스 검증", "포함" if include_verification else "제외"],
            ["최신 문서 검색", "포함" if search_latest else "제외"]
        ]
        
        input_table = Table(input_data)
        input_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(input_table)
        story.append(Spacer(1, 20))
        
        # 생성된 로드맵 (있는 경우)
        if 'roadmap_data' in locals() and roadmap_data:
            story.append(Paragraph("📋 생성된 로드맵", styles['Heading2']))
            
            # 버전 정보
            if 'version_info' in roadmap_data:
                story.append(Paragraph(f"<b>최신 버전 기준:</b> {roadmap_data.get('version_info', '')}", styles['Normal']))
                story.append(Paragraph(f"<b>생성일:</b> {roadmap_data.get('last_updated', '')}", styles['Normal']))
                if dev_mode:
                    story.append(Paragraph(f"<b>사용 모델:</b> {model_choice}", styles['Normal']))
                story.append(Spacer(1, 10))
            
            # 사전 요구사항
            if 'prerequisites' in roadmap_data:
                story.append(Paragraph("📌 사전 요구사항", styles['Heading3']))
                for prereq in roadmap_data['prerequisites']:
                    story.append(Paragraph(f"• {prereq}", styles['Normal']))
                story.append(Spacer(1, 10))
            
            # 주차별 로드맵
            story.append(Paragraph("📅 주차별 학습 계획", styles['Heading3']))
            
            for week_data in roadmap_data.get('roadmap', []):
                # 주차 제목
                week_title = f"📖 {week_data['week']}주차: {week_data['title']}"
                story.append(Paragraph(week_title, styles['Heading4']))
                
                # 학습 주제
                story.append(Paragraph("<b>📚 학습 주제:</b>", styles['Normal']))
                for topic_item in week_data.get('topics', []):
                    story.append(Paragraph(f"• {topic_item}", styles['Normal']))
                
                # 목표
                story.append(Paragraph(f"<b>🎯 목표:</b> {week_data.get('goals', '')}", styles['Normal']))
                
                # 실습 과제
                if 'practical_tasks' in week_data:
                    story.append(Paragraph("<b>🛠️ 실습 과제:</b>", styles['Normal']))
                    for task in week_data['practical_tasks']:
                        story.append(Paragraph(f"• {task}", styles['Normal']))
                
                # 완성 목표
                if 'deliverables' in week_data:
                    story.append(Paragraph("<b>📦 완성 목표:</b>", styles['Normal']))
                    for deliverable in week_data['deliverables']:
                        story.append(Paragraph(f"✅ {deliverable}", styles['Normal']))
                
                # 학습 자료
                story.append(Paragraph("<b>🔗 학습 자료:</b>", styles['Normal']))
                for resource in week_data.get('resources', []):
                    story.append(Paragraph(f"• {resource}", styles['Normal']))
                
                # 주차별 검색 키워드
                if 'week_specific_keywords' in week_data:
                    story.append(Paragraph("<b>🔍 이번 주 특화 검색:</b>", styles['Normal']))
                    for keyword in week_data['week_specific_keywords']:
                        story.append(Paragraph(f"• {keyword}", styles['Normal']))
                
                story.append(Spacer(1, 15))
            
            # 최종 목표
            if 'final_goals' in roadmap_data:
                story.append(Paragraph("🏆 최종 완성 목표", styles['Heading3']))
                for goal in roadmap_data['final_goals']:
                    story.append(Paragraph(f"• {goal}", styles['Normal']))
                story.append(Spacer(1, 10))
            
            # 난이도 진행
            if 'difficulty_progression' in roadmap_data:
                story.append(Paragraph("📈 난이도 진행", styles['Heading3']))
                story.append(Paragraph(roadmap_data['difficulty_progression'], styles['Normal']))
        
        else:
            story.append(Paragraph("📋 로드맵이 아직 생성되지 않았습니다.", styles['Normal']))
        
        # PDF 생성
        doc.build(story)
        buffer.seek(0)
        
        # 다운로드 제공
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"learning_roadmap_app_{current_time}.pdf"
        
        st.download_button(
            label="📥 PDF 다운로드",
            data=buffer.getvalue(),
            file_name=filename,
            mime="application/pdf"
        )
        
        st.success(f"✅ PDF가 생성되었습니다! '{filename}' 파일을 다운로드하세요.")
        
    except ImportError:
        st.error("❌ reportlab 패키지가 설치되지 않았습니다. `pip install reportlab`을 실행하세요.")
    except Exception as e:
        st.error(f"❌ PDF 생성 중 오류 발생: {str(e)}")

def search_real_resources(topic, search_keywords):
    """실제 존재하는 리소스를 검색해서 추가"""
    real_resources = []
    
    # 기본 검색 키워드들
    base_searches = [
        f"{topic} official documentation",
        f"{topic} tutorial 2024",
        f"{topic} getting started guide",
        f"learn {topic} beginner"
    ]
    
    # 로드맵에서 제공된 검색 키워드 추가
    if search_keywords:
        base_searches.extend([f"{topic} {keyword}" for keyword in search_keywords])
    
    # 실제로는 웹 검색 API를 사용해야 하지만, 
    # 현재는 일반적인 리소스 타입들을 제안
    common_resources = {
        "공식 문서": f"{topic} 공식 문서에서 기본 개념과 API 레퍼런스 학습",
        "GitHub 저장소": f"{topic} 관련 오픈소스 프로젝트와 예제 코드 탐색",
        "YouTube 채널": f"{topic} 전문가들의 튜토리얼 영상 시청",
        "개발 블로그": f"{topic} 관련 기술 블로그와 아티클 읽기",
        "온라인 강의": f"{topic} 온라인 강의 플랫폼에서 체계적 학습",
        "커뮤니티": f"{topic} 개발자 커뮤니티에서 질문과 토론 참여"
    }
    
    return common_resources

# 메인 UI
st.title("🗺️ AI 학습 로드맵 생성기")
st.markdown("---")

# API 키 입력
with st.sidebar:
    st.header("⚙️ 설정")
    
    # Dev 모드 토글
    dev_mode = st.checkbox(
        "🔧 개발자 모드",
        value=False,
        help="고급 설정 및 다양한 모델 선택 가능"
    )
    
    api_key_input = st.text_input(
        "OpenAI API Key", 
        value=st.session_state.openai_api_key,
        type="password",
        help="OpenAI API 키를 입력하세요"
    )
    
    # Dev 모드일 때만 모델 선택 표시
    if dev_mode:
        st.markdown("---")
        st.subheader("🤖 모델 설정")
        
        model_choice = st.selectbox(
            "사용할 모델",
            [
                "gpt-4o-mini",
                "gpt-4o", 
                "gpt-4-turbo",
                "gpt-4",
                "gpt-3.5-turbo"
            ],
            index=0,
            help="다양한 OpenAI 모델을 테스트할 수 있습니다"
        )
        
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=2.0,
            value=0.7,
            step=0.1,
            help="창의성 조절 (0: 일관성, 2: 창의성)"
        )
        
        max_tokens = st.number_input(
            "Max Tokens",
            min_value=500,
            max_value=4000,
            value=2000,
            step=100,
            help="응답 최대 길이"
        )
        
        st.info("💡 **모델 특징:**\n"
                "- **gpt-4o**: 최신 고성능 모델\n"
                "- **gpt-4o-mini**: 빠르고 효율적\n"
                "- **gpt-4-turbo**: 긴 컨텍스트 지원\n"
                "- **gpt-4**: 고품질 추론\n"
                "- **gpt-3.5-turbo**: 빠르고 경제적")
    else:
        # 일반 모드에서는 기본값 사용
        model_choice = "gpt-4o-mini"
        temperature = 0.7
        max_tokens = 2000
    
    if api_key_input != st.session_state.openai_api_key:
        st.session_state.openai_api_key = api_key_input
    
    if st.button("API 키 확인"):
        if init_openai():
            st.success("✅ API 키가 설정되었습니다!")
        else:
            st.error("❌ API 키를 입력해주세요")

# 메인 입력 폼
col1, col2 = st.columns(2)

with col1:
    st.header("📚 학습 정보 입력")
    
    topic = st.text_input(
        "학습하고 싶은 주제",
        placeholder="예: Unity ML-Agents, React Native, Docker",
        help="구체적인 기술이나 라이브러리명을 입력하세요"
    )
    
    level = st.selectbox(
        "현재 수준 (기본 선택)",
        ["완전 초보", "기초 지식 있음", "중급", "고급"],
        index=1
    )
    
    detailed_level = st.text_area(
        "현재 수준 상세 설명 (선택사항)",
        placeholder="예: Unity 기본 사용법은 알고 있고, C# 스크립팅도 할 수 있지만 ML-Agents는 처음입니다. 머신러닝 개념은 대학교에서 배웠지만 실제 구현 경험은 없습니다.",
        help="어떤 기술들을 이미 알고 있는지, 관련 경험이 있는지 자세히 설명해주세요. 더 정확한 로드맵을 생성할 수 있습니다.",
        height=100
    )
    
    duration = st.selectbox(
        "학습 기간",
        ["2주", "1개월", "2개월", "3개월", "6개월"],
        index=2
    )

with col2:
    st.header("🎯 추가 옵션")
    
    include_verification = st.checkbox(
        "리소스 검증 포함",
        value=True,
        help="생성된 로드맵의 링크들을 실시간으로 검증합니다"
    )
    
    search_latest = st.checkbox(
        "최신 문서 검색",
        value=True,
        help="주제 관련 최신 공식 문서를 검색합니다"
    )
    
    # Dev 모드일 때 추가 정보 표시
    if dev_mode:
        st.markdown("---")
        st.subheader("🔍 Dev 정보")
        st.write(f"**선택된 모델:** {model_choice}")
        st.write(f"**Temperature:** {temperature}")
        st.write(f"**Max Tokens:** {max_tokens}")
        
        if st.button("🧪 모델 테스트"):
            if not init_openai():
                st.error("❌ OpenAI API 키를 먼저 설정해주세요!")
            else:
                with st.spinner("모델 테스트 중..."):
                    try:
                        test_response = st.session_state.openai_client.chat.completions.create(
                            model=model_choice,
                            messages=[{"role": "user", "content": "Hello, this is a test."}],
                            max_tokens=50
                        )
                        st.success(f"✅ {model_choice} 모델이 정상 작동합니다!")
                        st.write(f"테스트 응답: {test_response.choices[0].message.content}")
                    except Exception as e:
                        st.error(f"❌ 모델 테스트 실패: {str(e)}")
        
        st.markdown("---")
        if st.button("📄 전체 앱 PDF 다운로드"):
            generate_full_app_pdf()
        
        st.markdown("---")
        st.subheader("📸 전체 화면 캡처")
        
        if st.button("📱 전체 앱 스크린샷 생성"):
            st.markdown("""
            **📷 전체 화면 캡처 가이드:**
            
            1. **모든 요소 펼치기:**
               - 사이드바 설정들 확인
               - 생성된 로드맵의 모든 주차별 expander 펼치기
               - 페이지 맨 아래까지 스크롤해서 모든 콘텐츠 로드
            
            2. **브라우저 캡처 (추천):**
               - 페이지 맨 위로 이동
               - `F12` → 개발자 도구 열기
               - `Ctrl+Shift+P` → "Capture full size screenshot" 입력
               - 또는 Chrome 확장 프로그램: "GoFullPage", "FireShot" 사용
            
            3. **인쇄를 통한 PDF:**
               - `Ctrl+P` → "PDF로 저장"
               - 설정에서 "배경 그래픽" 체크
               - "더 많은 설정" → "여백: 없음"
               
            4. **캡처 최적화 설정 적용됨:**
               - 가상 스크롤링 비활성화
               - 모든 요소 강제 렌더링
               - 캡처 친화적 CSS 적용
            """)
            
            # 캡처 최적화 CSS 적용
            st.markdown("""
            <style>
            /* 캡처 최적화 CSS */
            .main .block-container {
                max-width: none !important;
                padding-top: 1rem;
                padding-bottom: 2rem;
            }
            
            /* 가상 스크롤링 비활성화 */
            div[data-testid="stVerticalBlock"] {
                height: auto !important;
                overflow: visible !important;
            }
            
            /* 모든 expander 강제 표시 */
            .streamlit-expanderHeader {
                pointer-events: none;
            }
            
            /* 사이드바 고정 */
            .css-1d391kg {
                position: relative !important;
            }
            
            /* 인쇄 최적화 */
            @media print {
                .css-1d391kg {
                    position: static !important;
                    width: 100% !important;
                }
                
                .main {
                    margin-left: 0 !important;
                }
                
                body {
                    zoom: 0.8;
                }
            }
            
            /* 모든 요소 강제 렌더링 */
            * {
                -webkit-print-color-adjust: exact !important;
                color-adjust: exact !important;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # JavaScript로 모든 expander 자동 펼치기
            st.markdown("""
            <script>
            // 모든 expander 펼치기
            setTimeout(function() {
                const expanders = document.querySelectorAll('[data-testid="stExpander"] summary');
                expanders.forEach(function(expander) {
                    if (!expander.parentElement.hasAttribute('open')) {
                        expander.click();
                    }
                });
                
                // 스크롤을 맨 아래까지 해서 모든 요소 로드
                window.scrollTo(0, document.body.scrollHeight);
                
                // 다시 맨 위로
                setTimeout(function() {
                    window.scrollTo(0, 0);
                }, 1000);
                
            }, 500);
            </script>
            """, unsafe_allow_html=True)
            
            st.success("✅ 캡처 최적화가 적용되었습니다! 위 가이드를 따라 전체 화면을 캡처하세요.")
            st.info("💡 **팁**: 잠시 기다린 후 모든 요소가 펼쳐지면 캡처하세요.")

# 로드맵 생성
if st.button("🚀 로드맵 생성", type="primary", use_container_width=True):
    if not init_openai():
        st.error("❌ OpenAI API 키를 먼저 설정해주세요!")
        st.stop()
    
    if not topic:
        st.error("❌ 학습 주제를 입력해주세요!")
        st.stop()
    
    with st.spinner("🤖 AI가 최신 정보 기반 로드맵을 생성하고 있습니다..."):
        roadmap_data = generate_roadmap(topic, level, detailed_level, duration, model_choice, temperature, max_tokens)
    
    if roadmap_data:
        st.success("✅ 로드맵이 생성되었습니다!")
        
        # 로드맵 표시
        st.header(f"📋 {topic} 학습 로드맵")
        
        # 버전 정보 및 최신성 표시
        col1, col2 = st.columns([3, 1])
        with col1:
            if 'version_info' in roadmap_data:
                st.info(f"📅 **최신 버전 기준**: {roadmap_data.get('version_info', '')} (생성일: {roadmap_data.get('last_updated', '')})")
        with col2:
            if dev_mode:
                st.info(f"🤖 **사용 모델**: {model_choice}")

        
        # 사전 요구사항
        if 'prerequisites' in roadmap_data:
            st.subheader("📌 사전 요구사항")
            for prereq in roadmap_data['prerequisites']:
                st.write(f"• {prereq}")
        
        # 주차별 로드맵
        st.subheader("📅 주차별 학습 계획")
        
        for week_data in roadmap_data.get('roadmap', []):
            with st.expander(f"📖 {week_data['week']}주차: {week_data['title']}", expanded=True):
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**📚 학습 주제:**")
                    for topic_item in week_data.get('topics', []):
                        st.write(f"• {topic_item}")
                    
                    st.write("**🎯 목표:**")
                    st.write(week_data.get('goals', ''))
                    
                    # 실습 과제 추가
                    if 'practical_tasks' in week_data:
                        st.write("**🛠️ 실습 과제:**")
                        for task in week_data['practical_tasks']:
                            st.write(f"• {task}")
                    
                    # 완성 목표물 추가
                    if 'deliverables' in week_data:
                        st.write("**📦 완성 목표:**")
                        for deliverable in week_data['deliverables']:
                            st.write(f"✅ {deliverable}")
                    
                    if 'notes' in week_data and week_data['notes']:
                        st.write("**⚠️ 최신 버전 주의사항:**")
                        st.warning(week_data['notes'])
                
                with col2:
                    st.write("**🔗 학습 자료:**")
                    resources = week_data.get('resources', [])
                    
                    # 구체적인 리소스 설명으로 표시
                    for resource in resources:
                        st.write(f"• {resource}")
                    
                    # 주차별 특화 검색
                    if 'week_specific_keywords' in week_data and week_data['week_specific_keywords']:
                        st.write("**🔍 이번 주 특화 검색:**")
                        for keyword in week_data['week_specific_keywords']:
                            search_query = f"{topic} {keyword} tutorial"
                            google_search_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
                            st.write(f"• [{keyword}]({google_search_url})")
                    
                    # 주차별 진도 체크
                    progress_key = f"week_{week_data['week']}_completed"
                    completed = st.checkbox(
                        f"{week_data['week']}주차 완료", 
                        key=progress_key,
                        help="이번 주차 학습을 완료했으면 체크하세요"
                    )
        
        # 최종 목표와 난이도 진행
        col1, col2 = st.columns(2)
        
        with col1:
            if 'final_goals' in roadmap_data:
                st.subheader("🏆 최종 완성 목표")
                for goal in roadmap_data['final_goals']:
                    st.write(f"• {goal}")
        
        with col2:
            if 'difficulty_progression' in roadmap_data:
                st.subheader("📈 난이도 진행")
                st.info(roadmap_data['difficulty_progression'])
        
        # 실제 리소스 찾기 도구
        if search_latest:
            st.subheader("🔍 실제 리소스 찾기")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("**🎯 맞춤 검색:**")
                if 'search_keywords' in roadmap_data:
                    for keyword in roadmap_data['search_keywords']:
                        search_url = f"https://www.google.com/search?q={topic}+{keyword}+2024+2025".replace(' ', '+')
                        st.write(f"• ['{keyword}' 관련 최신 자료]({search_url})")
            
            with col2:
                st.write("**📚 추천 검색 사이트:**")
                search_sites = [
                    ("GitHub", f"https://github.com/search?q={topic}"),
                    ("Stack Overflow", f"https://stackoverflow.com/search?q={topic}"),
                    ("YouTube", f"https://www.youtube.com/results?search_query={topic}+tutorial+2024"),
                    ("Medium", f"https://medium.com/search?q={topic}")
                ]
                
                for site_name, search_url in search_sites:
                    st.write(f"• [{site_name}에서 검색]({search_url})")
            
            st.info("💡 **팁**: 위 링크들을 클릭해서 실제 최신 자료를 찾아보세요!")

# 푸터
st.markdown("---")
st.markdown("💡 **팁**: 현재 수준을 상세히 설명할수록 더 구체적이고 실행 가능한 로드맵을 받을 수 있습니다!")
st.markdown("🎯 **목표**: 각 주차별로 실제 완성할 수 있는 구체적인 결과물이 있는 로드맵")
st.markdown("🔄 **최신성 보장**: 모든 로드맵은 2025년 최신 버전 기준으로 생성됩니다.")
