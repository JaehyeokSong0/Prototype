import streamlit as st
from openai import OpenAI
import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import re
from io import BytesIO

# --- 페이지 설정 ---
st.set_page_config(
    page_title="AI 학습 로드맵 생성기",
    page_icon="🗺️",
    layout="wide"
)

# --- Session State 초기화 ---
# OpenAI 클라이언트 및 API 키
if 'openai_api_key' not in st.session_state:
    st.session_state.openai_api_key = ""
if 'openai_client' not in st.session_state:
    st.session_state.openai_client = None

# UI 상태
if 'current_topic' not in st.session_state:
    st.session_state.current_topic = ""
if 'current_level' not in st.session_state:
    st.session_state.current_level = "기초 지식 있음"
if 'current_detailed_level' not in st.session_state:
    st.session_state.current_detailed_level = ""
if 'current_duration' not in st.session_state:
    st.session_state.current_duration = "2개월"
if 'current_dev_mode' not in st.session_state:
    st.session_state.current_dev_mode = False
if 'current_include_verification' not in st.session_state:
    st.session_state.current_include_verification = True
if 'current_search_latest' not in st.session_state:
    st.session_state.current_search_latest = True

# 고급 설정 (개발자 모드)
if 'current_model' not in st.session_state:
    st.session_state.current_model = "gpt-4o-mini"
if 'current_temperature' not in st.session_state:
    st.session_state.current_temperature = 0.7
if 'current_max_tokens' not in st.session_state:
    st.session_state.current_max_tokens = 2000

# 생성된 결과물
if 'generated_roadmap' not in st.session_state:
    st.session_state.generated_roadmap = None

# --- 핵심 기능 함수 ---

def init_openai():
    """OpenAI 클라이언트 초기화"""
    if st.session_state.openai_api_key:
        try:
            st.session_state.openai_client = OpenAI(api_key=st.session_state.openai_api_key)
            return True
        except Exception as e:
            st.error(f"OpenAI 클라이언트 초기화 실패: {e}")
            return False
    return False

def generate_roadmap(topic, level, detailed_level, duration, model, temperature, max_tokens):
    """AI를 사용해 기본 로드맵 생성"""
    current_date = datetime.now().strftime("%Y년 %m월")
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
            max_tokens=max_tokens,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        return json.loads(content)

    except json.JSONDecodeError as json_error:
        st.error(f"JSON 파싱 오류: {str(json_error)}")
        st.error("AI가 유효하지 않은 JSON을 반환했습니다. 모델 설정을 조정하거나 다시 시도해주세요.")
        st.code(content, language='json')
        return None
    except Exception as e:
        st.error(f"로드맵 생성 중 오류 발생: {str(e)}")
        return None

def generate_full_app_pdf():
    """현재 앱의 전체 상태를 PDF 데이터로 생성하여 바이트 형태로 반환"""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        
        buffer = BytesIO()
        
        # 한글 폰트 설정 시도
        try:
            pdfmetrics.registerFont(TTFont('NanumGothic', 'NanumGothic.ttf')) # 로컬에 폰트 파일이 있다고 가정
            korean_font = 'NanumGothic'
        except:
            korean_font = 'Helvetica' # 실패 시 기본 폰트

        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        styles = getSampleStyleSheet()
        
        # 한글 폰트 적용 스타일
        styles.add(ParagraphStyle(name='KoreanNormal', fontName=korean_font, fontSize=10, leading=14))
        styles.add(ParagraphStyle(name='KoreanHeading1', fontName=korean_font, fontSize=24, leading=30, spaceAfter=20, textColor=colors.darkblue, alignment=1))
        styles.add(ParagraphStyle(name='KoreanHeading2', fontName=korean_font, fontSize=18, leading=22, spaceAfter=15, textColor=colors.darkslateblue))
        styles.add(ParagraphStyle(name='KoreanHeading3', fontName=korean_font, fontSize=14, leading=18, spaceAfter=10, textColor=colors.darkslategray))
        styles.add(ParagraphStyle(name='KoreanHeading4', fontName=korean_font, fontSize=12, leading=14, spaceAfter=8, textColor=colors.black))

        story = []
        
        story.append(Paragraph("AI 학습 로드맵 생성기 - 전체 상태 스냅샷", styles['KoreanHeading1']))
        story.append(Paragraph(f"생성 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['KoreanNormal']))
        story.append(Spacer(1, 20))

        # === 사이드바 설정 정보 ===
        story.append(Paragraph("⚙️ 사이드바 설정", styles['KoreanHeading2']))
        settings_data = [
            ["설정 항목", "값"],
            ["API 키", "설정됨" if st.session_state.openai_api_key else "미설정"],
            ["개발자 모드", "활성화" if st.session_state.current_dev_mode else "비활성화"],
        ]
        if st.session_state.current_dev_mode:
            settings_data.extend([
                ["선택된 모델", st.session_state.current_model],
                ["Temperature", str(st.session_state.current_temperature)],
                ["Max Tokens", str(st.session_state.current_max_tokens)]
            ])
        
        settings_table = Table(settings_data, colWidths=[2.5*inch, 3*inch])
        settings_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'), ('FONTNAME', (0, 0), (-1, -1), korean_font),
            ('FONTSIZE', (0, 0), (-1, -1), 10), ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey), ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(settings_table)
        story.append(Spacer(1, 20))

        # === 메인 입력 정보 ===
        story.append(Paragraph("📚 학습 정보 입력", styles['KoreanHeading2']))
        input_data = [
            ["입력 항목", "입력 값"],
            ["학습 주제", st.session_state.current_topic or "입력되지 않음"],
            ["현재 수준", st.session_state.current_level],
            ["학습 기간", st.session_state.current_duration],
            ["상세 설명", st.session_state.current_detailed_level or "없음"],
        ]
        input_table = Table(input_data, colWidths=[2.5*inch, 3*inch])
        input_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'), ('FONTNAME', (0, 0), (-1, -1), korean_font),
            ('FONTSIZE', (0, 0), (-1, -1), 10), ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen), ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(input_table)
        story.append(Spacer(1, 20))

        # === 생성된 로드맵 ===
        if st.session_state.generated_roadmap:
            roadmap = st.session_state.generated_roadmap
            story.append(Paragraph("📋 생성된 학습 로드맵", styles['KoreanHeading2']))
            story.append(Paragraph(f"<b>버전 기준:</b> {roadmap.get('version_info', 'N/A')}", styles['KoreanNormal']))
            story.append(Paragraph(f"<b>생성일:</b> {roadmap.get('last_updated', 'N/A')}", styles['KoreanNormal']))
            story.append(Spacer(1, 10))

            if 'prerequisites' in roadmap and roadmap['prerequisites']:
                story.append(Paragraph("📌 사전 요구사항", styles['KoreanHeading3']))
                for item in roadmap['prerequisites']:
                    story.append(Paragraph(f"• {item}", styles['KoreanNormal']))
                story.append(Spacer(1, 10))

            if 'roadmap' in roadmap:
                for week_data in roadmap['roadmap']:
                    story.append(Paragraph(f"📖 {week_data.get('week', 'X')}주차: {week_data.get('title', '')}", styles['KoreanHeading4']))
                    
                    details = [
                        ("<b>📚 학습 주제:</b>", week_data.get('topics')),
                        ("<b>🎯 목표:</b>", [week_data.get('goals')]),
                        ("<b>🛠️ 실습 과제:</b>", week_data.get('practical_tasks')),
                        ("<b>📦 완성 목표:</b>", week_data.get('deliverables')),
                        ("<b>🔗 학습 자료:</b>", week_data.get('resources')),
                        ("<b>🔍 이번 주 특화 검색:</b>", week_data.get('week_specific_keywords')),
                    ]
                    for title, items in details:
                        if items:
                            story.append(Paragraph(title, styles['KoreanNormal']))
                            for item in items:
                                story.append(Paragraph(f"&nbsp;&nbsp;• {item}", styles['KoreanNormal']))
                    story.append(Spacer(1, 15))

            if 'final_goals' in roadmap and roadmap['final_goals']:
                story.append(Paragraph("🏆 최종 완성 목표", styles['KoreanHeading3']))
                for goal in roadmap['final_goals']:
                    story.append(Paragraph(f"• {goal}", styles['KoreanNormal']))
                story.append(Spacer(1, 10))
            
            if 'difficulty_progression' in roadmap:
                story.append(Paragraph("📈 난이도 진행", styles['KoreanHeading3']))
                story.append(Paragraph(roadmap['difficulty_progression'], styles['KoreanNormal']))
        else:
            story.append(Paragraph("로드맵이 아직 생성되지 않았습니다.", styles['KoreanNormal']))

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    except ImportError:
        st.error("❌ PDF 생성을 위해 reportlab, nanum-gothic-coding-font 패키지를 설치해주세요.")
        st.code("pip install reportlab nanum-gothic-coding-font")
        return None
    except Exception as e:
        st.error(f"❌ PDF 생성 중 오류 발생: {str(e)}")
        if st.session_state.current_dev_mode:
            import traceback
            st.code(traceback.format_exc())
        return None

# --- 사이드바 UI ---
with st.sidebar:
    st.header("⚙️ 설정")
    
    dev_mode = st.checkbox("🔧 개발자 모드", value=st.session_state.current_dev_mode, help="고급 설정 및 다양한 모델 선택 가능")
    st.session_state.current_dev_mode = dev_mode
    
    api_key_input = st.text_input(
        "OpenAI API Key", value=st.session_state.openai_api_key, type="password", help="OpenAI API 키를 입력하세요"
    )
    if api_key_input != st.session_state.openai_api_key:
        st.session_state.openai_api_key = api_key_input
        init_openai()

    if st.button("API 키 확인 및 적용"):
        if init_openai():
            st.success("✅ API 키가 확인 및 적용되었습니다!")
        else:
            st.error("❌ 유효한 API 키를 입력해주세요.")

    if dev_mode:
        st.markdown("---")
        st.subheader("🤖 모델 설정 (개발자용)")
        st.session_state.current_model = st.selectbox(
            "사용할 모델", ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"], 
            index=["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"].index(st.session_state.current_model)
        )
        st.session_state.current_temperature = st.slider("Temperature", 0.0, 2.0, st.session_state.current_temperature, 0.1)
        st.session_state.current_max_tokens = st.number_input("Max Tokens", 500, 8000, st.session_state.current_max_tokens, 100)

# --- 메인 UI ---
st.title("🗺️ AI 학습 로드맵 생성기")
st.markdown("학습하고 싶은 주제와 현재 수준을 입력하면 AI가 맞춤형 학습 계획을 짜드립니다.")

# --- 입력 폼 ---
with st.form("roadmap_form"):
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.current_topic = st.text_input(
            "학습하고 싶은 주제", value=st.session_state.current_topic, placeholder="예: Unity ML-Agents, React Native, Docker"
        )
        st.session_state.current_level = st.selectbox(
            "현재 수준", ["완전 초보", "기초 지식 있음", "중급", "고급"], 
            index=["완전 초보", "기초 지식 있음", "중급", "고급"].index(st.session_state.current_level)
        )
    with col2:
        st.session_state.current_duration = st.selectbox(
            "학습 기간", ["2주", "1개월", "2개월", "3개월", "6개월"], 
            index=["2주", "1개월", "2개월", "3개월", "6개월"].index(st.session_state.current_duration)
        )
    
    st.session_state.current_detailed_level = st.text_area(
        "현재 수준 상세 설명 (선택사항, 더 정확한 결과를 위해 추천)", 
        value=st.session_state.current_detailed_level,
        placeholder="예: Unity 기본 사용법은 알고 있고, C# 스크립팅도 할 수 있지만 ML-Agents는 처음입니다. 머신러닝 개념은 대학교에서 배웠지만 실제 구현 경험은 없습니다."
    )

    submitted = st.form_submit_button("🚀 로드맵 생성", type="primary", use_container_width=True)

# --- 로드맵 생성 로직 ---
if submitted:
    if not st.session_state.openai_client:
        st.error("❌ OpenAI API 키를 사이드바에서 먼저 설정해주세요!")
    elif not st.session_state.current_topic:
        st.error("❌ 학습 주제를 입력해주세요!")
    else:
        with st.spinner("🤖 AI가 최신 정보 기반 로드맵을 생성하고 있습니다..."):
            roadmap_data = generate_roadmap(
                st.session_state.current_topic, 
                st.session_state.current_level, 
                st.session_state.current_detailed_level, 
                st.session_state.current_duration,
                st.session_state.current_model,
                st.session_state.current_temperature,
                st.session_state.current_max_tokens
            )
        
        if roadmap_data:
            st.session_state.generated_roadmap = roadmap_data
            st.success("✅ 로드맵이 성공적으로 생성되었습니다! 아래에서 내용을 확인하세요.")
            # st.rerun()을 호출하여 즉시 화면을 다시 그리게 할 수 있습니다.
        else:
            st.error("❌ 로드맵 생성에 실패했습니다. 잠시 후 다시 시도하거나, 개발자 모드에서 모델 설정을 변경해보세요.")

# --- 로드맵 표시 로직 (생성된 경우에만 보임) ---
if st.session_state.generated_roadmap:
    roadmap_data = st.session_state.generated_roadmap
    topic = st.session_state.current_topic

    st.markdown("---")
    st.header(f"📋 {topic} 학습 로드맵")
    
    # 메타 정보
    meta_col1, meta_col2 = st.columns([3, 1])
    with meta_col1:
        st.info(f"📅 **최신 버전 기준**: {roadmap_data.get('version_info', '정보 없음')} (생성일: {roadmap_data.get('last_updated', '정보 없음')})")
    if st.session_state.current_dev_mode:
        with meta_col2:
            st.info(f"🤖 **사용 모델**: {st.session_state.current_model}")
    
    # 사전 요구사항
    if 'prerequisites' in roadmap_data and roadmap_data['prerequisites']:
        with st.container(border=True):
            st.subheader("📌 사전 요구사항")
            for prereq in roadmap_data['prerequisites']:
                st.write(f"• {prereq}")
    
    # 주차별 계획
    st.subheader("📅 주차별 학습 계획")
    for week_data in roadmap_data.get('roadmap', []):
        with st.expander(f"📖 **{week_data.get('week', 'X')}주차: {week_data.get('title', '제목 없음')}**", expanded=True):
            w_col1, w_col2 = st.columns(2)
            with w_col1:
                st.markdown("**📚 학습 주제:**")
                for item in week_data.get('topics', []): st.write(f"• {item}")
                st.markdown("**🎯 목표:**")
                st.write(week_data.get('goals', ''))
            with w_col2:
                st.markdown("**🛠️ 실습 과제:**")
                for item in week_data.get('practical_tasks', []): st.write(f"• {item}")
                st.markdown("**📦 완성 목표:**")
                for item in week_data.get('deliverables', []): st.write(f"✅ {item}")

            st.markdown("**🔗 학습 자료:**")
            for item in week_data.get('resources', []): st.write(f"• {item}")

            if 'week_specific_keywords' in week_data and week_data['week_specific_keywords']:
                st.markdown("**🔍 이번 주 특화 검색 키워드:**")
                keywords = ", ".join([f"`{k}`" for k in week_data['week_specific_keywords']])
                st.write(keywords)

    # 최종 목표 및 난이도
    final_col1, final_col2 = st.columns(2)
    with final_col1:
        if 'final_goals' in roadmap_data and roadmap_data['final_goals']:
            st.subheader("🏆 최종 완성 목표")
            for goal in roadmap_data['final_goals']:
                st.write(f"• {goal}")
    with final_col2:
        if 'difficulty_progression' in roadmap_data:
            st.subheader("📈 난이도 진행")
            st.info(roadmap_data['difficulty_progression'])

    # --- 내보내기 기능 ---
    st.markdown("---")
    st.header("📄 로드맵 내보내기")
    
    pdf_data = generate_full_app_pdf()
    if pdf_data:
        current_time_filename = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"AI_Roadmap_{topic.replace(' ', '_')}_{current_time_filename}.pdf"
        
        st.download_button(
            label="📥 전체 로드맵 PDF 다운로드",
            data=pdf_data,
            file_name=filename,
            mime="application/pdf",
            help="현재 설정과 생성된 전체 로드맵을 PDF 파일로 저장합니다.",
            use_container_width=True
        )

# --- 푸터 ---
st.markdown("---")
st.markdown("💡 **팁**: 현재 수준을 상세히 설명할수록 더 구체적이고 실행 가능한 로드맵을 받을 수 있습니다!")
st.markdown("🎯 **목표**: 각 주차별로 실제 완성할 수 있는 구체적인 결과물이 있는 로드맵")
st.markdown("🔄 **최신성 보장**: 모든 로드맵은 2025년 최신 버전 기준으로 생성됩니다.")
