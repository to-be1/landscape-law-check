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

# [보완] 실무자에게 올바른 주소 입력을 유도하는 스마트 가이드 적용
project_address = st.sidebar.text_input(
    "📝 프로젝트 주소지 (지번/도로명)", 
    value="충북 제천시 청전동 일원", 
    help="⚠️ 반드시 '시/군/구'를 포함하여 입력해 주세요. (예: 제천시 청전동)"
)

zone_type = st.sidebar.selectbox("🗺️ 용도지역 분류", ["일반주거지역", "준주거지역", "중심상업지역", "일반상업지역", "근린상업지역", "준공업지역", "기타지역"])
special_district = st.sidebar.selectbox("⛰️ 용도지구 (특수지역) 분류", ["해당 없음 (일반 지역)", "자연경관지구", "역사문화환경보존지구", "고도지구", "기타 특수지구"])
building_type = st.sidebar.selectbox("🏢 건축물 용도", ["공동주택 (아파트)", "업무시설 (오피스텔/일반업무)", "판매시설 (백화점/마트)", "근린생활시설", "기타 건축물"])

site_area = st.sidebar.number_input("📐 계획 대지면적 (㎡)", min_value=0.0, value=13104.0, step=100.0)
total_floor_area = st.sidebar.number_input("🏢 연면적 합계 (㎡)", min_value=0.0, value=35000.0, step=500.0)
household_count = st.sidebar.number_input("👨‍👩‍👧‍👦 신축 계획 세대수", min_value=0, value=314, step=10)
legal_parking_count = st.sidebar.number_input("🚙 법정 자동차 주차대수", min_value=0, value=100, step=10)
plan_parking_count = st.sidebar.number_input("🚗 계획 자동차 주차대수", min_value=0, value=100, step=10)

# ---------------------------------------------------------
# 🧠 스마트 주소 추론 및 파싱 엔진
# ---------------------------------------------------------
match = re.search(r'([가-힣]+(시|군|구))', project_address)
local_gov_name = match.group(1) if match else ""

smart_inferred = False
if not local_gov_name:
    # 자주 쓰는 동네 이름을 통한 보조 추론 엔진
    dong_mapping = {
        "서울": ["불광", "강남", "서초", "송파", "여의도", "종로", "명동", "은평", "마포", "성수", "평창", "한남"],
        "인천": ["구월", "송도", "청라", "부평", "논현"],
        "수원": ["인계", "광교", "영통", "권선", "호매실"],
        "성남": ["분당", "판교", "위례", "정자", "야탑"],
        "화성": ["동탄", "병점", "향남", "봉담"],
        "부산": ["해운대", "서면", "광안", "센텀", "명지"],
        "부천": ["중동", "상동", "옥길"],
        "전주": ["효자", "에코", "혁신", "만성"],
        "제천": ["청전", "하소", "장락", "의림지", "신백"],
        "천안": ["성성", "불당", "두정", "백석", "신부"]
    }
    
    for city, dongs in dong_mapping.items():
        if any(dong in project_address for dong in dongs):
            local_gov_name = f"{city}특별시" if city == "서울" else f"{city}광역시" if city in ["인천", "부산", "광주", "대구", "대전", "울산"] else f"{city}시"
            smart_inferred = True
            break

if not local_gov_name:
    local_gov_name = "해당 지자체"
    st.sidebar.warning("⚠️ 주소에 '시/군/구'가 명확하지 않아 전국 기본 조례가 적용됩니다. 정확한 산출을 위해 '제천시 청전동' 처럼 시/군/구를 포함해 입력해 주세요.")
elif smart_inferred:
    st.sidebar.success(f"💡 동 이름 추론 완료: **{local_gov_name}** 조례가 자동 매핑되었습니다.")

# ---------------------------------------------------------
# 사이드바: 2. 🚀 동적 법령 원문 파싱 엔진
# ---------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.header("📡 2. 동적 법령 원문 파싱 엔진")
use_dynamic_parsing = st.sidebar.checkbox("⚙️ 동적 법령 원문 파싱 모드 켜기", value=False)

raw_law_text = ""
parsed_ratio = None

if use_dynamic_parsing:
    st.sidebar.info("💡 국가법령정보센터에서 해당 지자체 건축조례(대지의 조경) 원문을 복사하여 아래에 붙여넣으세요.")
    default_text = "연면적의 합계가 2천제곱미터 이상인 건축물: 대지면적의 15퍼센트 이상"
    raw_law_text = st.sidebar.text_area("📄 법규/조례 원문 텍스트", value=default_text, height=150)
    
    if total_floor_area >= 2000: match_dyn = re.search(r'2천제곱미터 이상[^\n]*?대지면적의\s*(\d+(?:\.\d+)?)\s*(?:퍼센트|%)', raw_law_text)
    elif total_floor_area >= 1000: match_dyn = re.search(r'1천제곱미터 이상[^\n]*?대지면적의\s*(\d+(?:\.\d+)?)\s*(?:퍼센트|%)', raw_law_text)
    else: match_dyn = None
        
    if not match_dyn: match_dyn = re.search(r'대지면적의\s*(\d+(?:\.\d+)?)\s*(?:퍼센트|%)', raw_law_text)
        
    if match_dyn:
        parsed_ratio = float(match_dyn.group(1)) / 100.0
        st.sidebar.success(f"🎯 원문 분석 완료: **{match_dyn.group(1)}%** 적용됨")
    else:
        st.sidebar.error("❌ 텍스트에서 '대지면적의 OO퍼센트' 패턴을 찾지 못했습니다.")

# ---------------------------------------------------------
# 사이드바: 3. 특례법 자동 판별기
# ---------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.header("📋 3. 특례법 자동 판별기")
project_category = st.sidebar.radio("사업의 성격", ["일반 신축 및 개발사업", "노후 건축물 정비 (재개발/재건축)"])

auto_small_scale = False; auto_eco_target = True

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
# 사이드바: 4. 계획 수치 입력
# ---------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.header("🌳 4. 계획 수치 입력")
st.sidebar.checkbox("🏘️ 특례법 완화 (조경면적 1/2) 자동 적용됨", value=auto_small_scale, disabled=True)
landscaping_area_plan = st.sidebar.number_input("🟩 계획 조경면적 (㎡)", min_value=0.0, value=3000.0, step=50.0)
natural_ground_plan = st.sidebar.number_input("🟫 계획 자연지반면적 (㎡)", min_value=0.0, value=400.0, step=10.0)
st.sidebar.checkbox("🌱 생태면적률 의무 대상 자동 적용됨", value=auto_eco_target, disabled=True)
eco_area_plan = st.sidebar.slider("🍃 계획 생태면적률 (%)", min_value=0.0, max_value=100.0, value=23.5, step=0.5)
open_space_plan = st.sidebar.number_input("⛲ 계획 공개공지면적 (㎡)", min_value=0.0, value=0.0, step=10.0)

tree_count = st.sidebar.number_input("🌳 계획 교목 총 수량 (주)", min_value=0, value=600, step=10)
evergreen_tree_count = st.sidebar.number_input("🌲 계획 상록교목 수량 (주)", min_value=0, value=120, step=5)
special_tree_count = st.sidebar.number_input("✨ 계획 특성수 수량 (주)", min_value=0, value=60, step=5)
shrub_count = st.sidebar.number_input("🌿 계획 관목 총 수량 (주)", min_value=0, value=3000, step=50)
evergreen_shrub_count = st.sidebar.number_input("🍃 계획 상록관목 수량 (주)", min_value=0, value=600, step=10)

play_area_plan = st.sidebar.number_input("🛝 계획 어린이놀이터 면적 (㎡)", min_value=0.0, value=150.0, step=10.0)
sports_area_plan = st.sidebar.number_input("🏋️ 계획 주민운동시설 면적 (㎡)", min_value=0.0, value=150.0, step=10.0)
bus_stop_plan = st.sidebar.number_input("🚌 계획 통학버스 정류장 (개소)", min_value=0, value=0, step=1)
bike_parking_plan = st.sidebar.number_input("🚲 계획 자전거보관소 (대)", min_value=0, value=25, step=5)
garden_area_plan = st.sidebar.number_input("🧑‍🌾 계획 텃밭/부속정원 면적 (㎡)", min_value=0.0, value=0.0, step=5.0)

report_data = []

# ---------------------------------------------------------
# 🧠 하이브리드 계산 로직 (동적 파싱 vs DB 매핑)
# ---------------------------------------------------------
if use_dynamic_parsing and parsed_ratio is not None:
    req_landscape_ratio = parsed_ratio
    law_article = f"[동적 파싱 적용] {local_gov_name} 조례 원문 기준"
else:
    law_article = f"{local_gov_name} 건축조례"
    
    if "서울" in local_gov_name:
        law_article = "서울특별시 건축조례 제24조"
        req_landscape_ratio = 0.15 if total_floor_area >= 2000 else 0.10
    elif "인천" in local_gov_name:
        law_article = "인천광역시 건축조례 제27조"
        if total_floor_area >= 2000: req_landscape_ratio = 0.15
        elif total_floor_area >= 1000: req_landscape_ratio = 0.10
        else: req_landscape_ratio = 0.05
    elif "부천" in local_gov_name:
        law_article = "부천시 건축조례 제24조"
        req_landscape_ratio = 0.20
    elif "전주" in local_gov_name:
        law_article = "전주시 건축조례 제23조"
        req_landscape_ratio = 0.18
    elif "수원" in local_gov_name:
        law_article = "수원시 건축조례 제31조"
        if "중심상업" in zone_type: req_landscape_ratio = 0.05
        elif total_floor_area >= 5000: req_landscape_ratio = 0.18
        elif total_floor_area >= 2000: req_landscape_ratio = 0.15
        elif total_floor_area >= 1000: req_landscape_ratio = 0.10
        else: req_landscape_ratio = 0.05
    elif "광주" in local_gov_name:
        if total_floor_area >= 2000: req_landscape_ratio = 0.15
        elif total_floor_area >= 1000: req_landscape_ratio = 0.13
        else: req_landscape_ratio = 0.07
    else:
        # DB에 없는 전국 일반 지자체 (스마트 디폴트 룰)
        if total_floor_area >= 2000: req_landscape_ratio = 0.15
        elif total_floor_area >= 1000: req_landscape_ratio = 0.10
        else: req_landscape_ratio = 0.05

    # 용도지구 특례 최우선 적용
    if "자연경관지구" in special_district:
        req_landscape_ratio = 0.30
        law_article = f"{local_gov_name} 도시계획조례 (자연경관지구 30% 강화)"

# 소규모 특례법 1/2 완화 적용
if auto_small_scale:
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

# 조경 면적이 바뀌면 수목 수량도 완벽하게 자동 연동되어 계산됩니다.
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

if auto_eco_target:
    eco_legal_text = "대지면적의 30.0% 이상 도입 권장"
    eco_val_str = f"30.0 % / {eco_area_plan:.1f} %"
    eco_pass = eco_area_plan >= 30.0
else:
    eco_legal_text = "소규모 사업 등 환경영향평가 비대상 의무 제외
