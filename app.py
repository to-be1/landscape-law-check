import streamlit as st
import math
import requests
import urllib3
import xml.etree.ElementTree as ET
import pandas as pd  # 엑셀 변환을 위한 데이터 분석 라이브러리 추가

# SSL 경고창 숨김
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 1. 화면 기본 설정
st.set_page_config(page_title="조경 법규 자동 검토", layout="wide")
st.title("🌿 조경 법규 실시간 자동 검토 프로그램")
st.write("이재형 님의 첫 번째 AI 자동화 프로젝트입니다.")

# 글자 짤림 방지 CSS
st.markdown("""
    <style>
    [data-testid="stMetricValue"] > div { white-space: normal !important; word-break: keep-all !important; font-size: 20px !important; line-height: 1.3 !important; }
    [data-testid="stMetricLabel"] > div { white-space: normal !important; word-break: keep-all !important; }
    </style>
""", unsafe_allow_html=True)

st.sidebar.header("📝 프로젝트 개요 입력")

regions = ["수원시", "천안시", "아산시", "서울 강남구", "서울 종로구", "성남시", "화성시", "청주시", "전주시", "제주시"]
region = st.sidebar.selectbox("지자체 선택", regions)

st.sidebar.markdown("---")

# 1. 기본 건축 개요
st.sidebar.subheader("1. 기본 건축 개요")
zone_type = st.sidebar.selectbox("용도지역 선택", ["일반주거지역", "전용주거지역", "준주거지역", "중심상업지역", "일반상업지역", "근린상업지역", "유통상업지역", "전용공업지역", "일반공업지역", "준공업지역", "녹지지역"])
building_type = st.sidebar.selectbox("건축물 용도", ["공동주택 (아파트)", "업무시설 (오피스텔/일반업무)", "판매시설 (백화점/마트)", "문화 및 집회시설", "숙박시설", "종교시설", "공장"])

site_area = st.sidebar.number_input("대지면적 (㎡)", value=15781.40, step=100.0)
total_floor_area = st.sidebar.number_input("연면적 (㎡)", value=50000.0, step=1000.0)
household_count = st.sidebar.number_input("세대수 (세대)", value=440, step=10)
parking_count = st.sidebar.number_input("자동차 주차대수 (대)", value=361, step=10)

# 2. 면적 및 시설 계획
st.sidebar.subheader("2. 면적 및 시설 계획")
landscaping_area_plan = st.sidebar.number_input("계획 조경면적 (㎡)", value=2840.65, step=50.0)
natural_ground_plan = st.sidebar.number_input("계획 자연지반 면적 (㎡)", value=284.07, step=10.0)
eco_area_plan = st.sidebar.number_input("계획 생태면적률 (%)", value=30.0, step=1.0)
open_space_plan = st.sidebar.number_input("계획 공개공지 면적 (㎡)", value=0.0, step=10.0)

st.sidebar.markdown("**[부대 및 복리시설]**")
play_area_plan = st.sidebar.number_input("어린이놀이터 계획 면적 (㎡)", value=640.0, step=10.0)
sports_area_plan = st.sidebar.number_input("주민운동시설 계획 면적 (㎡)", value=150.0, step=10.0)
bike_parking_plan = st.sidebar.number_input("자전거보관소 계획 (대)", value=113, step=5)
bus_stop_plan = st.sidebar.number_input("어린이 통학버스 정류장 (개소)", value=1, step=1)
garden_area_plan = st.sidebar.number_input("텃밭 / 부속정원 계획 면적 (㎡)", value=50.0, step=5.0)

# 3. 식재 계획
st.sidebar.subheader("3. 식재 계획")
tree_count = st.sidebar.number_input("계획 교목 전체 수량 (주)", value=568, step=10)
evergreen_tree_count = st.sidebar.number_input(" - 상록교목 수량 (주)", value=114, step=5)
special_tree_count = st.sidebar.number_input(" - 특성수 수량 (주)", value=57, step=5)
shrub_count = st.sidebar.number_input("계획 관목 전체 수량 (주)", value=2841, step=100)
evergreen_shrub_count = st.sidebar.number_input(" - 상록관목 수량 (주)", value=114, step=10)

# 이재형 님의 마스터키
api_key = "8575"

st.markdown("---")

# 4. 검사 실행 및 API 실시간 연동
if st.sidebar.button("법규 적합성 검사 실행"):
    
    # [추가] 엑셀 다운로드를 위해 데이터를 모아둘 빈 바구니(리스트) 생성
    report_data = []
    
    # ---------------------------------------------------------
    # 법제처 API 실시간 호출
    # ---------------------------------------------------------
    api_status_msg = "확인 중..."
    law_date_str = ""
    try:
        api_url = f"https://www.law.go.kr/DRF/lawSearch.do?OC={api_key}&target=admrul&type=XML&query=조경기준"
        res = requests.get(api_url, verify=False, timeout=5)
        
        if res.status_code == 200:
            root = ET.fromstring(res.text)
            total_cnt = int(root.find('totalCnt').text)
            if total_cnt > 0:
                law_item = root.find('.//admrul')
                law_date = law_item.find('시행일자').text
                law_date_str = f"{law_date[:4]}-{law_date[4:6]}-{law_date[6:]}"
                api_status_msg = f"🟢 실시간 연동됨 (최신 시행일자: {law_date_str})"
            else:
                api_status_msg = "🟡 데이터 없음"
        else:
            api_status_msg = "🔴 API 응답 오류"
    except Exception as e:
        api_status_msg = "🔴 통신 실패 (방화벽 등 확인)"
        
    col_header, col_api = st.columns([7, 3])
    with col_header:
        st.subheader(f"📊 {region} [{zone_type} / {building_type}] 검토 결과")
    with col_api:
        st.info(f"🔗 **국토부 조경기준:** {api_status_msg}")
    
    # ---------------------------------------------------------
    # 법규 계산 로직
    # ---------------------------------------------------------
    req_natural_ratio = 0.10
    if "상업" in zone_type:
        req_landscape_ratio = 0.05 if total_floor_area < 2000 else 0.08
    elif "공업" in zone_type:
        req_landscape_ratio = 0.05
    else:
        req_landscape_ratio = 0.15 if "서울" in region else 0.10
        
    law_landscape = f"{region} 건축조례"
    law_natural = "국토교통부 조경기준 제12조"
    law_eco = "환경영향평가 / 지구단위계획"
    
    legal_landscape_area = site_area * req_landscape_ratio
    legal_natural_ground = legal_landscape_area * req_natural_ratio
    
    legal_total_tree = math.ceil(landscaping_area_plan * 0.2)
    legal_total_shrub = math.ceil(landscaping_area_plan * 1.0)
    
    req_evergreen_ratio = 0.20      
    req_special_ratio = 0.10
    req_evergreen_shrub_ratio = 0.20
    
    legal_evergreen_tree = math.ceil(tree_count * req_evergreen_ratio)
    legal_special_tree = math.ceil(tree_count * req_special_ratio)
    legal_evergreen_shrub = math.ceil(shrub_count * req_evergreen_shrub_ratio)
    
    law_total_tree = "국토교통부 조경기준 제10조"
    law_evergreen = "국토교통부 조경기준 제13조"
    law_special = "지자체 조경기준"

    law_housing = "주택건설기준 등에 관한 규정"
    law_bike = "자전거이용 활성화에 관한 법률 시행령"
    
    if building_type != "공동주택 (아파트)":
        play_val_str, play_pass, play_formula_text = "해당사항 없음", "N/A", "비대상 건축물"
        sports_val_str, sports_pass, sports_formula_text = "해당사항 없음", "N/A", "비대상 건축물"
        bus_val_str, bus_pass, bus_formula_text = "해당사항 없음", "N/A", "비대상 건축물"
    else:
        if household_count < 150:
            play_formula_text = "150세대 미만: 의무 없음"
            play_val_str, play_pass = f"0 ㎡ / {play_area_plan:,.1f} ㎡", True
        elif household_count < 300:
            play_formula_text = "150~300미만: 적정면적 조율"
            play_val_str, play_pass = f"적정면적 / {play_area_plan:,.1f} ㎡", True
        elif household_count < 500:
            legal_play = 200 + (household_count * 1.0)
            play_formula_text = "300~500미만: 200㎡ + (세대수×1㎡)"
            play_val_str, play_pass = f"{legal_play:,.1f} ㎡ / {play_area_plan:,.1f} ㎡", play_area_plan >= legal_play
        else:
            legal_play = 500 + (household_count * 0.7)
            play_formula_text = "500세대 이상: 500㎡ + (세대수×0.7㎡)"
            play_val_str, play_pass = f"{legal_play:,.1f} ㎡ / {play_area_plan:,.1f} ㎡", play_area_plan >= legal_play
            
        if household_count < 300:
            sports_formula_text = "300세대 미만: 의무 없음"
            sports_val_str, sports_pass = f"0 ㎡ / {sports_area_plan:,.1f} ㎡", True
        else:
            sports_formula_text = "300세대 이상: 필수 설치 (조례 참조)"
            sports_val_str, sports_pass = f"필수 확보 / {sports_area_plan:,.1f} ㎡", sports_area_plan > 0
            
        if household_count < 500:
            bus_formula_text = "500세대 미만: 의무 없음"
            bus_val_str, bus_pass = f"0 개소 / {bus_stop_plan} 개소", True
        else:
            bus_formula_text = "500세대 이상: 1개소 이상 설치"
            bus_val_str, bus_pass = f"1 개소 / {bus_stop_plan} 개소", bus_stop_plan >= 1

    legal_bike_parking = math.ceil(parking_count * 0.20)
    
    open_space_applicable_zones = ["일반주거지역", "준주거지역", "중심상업지역", "일반상업지역", "근린상업지역", "유통상업지역", "준공업지역"]
    open_space_applicable_buildings = ["업무시설 (오피스텔/일반업무)", "판매시설 (백화점/마트)", "문화 및 집회시설", "숙박시설", "종교시설"]
    
    if building_type == "공동주택 (아파트)":
        open_space_text, open_space_val_str, open_space_pass = "일반 공동주택 제외", "해당 없음", "N/A"
    elif zone_type not in open_space_applicable_zones or building_type not in open_space_applicable_buildings or total_floor_area < 5000:
        open_space_text, open_space_val_str, open_space_pass = "대상 아님 (용도/지역/규모 미달)", f"0.0 ㎡ / {open_space_plan:,.1f} ㎡", True
    else:
        legal_open_space = site_area * 0.07
        open_space_text, open_space_val_str, open_space_pass = "대지면적의 7% 이상", f"{legal_open_space:,.1f} ㎡ / {open_space_plan:,.1f} ㎡", open_space_plan >= legal_open_space

    # ---------------------------------------------------------
    # 출력 및 데이터 수집 함수 (엑셀용 데이터 자동 수집 기능 추가)
    # ---------------------------------------------------------
    def print_row(category, title, legal_text, law_source, legal_plan_compare_str, is_pass):
        c1, c2, c3, c4 = st.columns([1, 1.8, 2.2, 0.8])
        c1.metric("항목", title)
        c2.metric("법적 기준 및 산식", legal_text)
        with c2: st.caption(f"📍 근거: {law_source}")
        c3.metric("법정 요구치 / 계획 수치", legal_plan_compare_str)
        
        pass_result = ""
        with c4:
            st.write("") 
            if is_pass == "N/A" or legal_plan_compare_str == "해당 없음": 
                st.info("➖ 제외")
                pass_result = "제외"
            elif is_pass: 
                st.success("✅ 적합")
                pass_result = "적합"
            else: 
                st.error("❌ 부족")
                pass_result = "부족"
        st.write("")
        
        # 엑셀 리포트 바구니에 현재 항목 데이터 담기
        report_data.append({
            "검토 분류": category,
            "검토 항목": title,
            "법적 기준 및 산식": legal_text,
            "관련 근거(법령/조례)": law_source,
            "법정 요구치 / 계획 수치": legal_plan_compare_str,
            "적합 여부": pass_result
        })

    # 화면 렌더링 및 엑셀 데이터 적재
    st.markdown("#### 1. 대지, 조경 및 생태 면적 검토")
    cat1 = "1. 면적 검토"
    print_row(cat1, "조경 면적", f"대지면적의 {req_landscape_ratio*100}%", law_landscape, f"{legal_landscape_area:,.1f} ㎡ / {landscaping_area_plan:,.1f} ㎡", landscaping_area_plan >= legal_landscape_area)
    print_row(cat1, "자연 지반", f"조경면적의 {req_natural_ratio*100}%", law_natural, f"{legal_natural_ground:,.1f} ㎡ / {natural_ground_plan:,.1f} ㎡", natural_ground_plan >= legal_natural_ground)
    print_row(cat1, "생태면적률", "대지면적의 30.0% 이상", law_eco, f"30.0 % / {eco_area_plan:.1f} %", eco_area_plan >= 30.0)
    print_row(cat1, "공개 공지", open_space_text, "건축법 제43조", open_space_val_str, open_space_pass)

    st.markdown("---")
    st.markdown("#### 2. 수목 식재 총량 및 세부 수량 검토")
    cat2 = "2. 식재 검토"
    print_row(cat2, "전체 교목 수량", "조경면적 1㎡당 0.2주 이상", law_total_tree, f"{legal_total_tree:,.0f} 주 / {tree_count:,.0f} 주", tree_count >= legal_total_tree)
    print_row(cat2, " - 상록 교목", f"전체 교목 수량의 {req_evergreen_ratio*100}% 이상", law_evergreen, f"{legal_evergreen_tree:,.0f} 주 / {evergreen_tree_count:,.0f} 주", evergreen_tree_count >= legal_evergreen_tree)
    print_row(cat2, " - 특성수 수량", f"전체 교목 수량의 {req_special_ratio*100}% 이상", law_special, f"{legal_special_tree:,.0f} 주 / {special_tree_count:,.0f} 주", special_tree_count >= legal_special_tree)
    print_row(cat2, "전체 관목 수량", "조경면적 1㎡당 1.0주 이상", law_total_tree, f"{legal_total_shrub:,.0f} 주 / {shrub_count:,.0f} 주", shrub_count >= legal_total_shrub)
    print_row(cat2, " - 상록 관목", f"전체 관목 수량의 {req_evergreen_shrub_ratio*100}% 이상", law_evergreen, f"{legal_evergreen_shrub:,.0f} 주 / {evergreen_shrub_count:,.0f} 주", evergreen_shrub_count >= legal_evergreen_shrub)

    st.markdown("---")
    st.markdown("#### 3. 부대 및 복리시설 검토 (공동주택 기준)")
    cat3 = "3. 부대/복리시설 검토"
    print_row(cat3, "어린이놀이터", play_formula_text, law_housing, play_val_str, play_pass)
    print_row(cat3, "주민운동시설", sports_formula_text, law_housing, sports_val_str, sports_pass)
    print_row(cat3, "통학버스 정류장", bus_formula_text, law_housing, bus_val_str, bus_pass)
    print_row(cat3, "자전거 보관소", "자동차 주차대수의 20% 이상", law_bike, f"{legal_bike_parking:,.0f} 대 / {bike_parking_plan:,.0f} 대", bike_parking_plan >= legal_bike_parking)
    print_row(cat3, "텃밭 / 부속정원", "설치 권장 (녹색건축인증 / 지자체 조례)", "녹색건축인증(G-SEED) 등", f"권장 / {garden_area_plan:,.1f} ㎡", True)

    # ---------------------------------------------------------
    # [새로운 기능] 엑셀 다운로드 버튼 생성
    # ---------------------------------------------------------
    st.markdown("---")
    st.subheader("📥 검토 결과 보고서 출력")
    
    # 파이썬의 pandas 기능을 사용해 리스트를 데이터프레임(엑셀표)으로 변환
    df_report = pd.DataFrame(report_data)
    
    # 엑셀에서 한글이 절대 깨지지 않도록 강제로 바이트(Bytes) 변환 꼬리표(BOM) 추가
    csv_data = df_report.to_csv(index=False).encode('utf-8-sig')
    
    st.download_button(
        label="📊 조경법규 검토 결과 엑셀(CSV) 다운로드",
        data=csv_data,
        file_name=f"조경법규검토결과_{region}_{building_type}.csv",
        mime="text/csv"
    )
    st.caption("※ 다운로드된 CSV 파일은 엑셀에서 바로 열람하고 표 서식으로 편집하여 보고서로 활용하실 수 있습니다.")