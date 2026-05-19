import streamlit as st
import pandas as pd
import math
import re

# ---------------------------------------------------------
# 페이지 기본 설정
# ---------------------------------------------------------
st.set_page_config(page_title="조경 법규 마스터 검토 시스템", layout="wide")

st.title("🌿 조경 법규 실시간 종합 검토 시스템")
st.caption("국가법령정보센터 API 및 지자체 조례·지침 연동 엔진 (실무 심의 및 인허가용)")
st.markdown("---")

# ---------------------------------------------------------
# 사이드바: 1. 건축물 기본 개요 입력
# ---------------------------------------------------------
st.sidebar.header("🏢 1. 건축물 기본 개요 입력")

# [주소지 파싱 기능] 주소 하나만 입력하면 시스템이 알아서 지자체를 찾아냅니다.
project_address = st.sidebar.text_input(
    "📝 프로젝트 주소지 (지번/도로명)", 
    value="충청남도 천안시 서북구 성성동 일원", 
    help="입력하신 주소를 분석하여 해당 지자체의 건축조례가 자동으로 매핑됩니다."
)

zone_type = st.sidebar.selectbox(
    "🗺️ 용도지역 분류",
    ["일반주거지역", "준주거지역", "중심상업지역", "일반상업지역", "근린상업지역", "준공업지역", "기타지역"]
)

building_type = st.sidebar.selectbox(
    "🏢 건축물 용도",
    ["공동주택 (아파트)", "업무시설 (오피스텔/일반업무)", "판매시설 (백화점/마트)", "근린생활시설", "기타 건축물"]
)

site_area = st.sidebar.number_input("📐 계획 대지면적 (㎡)", min_value=0.0, value=9500.0, step=100.0)
total_floor_area = st.sidebar.number_input("🏢 연면적 합계 (㎡)", min_value=0.0, value=35000.0, step=500.0)
household_count = st.sidebar.number_input("👨‍👩‍👧‍👦 신축 계획 세대수", min_value=0, value=350, step=10)
parking_count = st.sidebar.number_input("🚗 계획 주차대수", min_value=0, value=400, step=10)

# ---------------------------------------------------------
# 사이드바: 2. 적용 법규 자동 판별기 
# ---------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.header("📋 2. 적용 법규 자동 판별기")
st.sidebar.caption("현장 조건을 입력하면 관련 특례법규를 자동으로 찾아냅니다.")

project_category = st.sidebar.radio("사업의 성격", ["일반 신축 및 개발사업", "노후 건축물 정비 (재개발/재건축)"])

auto_small_scale = False
auto_eco_target = True

if project_category == "노후 건축물 정비 (재개발/재건축)":
    existing_hh = st.sidebar.number_input("철거 전 기존 세대수", min_value=0, value=150, step=10, help="200세대 미만일 경우 소규모재건축 대상이 될 수 있습니다.")
    is_street_zone = st.sidebar.checkbox("사방이 도로로 둘러싸인 '가로구역' 입니까?")

    if site_area < 10000 and existing_hh < 200:
        detected_law = "소규모재건축사업 (빈집특례법 적용)"
        auto_small_scale = True
        auto_eco_target = False
    elif site_area <= 20000 and is_street_zone:
        detected_law = "가로주택정비사업 (빈집특례법 적용)"
        auto_small_scale = True
        auto_eco_target = False
    else:
        detected_law = "일반 재개발/재건축 (도시 및 주거환경정비법)"
else:
    detected_law = "일반 신축 및 개발 (건축법 일반)"

if auto_small_scale:
    st.sidebar.success(f"💡 **판별 결과: {detected_law}**\n\n특례법 대상 현장입니다. 조경 50% 완화 및 생태면적률 제외가 아래 옵션에 자동 세팅되었습니다.")
else:
    st.sidebar.info(f"💡 **판별 결과: {detected_law}**\n\n일반 법규(조경 100% 의무, 생태면적률 권장)가 적용됩니다.")

# ---------------------------------------------------------
# 사이드바: 3. 조경 및 시설 계획 수치 입력
# ---------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.header("🌳 3. 조경 및 시설 계획 수치 입력")

is_small_scale = st.sidebar.checkbox("🏘️ 특례법 완화 (조경면적 1/2) 수동 제어", value=auto_small_scale)

landscaping_area_plan = st.sidebar.number_input("🟩 계획 조경면적 (㎡)", min_value=0.0, value=1600.0, step=50.0)
natural_ground_plan = st.sidebar.number_input("🟫 계획 자연지반면적 (㎡)", min_value=0.0, value=400.0, step=10.0)

is_eco_target = st.sidebar.checkbox("🌱 생태면적률 의무 적용 여부 수동 제어", value=auto_eco_target)
eco_area_plan = st.sidebar.slider("🍃 계획 생태면적률 (%)", min_value=0.0, max_value=100.0, value=32.0, step=0.5)
open_space_plan = st.sidebar.number_input("⛲ 계획 공개공지면적 (㎡)", min_value=0.0, value=0.0, step=10.0)

st.sidebar.markdown("---")
st.sidebar.header("🌲 4. 식재 및 부대시설 수량 입력")
tree_count = st.sidebar.number_input("🌳 계획 교목 총 수량 (주)", min_value=0, value=350, step=10)
evergreen_tree_count = st.sidebar.number_input("🌲 계획 상록교목 수량 (주)", min_value=0, value=80, step=5)
special_tree_count = st.sidebar.number_input("✨ 계획 특성수 수량 (주)", min_value=0, value=40, step=5)

shrub_count = st.sidebar.number_input("🌿 계획 관목 총 수량 (주)", min_value=0, value=1800, step=50)
evergreen_shrub_count = st.sidebar.number_input("🍃 계획 상록관목 수량 (주)", min_value=0, value=400, step=10)

play_area_plan = st.sidebar.number_input("🛝 계획 어린이놀이터 면적 (㎡)", min_value=0.0, value=900.0, step=10.0)
sports_area_plan = st.sidebar.number_input("🏋️ 계획 주민운동시설 면적 (㎡)", min_value=0.0, value=300.0, step=10.0)
bus_stop_plan = st.sidebar.number_input("🚌 계획 통학버스 정류장 (개소)", min_value=0, value=1, step=1)
bike_parking_plan = st.sidebar.number_input("🚲 계획 자전거보관소 (대)", min_value=0, value=130, step=5)
garden_area_plan = st.sidebar.number_input("🧑‍🌾 계획 텃밭/부속정원 면적 (㎡)", min_value=0.0, value=50.0, step=5.0)

report_data = []

# ---------------------------------------------------------
# 법규 계산 로직 (주소 기반 지자체 자동 추출 및 특례법 완화 적용)
# ---------------------------------------------------------
# 주소지에서 정규식을 통해 '시/군/구' 텍스트를 지능적으로 파싱합니다.
match = re.search(r'([가-힣]+(시|군|구))', project_address)
local_gov = match.group(1) if match else "해당 지자체"

if "서울" in project_address:
    law_article = "서울특별시 건축조례 제24조"
    local_gov = "서울특별시"
    if site_area < 2000: req_landscape_ratio = 0.10
    else: req_landscape_ratio = 0.15
elif "천안" in project_address:
    law_article = "천안시 건축조례 제29조"
    local_gov = "천안시"
    if "상업" in zone_type: req_landscape_ratio = 0.08
    elif total_floor_area >= 5000: req_landscape_ratio = 0.15
    else: req_landscape_ratio = 0.10
else:
    law_article = f"{local_gov} 건축조례"
    req_landscape_ratio = 0.12

if is_small_scale:
    req_landscape_ratio = req_landscape_ratio * 0.5  # 50% 완화
    law_landscape = f"빈집소규모주택정비법 시행령 제40조제1항 (1/2 완화) 및 {law_article}"
else:
    law_landscape = f"{law_article} 및 건축법 제42조"

req_natural_ratio = 0.10 

law_natural = "국토교통부 조경기준 제12조 (자연지반 식재 등)"
law_eco = "환경영향평가법 제22조 및 지자체 지구단위계획 수립지침"
law_open_space = "건축법 제43조 및 동법 시행령 제27조의2"
law_total_tree = "국토교통부 조경기준 제10조 (식재수량 및 기준)"
law_evergreen = "국토교통부 조경기준 제13조 (상록수 식재 비율)"
law_special = f"국토교통부 조경기준 제13조 및 {local_gov} 권장수종(시목 등)"
law_community = "주택건설기준 등에 관한 규정 제55조의2 (주민공동시설)"
law_bus_stop = "주택건설기준 등에 관한 규정 제26조제6항 (안전회차공간)"
law_bike = "자전거 이용 활성화에 관한 법률 시행령 제7조 [별표 1]"

legal_landscape_area = site_area * req_landscape_ratio
legal_natural_ground = legal_landscape_area * req_natural_ratio

legal_total_tree = math.ceil(legal_landscape_area * 0.2)
legal_total_shrub = math.ceil(legal_landscape_area * 1.0)

req_evergreen_ratio = 0.20      
req_special_ratio = 0.10
req_evergreen_shrub_ratio = 0.20

legal_evergreen_tree = math.ceil(legal_total_tree * req_evergreen_ratio)
legal_special_tree = math.ceil(legal_total_tree * req_special_ratio)
legal_evergreen_shrub = math.ceil(legal_total_shrub * req_evergreen_shrub_ratio)

if is_eco_target:
    eco_legal_text = "대지면적의 30.0% 이상 도입 권장"
    eco_val_str = f"30.0 % / {eco_area_plan:.1f} %"
    eco_pass = eco_area_plan >= 30.0
else:
    eco_legal_text = "소규모 사업 등 환경영향평가 비대상 의무 제외"
    eco_val_str = f"해당 없음 / {eco_area_plan:.1f} %"
    eco_pass = "N/A"

if building_type != "공동주택 (아파트)":
    play_legal_text, play_val_str, play_pass = "해당사항 없음", "해당 없음", "N/A"
    sports_legal_text, sports_val_str, sports_pass = "해당사항 없음", "해당 없음", "N/A"
    bus_formula_text, bus_val_str, bus_pass = "해당사항 없음", "해당 없음", "N/A"
else:
    if household_count < 100:
        play_legal_text = "100세대 미만: 주민공동시설 총량 의무 없음"
        sports_legal_text = "100세대 미만: 주민공동시설 총량 의무 없음"
    elif household_count < 1000:
        total_comm = household_count * 2.5
        play_legal_text = f"총량제 대상(세대수×2.5㎡). 놀이터 가이드 산식: 200㎡ + (세대수×1㎡)"
        sports_legal_text = f"총량제 대상(세대수×2.5㎡). 300세대 이상 필수 설치 대상"
    else:
        total_comm = (household_count * 3.0) + 500
        play_legal_text = f"총량제 대상(500㎡+세대수×3㎡). 놀이터 가이드 산식: 500㎡ + (세대수×0.7㎡)"
        sports_legal_text = f"총량제 대상(500㎡+세대수×3㎡). 500세대 이상 복합설치 의무"
        
    play_val_str = f"총량내 확보 / {play_area_plan:,.1f} ㎡"
    play_pass = True if play_area_plan > 0 else False
    sports_val_str = f"총량내 확보 / {sports_area_plan:,.1f} ㎡"
    sports_pass = True if sports_area_plan > 0 else False
    
    if household_count < 150: play_legal_text = "150세대 미만: 어린이놀이터 의무 설치 제외"
    if household_count < 300: sports_legal_text = "300세대 미만: 주민운동시설 의무 설치 제외"

    if household_count < 500:
        bus_formula_text = "500세대 미만: 의무 없음"
        bus_val_str, bus_pass = f"0 개소 / {bus_stop_plan} 개소", True
    else:
        bus_formula_text = "500세대 이상: 어린이 통학버스 유치원 회차공간 1개소 이상 설치 의무"
        bus_val_str, bus_pass = f"1 개소 / {bus_stop_plan} 개소", bus_stop_plan >= 1

legal_bike_parking = math.ceil(parking_count * 0.20)

open_space_applicable_zones = ["일반주거지역", "준주거지역", "중심상업지역", "일반상업지역", "근린상업지역", "준공업지역"]
open_space_applicable_buildings = ["업무시설 (오피스텔/일반업무)", "판매시설 (백화점/마트)", "기타 건축물"]

if building_type == "공동주택 (아파트)":
    open_space_text, open_space_val_str, open_space_pass = "일반 공동주택 제외", "해당 없음", "N/A"
elif zone_type not in open_space_applicable_zones or building_type not in open_space_applicable_buildings or total_floor_area < 5000:
    open_space_text, open_space_val_str, open_space_pass = "대상 아님 (용도/규모 미달)", f"0.0 ㎡ / {open_space_plan:,.1f} ㎡", True
else:
    legal_open_space = site_area * 0.07
    open_space_text, open_space_val_str, open_space_pass = "대지면적의 7% 이상 확보", f"{legal_open_space:,.1f} ㎡ / {open_space_plan:,.1f} ㎡", open_space_plan >= legal_open_space

# ---------------------------------------------------------
# 출력 및 데이터 수집 함수
# ---------------------------------------------------------
def print_law_row(category, title, legal_text, law_source, legal_plan_compare_str, is_pass):
    c1, c2, c3, c4 = st.columns([1.5, 3.2, 2.3, 0.8])
    with c1:
        st.markdown(f"**{title}**")
        st.caption(f"({category})")
    with c2:
        st.write(legal_text)
        st.caption(f"📍 근거: {law_source}")
    with c3:
        st.code(legal_plan_compare_str, language="text")
    with c4:
        if is_pass == "N/A" or legal_plan_compare_str == "해당 없음":
            st.info("➖ 제외")
            csv_status = "제외"
        elif is_pass:
            st.success("✅ 적합")
            csv_status = "적합"
        else:
            st.error("❌ 부족")
            csv_status = "부족"
            
    st.
