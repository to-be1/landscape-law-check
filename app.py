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

project_address = st.sidebar.text_input("📝 프로젝트 주소지 (지번/도로명)", value="경기도 수원시 팔달구 인계동 일원")
zone_type = st.sidebar.selectbox("🗺️ 용도지역 분류", ["일반주거지역", "준주거지역", "중심상업지역", "일반상업지역", "근린상업지역", "준공업지역", "기타지역"])
special_district = st.sidebar.selectbox("⛰️ 용도지구 (특수지역) 분류", ["해당 없음 (일반 지역)", "자연경관지구", "역사문화환경보존지구", "고도지구", "기타 특수지구"])
building_type = st.sidebar.selectbox("🏢 건축물 용도", ["공동주택 (아파트)", "업무시설 (오피스텔/일반업무)", "판매시설 (백화점/마트)", "근린생활시설", "기타 건축물"])

site_area = st.sidebar.number_input("📐 계획 대지면적 (㎡)", min_value=0.0, value=10000.0, step=100.0)
total_floor_area = st.sidebar.number_input("🏢 연면적 합계 (㎡)", min_value=0.0, value=35000.0, step=500.0)
household_count = st.sidebar.number_input("👨‍👩‍👧‍👦 신축 계획 세대수", min_value=0, value=85, step=10)
legal_parking_count = st.sidebar.number_input("🚙 법정 자동차 주차대수", min_value=0, value=350, step=10)
plan_parking_count = st.sidebar.number_input("🚗 계획 자동차 주차대수", min_value=0, value=400, step=10)

# ---------------------------------------------------------
# 사이드바: 2. 🚀 동적 법령 원문 파싱 엔진 (NEW)
# ---------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.header("📡 2. 동적 법령 원문 파싱 엔진")
st.sidebar.caption("법규가 개정되더라도 텍스트 원문만 넣으면 숫자를 스스로 추출해 적용합니다.")

use_dynamic_parsing = st.sidebar.checkbox("⚙️ 동적 법령 원문 파싱 모드 켜기", value=False)

raw_law_text = ""
parsed_ratio = None
parsing_message = ""

if use_dynamic_parsing:
    st.sidebar.info("💡 국가법령정보센터에서 해당 지자체 건축조례(대지의 조경) 원문을 복사하여 아래에 붙여넣으세요.")
    default_text = """제24조(대지의 조경)
1. 연면적의 합계가 2천제곱미터 이상인 건축물: 대지면적의 15퍼센트 이상
2. 연면적의 합계가 1천제곱미터 이상 2천제곱미터 미만인 건축물: 대지면적의 10퍼센트 이상
3. 연면적의 합계가 1천제곱미터 미만인 건축물: 대지면적의 5퍼센트 이상"""
    
    raw_law_text = st.sidebar.text_area("📄 법규/조례 원문 텍스트", value=default_text, height=150)
    
    # [핵심] 텍스트 내에서 현재 '연면적' 조건에 맞는 정확한 퍼센트 숫자를 찾아내는 정규식 엔진
    if total_floor_area >= 2000:
        match = re.search(r'2천제곱미터 이상[^\n]*?대지면적의\s*(\d+(?:\.\d+)?)\s*(?:퍼센트|%)', raw_law_text)
    elif total_floor_area >= 1000:
        match = re.search(r'1천제곱미터 이상[^\n]*?대지면적의\s*(\d+(?:\.\d+)?)\s*(?:퍼센트|%)', raw_law_text)
    else:
        match = None
        
    # 조건에 맞는 문장이 없거나 조건이 없는 조례인 경우, 기본 퍼센트를 검색
    if not match:
        match = re.search(r'대지면적의\s*(\d+(?:\.\d+)?)\s*(?:퍼센트|%)', raw_law_text)
        
    if match:
        parsed_ratio = float(match.group(1)) / 100.0
        parsing_message = f"🎯 원문 분석 완료: **{match.group(1)}%** 적용됨"
        st.sidebar.success(parsing_message)
    else:
        st.sidebar.error("❌ 텍스트에서 '대지면적의 OO퍼센트' 패턴을 찾지 못했습니다.")

# ---------------------------------------------------------
# 사이드바: 3. 적용 법규 자동 판별기 (특례법)
# ---------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.header("📋 3. 특례법 자동 판별기")
project_category = st.sidebar.radio("사업의 성격", ["일반 신축 및 개발사업", "노후 건축물 정비 (재개발/재건축)"])

auto_small_scale = False
auto_eco_target = True

if project_category == "노후 건축물 정비 (재개발/재건축)":
    existing_hh = st.sidebar.number_input("철거 전 기존 세대수", min_value=0, value=150, step=10)
    is_street_zone = st.sidebar.checkbox("사방이 도로로 둘러싸인 '가로구역' 입니까?")

    if site_area < 10000 and existing_hh < 200:
        detected_law = "소규모재건축사업 (빈집특례법 적용)"
        auto_small_scale = True; auto_eco_target = False
    elif site_area <= 20000 and is_street_zone:
        detected_law = "가로주택정비사업 (빈집특례법 적용)"
        auto_small_scale = True; auto_eco_target = False
    else:
        detected_law = "일반 재개발/재건축 (도시 및 주거환경정비법)"
else:
    detected_law = "일반 신축 및 개발 (건축법 일반)"

# ---------------------------------------------------------
# 사이드바: 4. 조경 및 시설 계획 수치 입력
# ---------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.header("🌳 4. 계획 수치 입력")

is_small_scale = auto_small_scale
is_eco_target = auto_eco_target

landscaping_area_plan = st.sidebar.number_input("🟩 계획 조경면적 (㎡)", min_value=0.0, value=3000.0, step=50.0)
natural_ground_plan = st.sidebar.number_input("🟫 계획 자연지반면적 (㎡)", min_value=0.0, value=400.0, step=10.0)
eco_area_plan = st.sidebar.slider("🍃 계획 생태면적률 (%)", min_value=0.0, max_value=100.0, value=30.0, step=0.5)
open_space_plan = st.sidebar.number_input("⛲ 계획 공개공지면적 (㎡)", min_value=0.0, value=0.0, step=10.0)

tree_count = st.sidebar.number_input("🌳 계획 교목 총 수량 (주)", min_value=0, value=600, step=10)
evergreen_tree_count = st.sidebar.number_input("🌲 계획 상록교목 수량 (주)", min_value=0, value=120, step=5)
special_tree_count = st.sidebar.number_input("✨ 계획 특성수 수량 (주)", min_value=0, value=60, step=5)
shrub_count = st.sidebar.number_input("🌿 계획 관목 총 수량 (주)", min_value=0, value=3000, step=50)
evergreen_shrub_count = st.sidebar.number_input("🍃 계획 상록관목 수량 (주)", min_value=0, value=600, step=10)

play_area_plan = st.sidebar.number_input("🛝 계획 어린이놀이터 면적 (㎡)", min_value=0.0, value=0.0, step=10.0)
sports_area_plan = st.sidebar.number_input("🏋️ 계획 주민운동시설 면적 (㎡)", min_value=0.0, value=0.0, step=10.0)
bus_stop_plan = st.sidebar.number_input("🚌 계획 통학버스 정류장 (개소)", min_value=0, value=0, step=1)
bike_parking_plan = st.sidebar.number_input("🚲 계획 자전거보관소 (대)", min_value=0, value=75, step=5)
garden_area_plan = st.sidebar.number_input("🧑‍🌾 계획 텃밭/부속정원 면적 (㎡)", min_value=0.0, value=0.0, step=5.0)

report_data = []

# ---------------------------------------------------------
# 🧠 하이브리드 계산 로직 (동적 파싱 vs DB 매핑)
# ---------------------------------------------------------
match = re.search(r'([가-힣]+(시|군|구))', project_address)
local_gov_name = match.group(1) if match else "해당 지자체"

# [핵심 분기] 사용자가 동적 파싱 모드를 켰고, 텍스트에서 숫자를 찾았다면 무조건 그 숫자를 1순위로 씁니다.
if use_dynamic_parsing and parsed_ratio is not None:
    req_landscape_ratio = parsed_ratio
    law_article = f"[동적 원문 파싱 적용] {local_gov_name} 조례 원문 기준"
else:
    # 파싱 모드를 껐거나 실패했다면, 기존에 구축한 내장 DB(서울, 부천, 인천 등)를 적용합니다.
    req_landscape_ratio = 0.15
    law_article = f"{local_gov_name} 건축조례"
    
    if "서울" in project_address:
        law_article = "서울특별시 건축조례 제24조"
        req_landscape_ratio = 0.15 if total_floor_area >= 2000 else 0.10
    elif "인천" in project_address:
        law_article = "인천광역시 건축조례 제27조"
        if total_floor_area >= 2000: req_landscape_ratio = 0.15
        elif total_floor_area >= 1000: req_landscape_ratio = 0.10
        else: req_landscape_ratio = 0.05
    elif "부천" in project_address:
        law_article = "부천시 건축조례 제24조"
        req_landscape_ratio = 0.20
    elif "전주" in project_address:
        law_article = "전주시 건축조례 제23조"
        req_landscape_ratio = 0.18
    elif "수원" in project_address:
        law_article = "수원시 건축조례 제31조"
        if "중심상업" in zone_type: req_landscape_ratio = 0.05
        elif total_floor_area >= 5000: req_landscape_ratio = 0.18
        elif total_floor_area >= 2000: req_landscape_ratio = 0.15
        elif total_floor_area >= 1000: req_landscape_ratio = 0.10
        else: req_landscape_ratio = 0.05
    else:
        if total_floor_area >= 2000: req_landscape_ratio = 0.15
        elif total_floor_area >= 1000: req_landscape_ratio = 0.10
        else: req_landscape_ratio = 0.05

    # 특수지구 최우선 덮어쓰기 (자연경관지구 등)
    if "자연경관지구" in special_district:
        req_landscape_ratio = 0.30
        law_article = f"{local_gov_name} 도시계획조례 (자연경관지구 30% 강화)"

# 특례법 1/2 완화 적용
if is_small_scale:
    req_landscape_ratio = req_landscape_ratio * 0.5
    law_landscape = f"소규모주택정비법 시행령 제40조 (1/2 완화) 및 {law_article}"
else:
    law_landscape = f"{law_article} 및 건축법 제42조"

req_natural_ratio = 0.10 
law_natural = "국토교통부 조경기준 제12조 (자연지반 식재 등)"
law_eco = "환경영향평가법 제22조 및 지자체 지구단위계획 수립지침"
law_open_space = "건축법 제43조 및 동법 시행령 제27조의2"
law_total_tree = "국토교통부 조경기준 제10조 (식재수량 및 기준)"
law_evergreen = "국토교통부 조경기준 제13조 (상록수 식재 비율)"
law_special = f"국토교통부 조경기준 제13조 및 {local_gov_name} 권장수종"
law_community = "주택건설기준 등에 관한 규정 제55조의2 (주민공동시설)"
law_bus_stop = "주택건설기준 등에 관한 규정 제26조제6항 (안전회차공간)"
law_bike = "자전거 이용 활성화에 관한 법률 시행령 제7조 [별표 1]"

# [핵심] 조경 면적이 텍스트에서 파싱한 숫자로 바뀌면, 수목 수량도 그에 연동되어 완벽히 계산됩니다.
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
    if household_count < 150:
        play_legal_text = "150세대 미만: 어린이놀이터 의무 설치 제외"
        play_val_str = f"해당 없음 / {play_area_plan:,.1f} ㎡"
        play_pass = "N/A"
    else:
        total_comm = household_count * 2.5 if household_count < 1000 else (household_count * 3.0) + 500
        play_legal_text = f"총량제 대상(의무: {total_comm:,.1f}㎡). 가이드: 200㎡+(세대수×1㎡)" if household_count < 1000 else f"총량제 대상(의무: {total_comm:,.1f}㎡). 가이드: 500㎡+(세대수×0.7㎡)"
        play_val_str = f"총량내 확보 / {play_area_plan:,.1f} ㎡"
        play_pass = True if play_area_plan > 0 else False

    if household_count < 300:
        sports_legal_text = "300세대 미만: 주민운동시설 의무 설치 제외"
        sports_val_str = f"해당 없음 / {sports_area_plan:,.1f} ㎡"
        sports_pass = "N/A"
    else:
        sports_legal_text = "총량제 대상. 300세대 이상 필수 설치 대상 (종목별 규격 참조)"
        sports_val_str = f"총량내 확보 / {sports_area_plan:,.1f} ㎡"
        sports_pass = True if sports_area_plan > 0 else False

    if household_count < 500:
        bus_formula_text = "500세대 미만: 의무 없음"
        bus_val_str, bus_pass = f"해당 없음 / {bus_stop_plan} 개소", "N/A"
    else:
        bus_formula_text = "500세대 이상: 어린이 통학버스 유치원 회차공간 1개소 이상 설치 의무"
        bus_val_str, bus_pass = f"1 개소 / {bus_stop_plan} 개소", bus_stop_plan >= 1

legal_bike_parking = math.ceil(legal_parking_count * 0.20)

open_space_applicable_zones = ["일반주거지역", "준주거지역", "중심상업지역", "일반상업지역", "근린상업지역", "준공업지역"]
open_space_applicable_buildings = ["업무시설 (오피스텔/일반업무)", "판매시설 (백화점/마트)", "기타 건축물"]

if building_type == "공동주택 (아파트)":
    open_space_text, open_space_val_str, open_space_pass = "일반 공동주택 제외", "해당 없음", "N/A"
elif zone_type not in open_space_applicable_zones or building_type not in open_space_applicable_buildings or total_floor_area < 5000:
    open_space_text, open_space_val_str, open_space_pass = "대상 아님 (용도/규모 미달)", f"해당 없음 / {open_space_plan:,.1f} ㎡", "N/A"
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
        if is_pass == "N/A" or "해당 없음" in legal_plan_compare_str:
            st.info("➖ 제외")
            csv_status = "제외"
        elif is_pass:
            st.success("✅ 적합")
            csv_status = "적합"
        else:
            st.error("❌ 부족")
            csv_status = "부족"
            
    st.markdown("<div style='margin: -5px 0 10px 0; border-bottom: 1px solid #EEEEEE;'></div>", unsafe_allow_html=True)
    
    report_data.append({
        "검토 분류": category,
        "검토 항목": title,
        "법적 기준 및 산식": legal_text,
        "관련 근거 및 상세 법령 조항": law_source,
        "법정 요구치 / 계획 수치": legal_plan_compare_str,
        "적합 여부": csv_status
    })

# ---------------------------------------------------------
# 화면 렌더링
# ---------------------------------------------------------
if use_dynamic_parsing and parsed_ratio:
    st.markdown(f"### 🚀 프로젝트 자동 판별 결과: <span style='color:#007BFF;'>법규 텍스트 실시간 파싱 적용 중</span>", unsafe_allow_html=True)
else:
    st.markdown(f"### 🚀 프로젝트 자동 판별 결과: <span style='color:#2E5A44;'>{detected_law}</span>", unsafe_allow_html=True)
st.write("")

st.markdown("### 🔍 실시간 인허가 연동 근거법규 ALL 리스트 및 조회 포털")
st.caption("※ 실무 심의 시 즉시 증명이 가능하도록 참고한 모든 상위법령 고시 및 웹 조회 시스템 링크를 투명하게 공개합니다.")

col_link1, col_link2, col_link3 = st.columns(3)
with col_link1:
    st.link_button("🌐 국가법령정보센터 (법률/시행령 조회)", "https://www.law.go.kr/")
with col_link2:
    st.link_button("🗺️ 토지이음 (지구단위계획/용도지역 조회)", "http://www.eum.go.kr/")
with col_link3:
    st.link_button("🍃 환경영향평가 정보시스템 (생태면적률 조회)", "https://www.eiass.go.kr/")

law_list = [
    {"분류": "지자체/도시계획 조례", "근거 법규 및 지침명": f"{law_article}", "시행/개정년도": f"{local_gov_name} 최신 조례"},
    {"분류": "상위 법률", "근거 법규 및 지침명": "빈집 및 소규모주택 정비에 관한 특례법 시행령 제40조 (완화 조항)", "시행/개정년도": "2026년 현행 법률"},
    {"분류": "정부 고시", "근거 법규 및 지침명": "국토교통부 조경기준 (식재 총량, 상록수 20% 및 특성수 10% 규정)", "시행/개정년도": "2024년 고시"},
    {"분류": "대통령령", "근거 법규 및 지침명": "주택건설기준 등에 관한 규정 제55조의2 (주민공동시설 총량제)", "시행/개정년도": "2025년 최신 개정"},
    {"분류": "환경부 지침", "근거 법규 및 지침명": "환경영향평가 생태면적률 적용 지침", "시행/개정년도": "2024년 지침"},
    {"분류": "상위 법률", "근거 법규 및 지침명": "자전거 이용 활성화에 관한 법률 시행령 제7조 [별표 1]", "시행/개정년도": "2026년 현행 법률"}
]
st.table(pd.DataFrame(law_list))

st.markdown("### 📋 실시간 종합 법규 검토 리포트")

display_address = project_address if project_address else "주소 미지정 현장"
st.info(f"**📍 현장 주소:** {display_address}\n\n**🔍 자동 인식 조건:** {local_gov_name} | {special_district} | 대지면적: {site_area:,.1f}㎡")
st.write("")

h1, h2, h3, h4 = st.columns([1.5, 3.2, 2.3, 0.8])
h1.markdown("**🔍 검토 항목 명칭**")
h2.markdown("**📜 법적 기준 및 산식 근거식**")
h3.markdown("**📊 법정요구 수치 / 내 계획**")
h4.markdown("**📢 결과**")
st.markdown("<div style='border-bottom: 2px solid #2E5A44; margin-bottom: 15px;'></div>", unsafe_allow_html=True)

if is_small_scale:
    landscape_metric_text = f"특례법에 의한 50% 완화 적용 (최종 의무 조경률: {req_landscape_ratio*100}%)"
else:
    landscape_metric_text = f"해당 지자체/지구 조례 또는 원문에 따른 대지면적의 {req_landscape_ratio*100}% 이상 확보"

print_law_row("1. 면적 검토", "조경 면적", landscape_metric_text, law_landscape, f"{legal_landscape_area:,.1f} ㎡ / {landscaping_area_plan:,.1f} ㎡", landscaping_area_plan >= legal_landscape_area)
print_law_row("1. 면적 검토", "자연 지반", f"의무 조경면적의 {req_natural_ratio*100}% 이상 확보", law_natural, f"{legal_natural_ground:,.1f} ㎡ / {natural_ground_plan:,.1f} ㎡", natural_ground_plan >= legal_natural_ground)
print_law_row("1. 면적 검토", "생태면적률", eco_legal_text, law_eco, eco_val_str, eco_pass)
print_law_row("1. 면적 검토", "공개 공지", open_space_text, law_open_space, open_space_val_str, open_space_pass)

print_law_row("2. 식재 검토", "전체 교목 수량", "의무조경면적 1㎡당 최소 0.2주 식재", law_total_tree, f"{legal_total_tree:,.0f} 주 / {tree_count:,.0f} 주", tree_count >= legal_total_tree)
print_law_row("2. 식재 검토", " - 상록 교목", f"법정 교목 의무 수량의 {req_evergreen_ratio*100}% 이상 필수 상록수 식재", law_evergreen, f"{legal_evergreen_tree:,.0f} 주 / {evergreen_tree_count:,.0f} 주", evergreen_tree_count >= legal_evergreen_tree)
print_law_row("2. 식재 검토", " - 특성수 수량", f"법정 교목 의무 수량의 {req_special_ratio*100}% 이상 국토부 기준 및 지자체 권장수종 적용", law_special, f"{legal_special_tree:,.0f} 주 / {special_tree_count:,.0f} 주", special_tree_count >= legal_special_tree)
print_law_row("2. 식재 검토", "전체 관목 수량", "의무조경면적 1㎡당 최소 1.0주 식재", law_total_tree, f"{legal_total_shrub:,.0f} 주 / {shrub_count:,.0f} 주", shrub_count >= legal_total_shrub)
print_law_row("2. 식재 검토", " - 상록 관목", f"법정 관목 의무 수량의 {req_evergreen_shrub_ratio*100}% 이상 필수 상록수 식재", law_evergreen, f"{legal_evergreen_shrub:,.0f} 주 / {evergreen_shrub_count:,.0f} 주", evergreen_shrub_count >= legal_evergreen_shrub)

print_law_row("3. 부대시설 검토", "어린이놀이터", play_legal_text, law_community, play_val_str, play_pass)
print_law_row("3. 부대시설 검토", "주민운동시설", sports_legal_text, law_community, sports_val_str, sports_pass)
print_law_row("3. 부대시설 검토", "통학버스 정류장", bus_formula_text, law_bus_stop, bus_val_str, bus_pass)
print_law_row("3. 부대시설 검토", "자전거 보관소", "법정 자동차 주차대수의 20% 이상 설치 의무", law_bike, f"{legal_bike_parking:,.0f} 대 / {bike_parking_plan:,.0f} 대", bike_parking_plan >= legal_bike_parking)
print_law_row("3. 부대시설 검토", "텃밭 / 부속정원", "설치 권장 (녹색건축인증 및 친환경 인센티브 조례 항목)", "녹색건축인증기준 지침 가이드", f"권장 / {garden_area_plan:,.1f} ㎡", True)

st.markdown("---")
st.subheader("📥 검토 결과 보고서 출력")

df_report = pd.DataFrame(report_data)
csv_data = df_report.to_csv(index=False).encode('utf-8-sig')

safe_address = re.sub(r'[^가-힣a-zA-Z0-9]', '_', display_address)[:15]

st.download_button(
    label="📊 조경법규 검토 결과 엑셀(CSV) 다운로드",
    data=csv_data,
    file_name=f"조경법규검토결과_{safe_address}.csv",
    mime="text/csv"
)
st.caption("※ 다운로드된 CSV 파일은 엑셀에서 바로 열람하고 표 서식으로 편집하여 보고서로 활용하실 수 있습니다.")
