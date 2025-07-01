def generate_full_page_pdf():
    """현재 웹페이지 전체를 PDF로 캡처 (확장된 로드맵 포함)"""
    
    # PDF 생성 시작 상태 표시
    pdf_status = st.empty()
    pdf_status.info("📄 전체 페이지 PDF 생성 중...")
    
    try:
        # 웹페이지 캡처를 위한 JavaScript 코드
        capture_js = """
        <script>
        // PDF 생성을 위한 페이지 캡처 함수
        async function captureFullPage() {
            try {
                // 페이지의 모든 확장 가능한 요소들을 확장
                const expanders = document.querySelectorAll('[data-testid="stExpander"]');
                expanders.forEach(expander => {
                    const button = expander.querySelector('button');
                    if (button && button.getAttribute('aria-expanded') === 'false') {
                        button.click();
                    }
                });
                
                // 잠시 기다려서 확장이 완료되도록 함
                await new Promise(resolve => setTimeout(resolve, 1000));
                
                // 브라우저의 인쇄 기능 호출
                window.print();
                
                return true;
            } catch (error) {
                console.error('페이지 캡처 오류:', error);
                return false;
            }
        }
        
        // 함수 실행
        captureFullPage();
        </script>
        """
        
        # JavaScript 코드를 Streamlit에 삽입
        st.components.v1.html(capture_js, height=0)
        
        pdf_status.success("✅ 브라우저 인쇄 창이 열렸습니다!")
        
        # 사용자 안내
        st.info("""
        📖 **인쇄 창 사용법:**
        1. 인쇄 창에서 **'대상'을 'PDF로 저장'**으로 변경
        2. **'기타 설정'** 클릭
        3. **'배경 그래픽'** 체크 (색상과 스타일 유지)
        4. **'저장'** 버튼 클릭하여 PDF 다운로드
        
        💡 **팁:** 
        - 모든 로드맵 섹션이 확장된 상태로 캡처됩니다
        - 페이지가 길면 여러 페이지로 자동 분할됩니다
        """)
        
    except Exception as e:
        pdf_status.error(f"❌ PDF 캡처 설정 중 오류: {str(e)}")
        
        # 수동 방법 안내
        st.warning("⚠️ 자동 캡처에 실패했습니다. 수동으로 인쇄하세요:")
        st.markdown("""
        **수동 PDF 생성 방법:**
        1. **Ctrl+P** (Windows) 또는 **Cmd+P** (Mac) 키 입력
        2. 대상을 **'PDF로 저장'**으로 변경
        3. **'기타 설정'** → **'배경 그래픽'** 체크
        4. **저장** 클릭
        """)


def generate_full_app_pdf_alternative():
    """대안: HTML을 이용한 전체 페이지 PDF 생성"""
    
    pdf_status = st.empty()
    pdf_status.info("📄 HTML 기반 PDF 생성 중...")
    
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate
        from reportlab.lib.units import inch
        from io import BytesIO
        import base64
        
        # 현재 페이지의 HTML 생성
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>AI 학습 로드맵 - {st.session_state.current_topic or '전체 리포트'}</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                h1, h2, h3 {{
                    color: #1f77b4;
                    border-bottom: 2px solid #e0e0e0;
                    padding-bottom: 5px;
                }}
                .expander {{
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    margin: 10px 0;
                    padding: 15px;
                    background-color: #f9f9f9;
                }}
                .week-section {{
                    background-color: #ffffff;
                    border-left: 4px solid #1f77b4;
                    padding: 15px;
                    margin: 15px 0;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                ul {{
                    padding-left: 20px;
                }}
                li {{
                    margin: 5px 0;
                }}
                .meta-info {{
                    background-color: #e3f2fd;
                    padding: 10px;
                    border-radius: 5px;
                    margin: 10px 0;
                }}
                .goal {{
                    background-color: #fff3e0;
                    padding: 10px;
                    border-radius: 5px;
                    border-left: 4px solid #ff9800;
                }}
                @media print {{
                    body {{ margin: 0; }}
                    .expander {{ page-break-inside: avoid; }}
                }}
            </style>
        </head>
        <body>
        """
        
        # 제목
        html_content += f"""
        <h1>🗺️ AI 학습 로드맵 생성기</h1>
        <div class="meta-info">
            <p><strong>생성 일시:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>학습 주제:</strong> {st.session_state.current_topic or '미입력'}</p>
            <p><strong>현재 수준:</strong> {st.session_state.current_level}</p>
            <p><strong>학습 기간:</strong> {st.session_state.current_duration}</p>
        </div>
        """
        
        # 로드맵 내용
        if st.session_state.generated_roadmap:
            roadmap_data = st.session_state.generated_roadmap
            
            html_content += "<h2>📋 생성된 학습 로드맵</h2>"
            
            # 메타 정보
            if 'version_info' in roadmap_data:
                html_content += f"""
                <div class="meta-info">
                    <p><strong>최신 버전 기준:</strong> {roadmap_data.get('version_info', '')}</p>
                    <p><strong>생성 일자:</strong> {roadmap_data.get('last_updated', '')}</p>
                </div>
                """
            
            # 사전 요구사항
            if 'prerequisites' in roadmap_data and roadmap_data['prerequisites']:
                html_content += "<h3>📌 사전 요구사항</h3><ul>"
                for prereq in roadmap_data['prerequisites']:
                    html_content += f"<li>{prereq}</li>"
                html_content += "</ul>"
            
            # 주차별 로드맵
            if 'roadmap' in roadmap_data:
                html_content += "<h3>📅 주차별 학습 계획</h3>"
                
                for week_data in roadmap_data['roadmap']:
                    html_content += f"""
                    <div class="week-section">
                        <h4>📖 {week_data.get('week', 'X')}주차: {week_data.get('title', '')}</h4>
                        
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                            <div>
                                <h5>📚 학습 주제:</h5>
                                <ul>
                    """
                    
                    for topic in week_data.get('topics', []):
                        html_content += f"<li>{topic}</li>"
                    
                    html_content += """
                                </ul>
                                
                                <div class="goal">
                                    <strong>🎯 목표:</strong> """ + week_data.get('goals', '') + """
                                </div>
                    """
                    
                    if 'practical_tasks' in week_data:
                        html_content += "<h5>🛠️ 실습 과제:</h5><ul>"
                        for task in week_data['practical_tasks']:
                            html_content += f"<li>{task}</li>"
                        html_content += "</ul>"
                    
                    html_content += "</div><div>"
                    
                    if 'deliverables' in week_data:
                        html_content += "<h5>📦 완성 목표:</h5><ul>"
                        for deliverable in week_data['deliverables']:
                            html_content += f"<li>✅ {deliverable}</li>"
                        html_content += "</ul>"
                    
                    if 'resources' in week_data:
                        html_content += "<h5>🔗 학습 자료:</h5><ul>"
                        for resource in week_data['resources']:
                            html_content += f"<li>{resource}</li>"
                        html_content += "</ul>"
                    
                    if 'week_specific_keywords' in week_data:
                        html_content += "<h5>🔍 이번 주 특화 검색:</h5><ul>"
                        for keyword in week_data['week_specific_keywords']:
                            html_content += f"<li>{keyword}</li>"
                        html_content += "</ul>"
                    
                    html_content += "</div></div></div>"
            
            # 최종 목표
            if 'final_goals' in roadmap_data and roadmap_data['final_goals']:
                html_content += "<h3>🏆 최종 완성 목표</h3><ul>"
                for goal in roadmap_data['final_goals']:
                    html_content += f"<li>{goal}</li>"
                html_content += "</ul>"
            
            # 난이도 진행
            if 'difficulty_progression' in roadmap_data:
                html_content += f"""
                <h3>📈 난이도 진행</h3>
                <div class="meta-info">{roadmap_data['difficulty_progression']}</div>
                """
        
        else:
            html_content += """
            <h2>📋 로드맵이 아직 생성되지 않았습니다</h2>
            <p>로드맵을 생성한 후 PDF를 다시 다운로드하세요.</p>
            """
        
        html_content += """
        </body>
        </html>
        """
        
        # HTML을 base64로 인코딩
        html_b64 = base64.b64encode(html_content.encode('utf-8')).decode()
        
        # 다운로드 링크 생성
        current_time_filename = datetime.now().strftime("%Y%m%d_%H%M%S")
        if st.session_state.current_topic:
            safe_topic = "".join(c for c in st.session_state.current_topic if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_topic = safe_topic.replace(' ', '_')[:20]
            filename = f"roadmap_{safe_topic}_{current_time_filename}.html"
        else:
            filename = f"learning_roadmap_{current_time_filename}.html"
        
        # HTML 파일 다운로드 제공
        st.download_button(
            label="📥 HTML 다운로드 (브라우저에서 PDF로 변환)",
            data=html_content.encode('utf-8'),
            file_name=filename,
            mime="text/html",
            key="html_download_btn",
            use_container_width=True
        )
        
        pdf_status.success("✅ HTML 파일이 생성되었습니다!")
        
        st.info("""
        📖 **HTML → PDF 변환 방법:**
        1. 다운로드한 HTML 파일을 브라우저로 열기
        2. **Ctrl+P** (Windows) 또는 **Cmd+P** (Mac)
        3. **'PDF로 저장'** 선택
        4. **'기타 설정' → '배경 그래픽'** 체크
        5. **저장** 클릭
        
        💡 이 방법으로 완벽한 형태의 PDF를 얻을 수 있습니다!
        """)
        
    except Exception as e:
        pdf_status.error(f"❌ HTML 생성 중 오류: {str(e)}")
        
        # 수동 방법 재안내
        st.warning("HTML 생성도 실패했습니다. 브라우저 인쇄 기능을 사용하세요:")
        st.markdown("""
        **수동 PDF 생성:**
        1. **Ctrl+P** (Windows) 또는 **Cmd+P** (Mac)
        2. **'PDF로 저장'** 선택
        3. **'기타 설정' → '배경 그래픽'** 체크
        4. **저장** 클릭
        """)


# 메인 PDF 생성 함수 (두 가지 옵션 제공)
def generate_full_app_pdf():
    """전체 페이지 PDF 생성 - 두 가지 방법 제공"""
    
    st.subheader("📄 전체 페이지 PDF 생성")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**방법 1: 브라우저 인쇄 (추천)**")
        if st.button("🖨️ 브라우저 인쇄 실행", use_container_width=True):
            generate_full_page_pdf()
    
    with col2:
        st.write("**방법 2: HTML 다운로드**")
        if st.button("📄 HTML 파일 생성", use_container_width=True):
            generate_full_app_pdf_alternative()
    
    # 사용법 안내
    with st.expander("❓ PDF 생성 방법 상세 설명"):
        st.markdown("""
        ### 🖨️ 방법 1: 브라우저 인쇄 (가장 정확함)
        - 현재 화면 상태 그대로 PDF로 저장
        - 모든 확장된 로드맵 섹션 포함
        - 색상, 스타일, 레이아웃 완벽 보존
        
        ### 📄 방법 2: HTML 다운로드
        - 구조화된 HTML 파일 생성
        - 오프라인에서도 열람 가능
        - 브라우저에서 PDF로 변환 가능
        
        ### 💡 수동 방법 (항상 작동)
        1. **Ctrl+P** (Windows) 또는 **Cmd+P** (Mac)
        2. 대상: **'PDF로 저장'**
        3. **'기타 설정'** 클릭
        4. **'배경 그래픽'** 체크 ✅
        5. 여백: **'최소'** 선택 (선택사항)
        6. **저장** 클릭
        """)


# 사용 예시 (기존 코드에서 PDF 생성 부분을 교체)
if st.session_state.current_dev_mode:
    st.markdown("---")
    st.subheader("📄 전체 페이지 내보내기")
    
    # PDF 생성 옵션들
    generate_full_app_pdf()
    
    # 상태에 따른 안내
    if st.session_state.generated_roadmap:
        st.success("✅ 로드맵이 생성되어 있어 완전한 PDF를 만들 수 있습니다!")
    else:
        st.info("💡 로드맵을 먼저 생성하면 더 완전한 PDF를 얻을 수 있습니다.")


# 추가: 로드맵 확장 상태 관리를 위한 JavaScript 헬퍼
def inject_expand_all_script():
    """모든 로드맵 섹션을 확장하는 JavaScript"""
    expand_js = """
    <script>
    function expandAllSections() {
        // Streamlit expander 찾기
        const expanders = document.querySelectorAll('[data-testid="stExpander"]');
        console.log('Found expanders:', expanders.length);
        
        expanders.forEach((expander, index) => {
            const button = expander.querySelector('button');
            if (button) {
                const isExpanded = button.getAttribute('aria-expanded') === 'true';
                console.log(`Expander ${index}: expanded = ${isExpanded}`);
                
                if (!isExpanded) {
                    button.click();
                    console.log(`Clicked expander ${index}`);
                }
            }
        });
    }
    
    // 페이지 로드 후 실행
    setTimeout(expandAllSections, 1000);
    </script>
    """
    
    st.components.v1.html(expand_js, height=0)


# 로드맵 표시 시 자동 확장 스크립트 주입 (선택사항)
if st.session_state.generated_roadmap and st.session_state.current_dev_mode:
    with st.expander("🔧 개발자 도구"):
        if st.button("📖 모든 섹션 확장"):
            inject_expand_all_script()
            st.success("모든 로드맵 섹션을 확장했습니다. 이제 PDF를 생성하세요!")
