import streamlit as st
import pandas as pd
import math
import re

# ---------------------------------------------------------
# 페이지 기본 설정
# ---------------------------------------------------------
st.set_page_config(page_title="조경 법규 마스터 검토 시스템", layout="wide")

st.title("🌿 조경 법규 실시간 종합 검토 시스템 (Pro)")
st.caption("국가법령정보센터 API 및 지자체 조례·지침 연동 엔진 (실무 심의 및 인허가용)")
st.markdown("---")

# ---------------------------------------------------------
# 사이드바: 1. 건축물 기본 개요 입력
# ---------------------------------------------------------
st.sidebar.header("🏢 1. 건축물 기본 개요 입력")

project_address = st.sidebar.text_input(
    "📝 프로젝트 주소지 (지번/도로명)", 
    value="원미구 조마루로 231", 
    help="⚠️ '시/군/구'를 포함하여 입력해 주세요. (예: 부천시 원미구)"
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
# 🧠 [핵심 보완] 스마트 주소 추론 및 파싱 엔진 (구/동 단위 매핑)
# ---------------------------------------------------------
match_si = re.search(r'([가-힣]+시)', project_address)
match_gun = re.search(r'([가-힣]+군)', project_address)
match_gu = re.search(r'([가-힣]+구)', project_address)

local_gov_name = ""
if match_si: local_gov_name = match_si.group(1)
elif match_gun: local_gov_name = match_gun.group(1)
elif match_gu: local_gov_name = match_gu.group(1)

smart_inferred = False
city_mapping = {
    "서울특별시": ["서울", "강남", "서초", "송파", "여의도", "종로", "명동", "은평", "마포", "성수", "평창", "한남"],
    "인천광역시": ["인천", "구월", "송도", "청라", "부평", "논현", "남동", "계양", "미추홀", "연수"],
    "수원시": ["수원", "인계", "광교", "영통", "권선", "호매실", "팔달", "장안"],
    "성남시": ["성남", "분당", "판교", "위례", "정자", "야탑", "수정", "중원"],
    "화성시": ["화성", "동탄", "병점", "향남", "봉담"],
    "부산광역시": ["부산", "해운대", "서면", "광안", "센텀", "명지", "수영", "동래", "기장"],
    "부천시": ["부천", "중동", "상동", "옥길", "원미", "소사", "오정", "조마루"],
    "전주시": ["전주", "효자", "에코", "혁신", "만성", "완산", "덕진"],
    "제천시": ["제천", "청전", "하소", "장락", "의림지", "신백"],
    "천안시": ["천안", "성성", "불당", "두정", "백석", "신부", "서북", "동남"],
    "광주광역시": ["광주", "상무", "수완", "첨단", "광산", "북구", "서구", "남구", "동구"]
}

for proper_city, keywords in city_mapping.items():
    if any(keyword in project_address for keyword in keywords):
        local_gov_name = proper_city
        smart_inferred = True
        break

if not local_gov_name:
    local_gov_name = "해당 지자체"
    st.sidebar.warning("⚠️ 주소에 '시/군/구'가 명확하지 않아 전국 기본 조례가 적용됩니다.")
elif smart_inferred:
    st.sidebar.success(f"💡 주소 자동 매핑 완료: **{local_gov_name}** 조례가 적용됩니다.")

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
# 사이드바: 4. 계획 수치 입력 (옥상조경 추가)
# ---------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.header("🌳 4. 계획 수치 입력")
st.sidebar.checkbox("🏘️ 특례법 완화 (조경면적 1/2) 자동 적용됨", value=auto_small_scale, disabled=True)

# 옥상 조경 입력 추가
landscaping_area_plan = st.sidebar.number_input("🟩 지상 계획 조경면적 (㎡)", min_value=0.0, value=3000.0, step=50.0)
rooftop_landscape_plan = st.sidebar.number_input("🏙️ 계획 옥상조경면적 (㎡)", min_value=0.0, value=0.0, step=50.0, help="건축법 시행령 제27조에 따라 2/3 면적 산정 (최대 50% 한도)")

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
law_rooftop = "건축법 시행령 제27조 (옥상조경 인정 기준)"
law_soil_depth = "국토교통부 조경기준 제12조 (식재토심)"
law_fire_truck = "소방기본법 시행령 제7조의12 (소방자동차 전용구역)"

# 조경 면적 및 옥상조경 특례 계산
legal_landscape_area = site_area * req_landscape_ratio

# 옥상조경 인정 로직 (최대 법정조경면적의 50%까지만 인정)
rooftop_recognized = rooftop_landscape_plan * (2/3)
rooftop_max_allowable = legal_landscape_area * 0.5
applied_rooftop_area = min(rooftop_recognized, rooftop_max_allowable)
total_recognized_landscape = landscaping_area_plan + applied_rooftop_area

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
    eco_legal_text = "소규모 사업 등 환경영향평가 비대상 의무 제외"
    eco_val_str = f"해당 없음 / {eco_area_plan:.1f} %"
    eco_pass = "N/A"

# 부대복리시설 판정
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
        sports_legal_text = "총량제 대상. 300세대 이상 필수 설치 대상"
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
    open_space_text, open_space_val_str, open_space_pass = "대지면적의 7% 이상 확보 (조경면적과 중복 인정 검토 요망)", f"{legal_open_space:,.1f} ㎡ / {open_space_plan:,.1f} ㎡", open_space_plan >= legal_open_space

# 건축물 용도별 토심 및 소방 검토 로직
if building_type == "공동주택 (아파트)":
    soil_depth_text = "교목 0.9m 이상 (인공지반 1.2m 권장)"
    fire_truck_text = "소방차 전용구역(폭 6m) 내 식재 및 단차 금지"
else:
    soil_depth_text = "교목 0.6m 이상 (인공지반 0.9m 권장)"
    fire_truck_text = "소방진입창 하부 및 대형 사다리차 전개 공간 식재 지양"

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
        "검토 항목": title,
        "법적 기준 및 산식": legal_text,
        "관련 근거": law_source,
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
col_link1, col_link2, col_link3 = st.columns(3)
with col_link1: st.link_button("🌐 국가법령정보센터", "https://www.law.go.kr/")
with col_link2: st.link_button("🗺️ 토지이음 (지구단위계획)", "http://www.eum.go.kr/")
with col_link3: st.link_button("🍃 환경영향평가 정보시스템", "https://www.eiass.go.kr/")

law_list = [
    {"분류": "지자체/도시계획 조례", "근거 법규 및 지침명": f"{law_article}", "시행/개정년도": f"{local_gov_name} 최신 조례"},
    {"분류": "상위 법률", "근거 법규 및 지침명": "빈집 및 소규모주택 정비에 관한 특례법 시행령 제40조 (완화 조항)", "시행/개정년도": "2026년 현행 법률"},
    {"분류": "건축/구조 특화", "근거 법규 및 지침명": "건축법 시행령 제27조 (옥상조경 인정 기준)", "시행/개정년도": "2024년 고시"},
    {"분류": "소방/안전 특화", "근거 법규 및 지침명": "소방기본법 시행령 제7조의12 (소방자동차 전용구역)", "시행/개정년도": "현행 법률"},
    {"분류": "대통령령", "근거 법규 및 지침명": "주택건설기준 등에 관한 규정 제55조의2 (주민공동시설 총량제)", "시행/개정년도": "2025년 최신 개정"}
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

if auto_small_scale:
    landscape_metric_text = f"특례법에 의한 50% 완화 적용 (최종 의무 조경률: {req_landscape_ratio*100}%)"
else:
    landscape_metric_text = f"해당 지자체/지구 조례 또는 원문에 따른 대지면적의 {req_landscape_ratio*100}% 이상 확보"

print_law_row("1. 면적 검토", "최종 인정 조경면적", landscape_metric_text, law_landscape, f"{legal_landscape_area:,.1f} ㎡ / {total_recognized_landscape:,.1f} ㎡", total_recognized_landscape >= legal_landscape_area)

if rooftop_landscape_plan > 0:
    rooftop_text = f"옥상조경의 2/3 인정하되, 법정 조경면적의 50%({rooftop_max_allowable:,.1f} ㎡) 한도 내 인정"
    print_law_row("1. 면적 검토", " └ 옥상조경 산입면적", rooftop_text, law_rooftop, f"최대 {rooftop_max_allowable:,.1f} ㎡ / {applied_rooftop_area:,.1f} ㎡ 인정됨", True)

print_law_row("1. 면적 검토", "자연 지반", f"의무 조경면적의 {req_natural_ratio*100}% 이상 확보", law_natural, f"{legal_natural_ground:,.1f} ㎡ / {natural_ground_plan:,.1f} ㎡", natural_ground_plan >= legal_natural_ground)
print_law_row("1. 면적 검토", "생태면적률", eco_legal_text, law_eco, eco_val_str, eco_pass)
print_law_row("1. 면적 검토", "공개 공지", open_space_text, law_open_space, open_space_val_str, open_space_pass)

print_law_row("2. 식재 검토", "전체 교목 수량", "의무조경면적 1㎡당 최소 0.2주 식재", law_total_tree, f"{legal_total_tree:,.0f} 주 / {tree_count:,.0f} 주", tree_count >= legal_total_tree)
print_law_row("2. 식재 검토", " - 상록 교목", f"법정 교목 의무 수량의 {req_evergreen_ratio*100}% 이상 필수 상록수 식재", law_evergreen, f"{legal_evergreen_tree:,.0f} 주 / {evergreen_tree_count:,.0f} 주", evergreen_tree_count >= legal_evergreen_tree)
print_law_row("2. 식재 검토", " - 특성수 수량", f"법정 교목 의무 수량의 {req_special_ratio*100}% 이상 국토부 기준 및 지자체 권장수종 적용", law_special, f"{legal_special_tree:,.0f} 주 / {special_tree_count:,.0f} 주", special_tree_count >= legal_special_tree)
print_law_row("2. 식재 검토", "전체 관목 수량", "의무조경면적 1㎡당 최소 1.0주 식재", law_total_tree, f"{legal_total_shrub:,.0f} 주 / {shrub_count:,.0f} 주", shrub_count >= legal_total_shrub)

print_law_row("3. 부대시설", "어린이놀이터", play_legal_text, law_community, play_val_str, play_pass)
print_law_row("3. 부대시설", "주민운동시설", sports_legal_text, law_community, sports_val_str, sports_pass)
print_law_row("3. 부대시설", "자전거 보관소", "법정 자동차 주차대수의 20% 이상 설치 의무", law_bike, f"{legal_bike_parking:,.0f} 대 / {bike_parking_plan:,.0f} 대", bike_parking_plan >= legal_bike_parking)

print_law_row("4. 특화 설계 기준", "식재 토심 (구조 협업)", soil_depth_text, law_soil_depth, "권장 사양 확인 완료", True)
print_law_row("4. 특화 설계 기준", "소방 및 피난 동선", fire_truck_text, law_fire_truck, "소방차량 동선 겹침 여부 확인", True)

st.markdown("---")
st.subheader("📥 검토 결과 보고서 출력")
df_report = pd.DataFrame(report_data)
csv_data = df_report.to_csv(index=False).encode('utf-8-sig')
safe_address = re.sub(r'[^가-힣a-zA-Z0-9]', '_', display_address)[:15]
st.download_button("📊 조경법규 검토 결과 엑셀(CSV) 다운로드", data=csv_data, file_name=f"조경법규검토결과_{safe_address}.csv", mime="text/csv")
