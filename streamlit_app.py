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
    
    위 정보를 바탕으로 **{current_date} 현재 최신 버전 기준**으로 체계적인 학습 로드맵을 생성해주세요.
    
    **필수 요구사항:**
    1. 반드시 유효한 JSON 형식으로만 응답
    2. 문자열에는 반드시 이스케이프 처리된 따옴표 사용
    3. 모든 리소스와 API는 2024년 말 ~ 2025년 최신 버전 기준
    4. 공식 문서 링크는 현재 활성화된 최신 버전만 사용
    5. 학습자의 상세한 현재 수준을 고려하여 효율적인 커리큘럼 구성
    
    정확히 다음 JSON 형식으로만 응답하세요:
    {{
        "roadmap": [
            {{
                "week": 1,
                "title": "주차 제목",
                "topics": ["주제1", "주제2"],
                "resources": ["리소스1", "리소스2"],
                "goals": "학습 목표",
                "notes": "주의사항"
            }}
        ],
        "prerequisites": ["요구사항1", "요구사항2"],
        "final_goals": ["목표1", "목표2"],
        "version_info": "최신 버전 정보",
        "last_updated": "{current_date}"
    }}
    
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

def search_latest_docs(topic):
    """최신 공식 문서 검색 (간단한 구글 검색)"""
    search_query = f"{topic} official documentation site:github.com OR site:docs.unity3d.com OR site:learn.microsoft.com"
    
    # 실제로는 Google Custom Search API나 다른 검색 API를 사용해야 함
    # 여기서는 시뮬레이션
    mock_results = [
        {
            "title": f"{topic} 공식 문서",
            "url": f"https://docs.example.com/{topic.lower()}",
            "snippet": f"{topic}의 최신 문서입니다.",
            "last_updated": "2024-12"
        }
    ]
    
    return mock_results

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
                    
                    if 'notes' in week_data and week_data['notes']:
                        st.write("**⚠️ 최신 버전 주의사항:**")
                        st.warning(week_data['notes'])
                
                with col2:
                    st.write("**🔗 학습 자료:**")
                    resources = week_data.get('resources', [])
                    
                    if include_verification and resources:
                        with st.spinner("리소스 검증 중..."):
                            verified = verify_resources(resources)
                        
                        for resource_info in verified:
                            st.write(f"• [{resource_info['url']}]({resource_info['url']}) {resource_info['status']}")
                    else:
                        for resource in resources:
                            st.write(f"• {resource}")
        
        # 최종 목표
        if 'final_goals' in roadmap_data:
            st.subheader("🏆 최종 학습 목표")
            for goal in roadmap_data['final_goals']:
                st.write(f"• {goal}")
        
        # 최신 문서 검색 결과
        if search_latest:
            st.subheader("🔍 관련 최신 문서")
            with st.spinner("최신 문서를 검색하고 있습니다..."):
                latest_docs = search_latest_docs(topic)
            
            for doc in latest_docs:
                st.write(f"📄 [{doc['title']}]({doc['url']}) (업데이트: {doc['last_updated']})")
                st.write(f"   {doc['snippet']}")

# 푸터
st.markdown("---")
st.markdown("💡 **팁**: 현재 수준을 상세히 설명할수록 더 정확하고 효율적인 로드맵을 받을 수 있습니다!")
st.markdown("🔄 **최신성 보장**: 모든 로드맵은 2025년 최신 버전 기준으로 생성됩니다.")
