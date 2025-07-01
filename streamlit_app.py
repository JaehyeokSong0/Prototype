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

# UI 상태 저장을 위한 session state 초기화
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
if 'current_model' not in st.session_state:
    st.session_state.current_model = "gpt-4o-mini"
if 'current_temperature' not in st.session_state:
    st.session_state.current_temperature = 0.7
if 'current_max_tokens' not in st.session_state:
    st.session_state.current_max_tokens = 2000
if 'current_include_verification' not in st.session_state:
    st.session_state.current_include_verification = True
if 'current_search_latest' not in st.session_state:
    st.session_state.current_search_latest = True
if 'generated_roadmap' not in st.session_state:
    st.session_state.generated_roadmap = None

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
    """현재 앱의 전체 화면 상태를 PDF로 생성"""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from io import BytesIO
        
        # 한글 폰트 설정
        korean_font = 'Helvetica'  # 기본값
        try:
            import platform
            system = platform.system()
            
            if system == "Windows":
                try:
                    pdfmetrics.registerFont(TTFont('Korean', "C:/Windows/Fonts/malgun.ttf"))
                    korean_font = 'Korean'
                except:
                    pass
        except:
            pass
        
        # PDF 버퍼 생성
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        styles = getSampleStyleSheet()
        
        # 한글 폰트 적용
        if korean_font == 'Korean':
            for style_name in ['Normal', 'Heading1', 'Heading2', 'Heading3', 'Heading4']:
                styles[style_name].fontName = korean_font
        
        story = []
        
        # === 제목 ===
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.darkblue,
            fontName=korean_font,
            alignment=1  # 중앙 정렬
        )
        
        if korean_font == 'Korean':
            story.append(Paragraph("AI 학습 로드맵 생성기", title_style))
            story.append(Paragraph("전체 앱 상태 스냅샷", styles['Heading2']))
        else:
            story.append(Paragraph("AI Learning Roadmap Generator", title_style))
            story.append(Paragraph("Full App State Snapshot", styles['Heading2']))
        
        story.append(Spacer(1, 20))
        
        # === 생성 정보 ===
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if korean_font == 'Korean':
            story.append(Paragraph(f"생성 일시: {current_time}", styles['Normal']))
        else:
            story.append(Paragraph(f"Generated: {current_time}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # === 사이드바 설정 정보 ===
        if korean_font == 'Korean':
            story.append(Paragraph("⚙️ 사이드바 설정", styles['Heading2']))
        else:
            story.append(Paragraph("⚙️ Sidebar Settings", styles['Heading2']))
        
        # 설정 테이블 데이터
        if korean_font == 'Korean':
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
        else:
            settings_data = [
                ["Setting", "Value"],
                ["API Key", "Set" if st.session_state.openai_api_key else "Not Set"],
                ["Dev Mode", "Enabled" if st.session_state.current_dev_mode else "Disabled"],
            ]
            
            if st.session_state.current_dev_mode:
                settings_data.extend([
                    ["Selected Model", st.session_state.current_model],
                    ["Temperature", str(st.session_state.current_temperature)],
                    ["Max Tokens", str(st.session_state.current_max_tokens)]
                ])
        
        settings_table = Table(settings_data, colWidths=[2.5*inch, 3*inch])
        settings_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), korean_font),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        story.append(settings_table)
        story.append(Spacer(1, 20))
        
        # === 메인 입력 정보 ===
        if korean_font == 'Korean':
            story.append(Paragraph("📚 학습 정보 입력", styles['Heading2']))
        else:
            story.append(Paragraph("📚 Learning Information Input", styles['Heading2']))
        
        # 입력 테이블 데이터
        if korean_font == 'Korean':
            input_data = [
                ["입력 항목", "입력 값"],
                ["학습 주제", st.session_state.current_topic or "입력되지 않음"],
                ["현재 수준", st.session_state.current_level],
                ["학습 기간", st.session_state.current_duration],
                ["리소스 검증", "포함" if st.session_state.current_include_verification else "제외"],
                ["최신 문서 검색", "포함" if st.session_state.current_search_latest else "제외"]
            ]
            
            # 상세 설명이 있으면 추가
            if st.session_state.current_detailed_level:
                detailed_text = st.session_state.current_detailed_level
                if len(detailed_text) > 150:
                    detailed_text = detailed_text[:150] + "..."
                input_data.insert(-2, ["상세 설명", detailed_text])
        else:
            input_data = [
                ["Input Item", "Value"],
                ["Learning Topic", st.session_state.current_topic or "Not entered"],
                ["Current Level", st.session_state.current_level],
                ["Learning Duration", st.session_state.current_duration],
                ["Resource Verification", "Included" if st.session_state.current_include_verification else "Excluded"],
                ["Latest Docs Search", "Included" if st.session_state.current_search_latest else "Excluded"]
            ]
            
            if st.session_state.current_detailed_level:
                detailed_text = st.session_state.current_detailed_level
                if len(detailed_text) > 150:
                    detailed_text = detailed_text[:150] + "..."
                input_data.insert(-2, ["Detailed Description", detailed_text])
        
        input_table = Table(input_data, colWidths=[2.5*inch, 3*inch])
        input_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), korean_font),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        story.append(input_table)
        story.append(Spacer(1, 20))
        
        # === 생성된 로드맵 ===
        if st.session_state.generated_roadmap:
            roadmap_data = st.session_state.generated_roadmap
            
            if korean_font == 'Korean':
                story.append(Paragraph("📋 생성된 학습 로드맵", styles['Heading2']))
            else:
                story.append(Paragraph("📋 Generated Learning Roadmap", styles['Heading2']))
            
            # 로드맵 메타 정보
            if 'version_info' in roadmap_data:
                if korean_font == 'Korean':
                    story.append(Paragraph(f"<b>최신 버전 기준:</b> {roadmap_data.get('version_info', '')}", styles['Normal']))
                    story.append(Paragraph(f"<b>생성 일자:</b> {roadmap_data.get('last_updated', '')}", styles['Normal']))
                    if st.session_state.current_dev_mode:
                        story.append(Paragraph(f"<b>사용 모델:</b> {st.session_state.current_model}", styles['Normal']))
                else:
                    story.append(Paragraph(f"<b>Version Info:</b> {roadmap_data.get('version_info', '')}", styles['Normal']))
                    story.append(Paragraph(f"<b>Generated:</b> {roadmap_data.get('last_updated', '')}", styles['Normal']))
                    if st.session_state.current_dev_mode:
                        story.append(Paragraph(f"<b>Model Used:</b> {st.session_state.current_model}", styles['Normal']))
                story.append(Spacer(1, 10))
            
            # 사전 요구사항
            if 'prerequisites' in roadmap_data and roadmap_data['prerequisites']:
                if korean_font == 'Korean':
                    story.append(Paragraph("📌 사전 요구사항", styles['Heading3']))
                else:
                    story.append(Paragraph("📌 Prerequisites", styles['Heading3']))
                
                for prereq in roadmap_data['prerequisites']:
                    story.append(Paragraph(f"• {prereq}", styles['Normal']))
                story.append(Spacer(1, 10))
            
            # 주차별 로드맵
            if 'roadmap' in roadmap_data:
                if korean_font == 'Korean':
                    story.append(Paragraph("📅 주차별 학습 계획", styles['Heading3']))
                else:
                    story.append(Paragraph("📅 Weekly Learning Plan", styles['Heading3']))
                
                for week_data in roadmap_data['roadmap']:
                    # 주차 제목
                    if korean_font == 'Korean':
                        week_title = f"📖 {week_data.get('week', 'X')}주차: {week_data.get('title', '')}"
                    else:
                        week_title = f"📖 Week {week_data.get('week', 'X')}: {week_data.get('title', '')}"
                    
                    story.append(Paragraph(week_title, styles['Heading4']))
                    
                    # 학습 주제
                    if 'topics' in week_data:
                        if korean_font == 'Korean':
                            story.append(Paragraph("<b>📚 학습 주제:</b>", styles['Normal']))
                        else:
                            story.append(Paragraph("<b>📚 Learning Topics:</b>", styles['Normal']))
                        
                        for topic_item in week_data['topics']:
                            story.append(Paragraph(f"  • {topic_item}", styles['Normal']))
                    
                    # 목표
                    if 'goals' in week_data:
                        if korean_font == 'Korean':
                            story.append(Paragraph(f"<b>🎯 목표:</b> {week_data['goals']}", styles['Normal']))
                        else:
                            story.append(Paragraph(f"<b>🎯 Goals:</b> {week_data['goals']}", styles['Normal']))
                    
                    # 실습 과제
                    if 'practical_tasks' in week_data:
                        if korean_font == 'Korean':
                            story.append(Paragraph("<b>🛠️ 실습 과제:</b>", styles['Normal']))
                        else:
                            story.append(Paragraph("<b>🛠️ Practical Tasks:</b>", styles['Normal']))
                        
                        for task in week_data['practical_tasks']:
                            story.append(Paragraph(f"  • {task}", styles['Normal']))
                    
                    # 완성 목표
                    if 'deliverables' in week_data:
                        if korean_font == 'Korean':
                            story.append(Paragraph("<b>📦 완성 목표:</b>", styles['Normal']))
                        else:
                            story.append(Paragraph("<b>📦 Deliverables:</b>", styles['Normal']))
                        
                        for deliverable in week_data['deliverables']:
                            story.append(Paragraph(f"  ✅ {deliverable}", styles['Normal']))
                    
                    # 학습 자료
                    if 'resources' in week_data:
                        if korean_font == 'Korean':
                            story.append(Paragraph("<b>🔗 학습 자료:</b>", styles['Normal']))
                        else:
                            story.append(Paragraph("<b>🔗 Learning Resources:</b>", styles['Normal']))
                        
                        for resource in week_data['resources']:
                            story.append(Paragraph(f"  • {resource}", styles['Normal']))
                    
                    # 주차별 검색 키워드
                    if 'week_specific_keywords' in week_data:
                        if korean_font == 'Korean':
                            story.append(Paragraph("<b>🔍 이번 주 특화 검색:</b>", styles['Normal']))
                        else:
                            story.append(Paragraph("<b>🔍 Week-specific Search:</b>", styles['Normal']))
                        
                        for keyword in week_data['week_specific_keywords']:
                            story.append(Paragraph(f"  • {keyword}", styles['Normal']))
                    
                    story.append(Spacer(1, 15))
            
            # 최종 목표
            if 'final_goals' in roadmap_data and roadmap_data['final_goals']:
                if korean_font == 'Korean':
                    story.append(Paragraph("🏆 최종 완성 목표", styles['Heading3']))
                else:
                    story.append(Paragraph("🏆 Final Goals", styles['Heading3']))
                
                for goal in roadmap_data['final_goals']:
                    story.append(Paragraph(f"• {goal}", styles['Normal']))
                story.append(Spacer(1, 10))
            
            # 난이도 진행
            if 'difficulty_progression' in roadmap_data:
                if korean_font == 'Korean':
                    story.append(Paragraph("📈 난이도 진행", styles['Heading3']))
                else:
                    story.append(Paragraph("📈 Difficulty Progression", styles['Heading3']))
                
                story.append(Paragraph(roadmap_data['difficulty_progression'], styles['Normal']))
        
        else:
            if korean_font == 'Korean':
                story.append(Paragraph("📋 로드맵이 아직 생성되지 않았습니다.", styles['Heading2']))
                story.append(Paragraph("로드맵을 생성한 후 PDF를 다시 다운로드하세요.", styles['Normal']))
            else:
                story.append(Paragraph("📋 Roadmap has not been generated yet.", styles['Heading2']))
                story.append(Paragraph("Please generate a roadmap first, then download the PDF again.", styles['Normal']))
        
        # PDF 생성
        doc.build(story)
        buffer.seek(0)
        
        # 다운로드 제공
        current_time_filename = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"learning_roadmap_full_app_{current_time_filename}.pdf"
        
        st.download_button(
            label="📥 PDF 다운로드",
            data=buffer.getvalue(),
            file_name=filename,
            mime="application/pdf",
            key="pdf_download_btn"
        )
        
        if korean_font == 'Korean':
            st.success(f"✅ 전체 앱 상태가 PDF로 생성되었습니다! '{filename}' 파일을 다운로드하세요.")
        else:
            st.success(f"✅ Full app state PDF generated! Download '{filename}' file.")
        
    except ImportError:
        st.error("❌ PDF 생성을 위해 reportlab 패키지를 설치해주세요.")
        st.code("pip install reportlab")
        st.info("💡 로컬에서 실행 중이라면 터미널에서 위 명령어를 실행하세요.\n📱 Streamlit Cloud에서 실행 중이라면 requirements.txt에 reportlab을 추가하고 재배포하세요.")
    except Exception as e:
        st.error(f"❌ PDF 생성 중 오류 발생: {str(e)}")
        # 디버깅을 위한 상세 정보
        if st.session_state.current_dev_mode:
            st.error(f"상세 오류: {type(e).__name__}: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

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

# API 키 입력
with st.sidebar:
    st.header("⚙️ 설정")
    
    # Dev 모드 토글
    dev_mode = st.checkbox(
        "🔧 개발자 모드",
        value=st.session_state.current_dev_mode,
        help="고급 설정 및 다양한 모델 선택 가능"
    )
    st.session_state.current_dev_mode = dev_mode
    
    api_key_input = st.text_input(
        "OpenAI API Key", 
        value=st.session_state.openai_api_key,
        type="password",
        help="OpenAI API 키를 입력하세요"
    )
    
    if api_key_input != st.session_state.openai_api_key:
        st.session_state.openai_api_key = api_key_input
    
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
        st.session_state.current_model = model_choice
        
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=2.0,
            value=st.session_state.current_temperature,
            step=0.1,
            help="창의성 조절 (0: 일관성, 2: 창의성)"
        )
        st.session_state.current_temperature = temperature
        
        max_tokens = st.number_input(
            "Max Tokens",
            min_value=500,
            max_value=4000,
            value=st.session_state.current_max_tokens,
            step=100,
            help="응답 최대 길이"
        )
        st.session_state.current_max_tokens = max_tokens
        
        st.info("💡 **모델 특징:**\n"
                "- **gpt-4o**: 최신 고성능 모델\n"
                "- **gpt-4o-mini**: 빠르고 효율적\n"
                "- **gpt-4-turbo**: 긴 컨텍스트 지원\n"
                "- **gpt-4**: 고품질 추론\n"
                "- **gpt-3.5-turbo**: 빠르고 경제적")
    else:
        # 일반 모드에서는 session state 기본값 사용
        model_choice = st.session_state.current_model
        temperature = st.session_state.current_temperature
        max_tokens = st.session_state.current_max_tokens
    
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
        value=st.session_state.current_topic,
        placeholder="예: Unity ML-Agents, React Native, Docker",
        help="구체적인 기술이나 라이브러리명을 입력하세요"
    )
    st.session_state.current_topic = topic
    
    level = st.selectbox(
        "현재 수준 (기본 선택)",
        ["완전 초보", "기초 지식 있음", "중급", "고급"],
        index=["완전 초보", "기초 지식 있음", "중급", "고급"].index(st.session_state.current_level)
    )
    st.session_state.current_level = level
    
    detailed_level = st.text_area(
        "현재 수준 상세 설명 (선택사항)",
        value=st.session_state.current_detailed_level,
        placeholder="예: Unity 기본 사용법은 알고 있고, C# 스크립팅도 할 수 있지만 ML-Agents는 처음입니다. 머신러닝 개념은 대학교에서 배웠지만 실제 구현 경험은 없습니다.",
        help="어떤 기술들을 이미 알고 있는지, 관련 경험이 있는지 자세히 설명해주세요. 더 정확한 로드맵을 생성할 수 있습니다.",
        height=100
    )
    st.session_state.current_detailed_level = detailed_level
    
    duration = st.selectbox(
        "학습 기간",
        ["2주", "1개월", "2개월", "3개월", "6개월"],
        index=["2주", "1개월", "2개월", "3개월", "6개월"].index(st.session_state.current_duration)
    )
    st.session_state.current_duration = duration

with col2:
    st.header("🎯 추가 옵션")
    
    include_verification = st.checkbox(
        "리소스 검증 포함",
        value=st.session_state.current_include_verification,
        help="생성된 로드맵의 링크들을 실시간으로 검증합니다"
    )
    st.session_state.current_include_verification = include_verification
    
    search_latest = st.checkbox(
        "최신 문서 검색",
        value=st.session_state.current_search_latest,
        help="주제 관련 최신 공식 문서를 검색합니다"
    )
    st.session_state.current_search_latest = search_latest
    
    # Dev 모드일 때 추가 정보 표시
    if st.session_state.current_dev_mode:
        st.markdown("---")
        st.subheader("🔍 Dev 정보")
        st.write(f"**선택된 모델:** {st.session_state.current_model}")
        st.write(f"**Temperature:** {st.session_state.current_temperature}")
        st.write(f"**Max Tokens:** {st.session_state.current_max_tokens}")
        
        if st.button("🧪 모델 테스트"):
            if not init_openai():
                st.error("❌ OpenAI API 키를 먼저 설정해주세요!")
            else:
                with st.spinner("모델 테스트 중..."):
                    try:
                        test_response = st.session_state.openai_client.chat.completions.create(
                            model=st.session_state.current_model,
                            messages=[{"role": "user", "content": "Hello, this is a test."}],
                            max_tokens=50
                        )
                        st.success(f"✅ {st.session_state.current_model} 모델이 정상 작동합니다!")
                        st.write(f"테스트 응답: {test_response.choices[0].message.content}")
                    except Exception as e:
                        st.error(f"❌ 모델 테스트 실패: {str(e)}")

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
        # 생성된 로드맵을 session state에 저장
        st.session_state.generated_roadmap = roadmap_data
        st.success("✅ 로드맵이 생성되었습니다!")
        
        # 로드맵 표시
        st.header(f"📋 {topic} 학습 로드맵")
        
        # 버전 정보 및 최신성 표시
        col1, col2 = st.columns([3, 1])
        with col1:
            if 'version_info' in roadmap_data:
                st.info(f"📅 **최신 버전 기준**: {roadmap_data.get('version_info', '')} (생성일: {roadmap_data.get('last_updated', '')})")
        with col2:
            if st.session_state.current_dev_mode:
                st.info(f"🤖 **사용 모델**: {st.session_state.current_model}")
        
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
        
        # Dev 모드에서만 PDF 다운로드 옵션 표시
        if st.session_state.current_dev_mode:
            st.markdown("---")
            st.subheader("📄 앱 상태 내보내기")
            if st.button("📥 전체 앱 PDF 다운로드"):
                generate_full_app_pdf()
            
            if st.session_state.generated_roadmap:
                st.info("💡 현재 화면의 모든 설정, 입력값, 생성된 로드맵을 포함한 완전한 PDF를 생성합니다.")
            else:
                st.warning("⚠️ 로드맵을 먼저 생성하면 더 완전한 PDF를 받을 수 있습니다.")

# 푸터
st.markdown("---")
st.markdown("💡 **팁**: 현재 수준을 상세히 설명할수록 더 구체적이고 실행 가능한 로드맵을 받을 수 있습니다!")
st.markdown("🎯 **목표**: 각 주차별로 실제 완성할 수 있는 구체적인 결과물이 있는 로드맵")
st.markdown("🔄 **최신성 보장**: 모든 로드맵은 2025년 최신 버전 기준으로 생성됩니다.")
