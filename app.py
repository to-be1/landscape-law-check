import streamlit as st
import pandas as pd
import math
import re
import requests

# ---------------------------------------------------------
# 1. Pro 시스템 설정 및 데이터베이스
# ---------------------------------------------------------
st.set_page_config(page_title="Professional Landscape Law Reviewer", layout="wide")

# 카카오 API 지역명 변환 사전
KAKAO_CITY_MAP = {
    "서울": "서울특별시", "경기": "경기도", "인천": "인천광역시",
    "충북": "충청북도", "충남": "충청남도", "전북": "전북특별자치도",
    "광주": "광주광역시", "부산": "부산광역시", "대구": "대구광역시", "대전": "대전광역시"
}

REGION_DB = {
    "서울특별시": ["강남구", "은평구", "마포구", "종로구", "송파구", "서초구", "기타"],
    "인천광역시": ["부평구", "남동구", "계양구", "연수구", "미추홀구", "서구", "기타"],
    "경기도": ["부천시", "수원시", "성남시", "화성시", "안양시", "고양시", "기타"],
    "전북특별자치도": ["전주시", "기타"],
    "충청북도": ["제천시", "충주시", "청주시", "기타"],
    "충청남도": ["천안시", "아산시", "기타"],
    "광주광역시": ["광산구", "북구", "서구", "남구", "동구", "기타"]
}

st.title("🌿 조경 법규 전문 검토 엔진 (Kakao API & 총량제 연동)")
st.caption("건축법, 주택건설기준 등에 관한 규정, 지자체 조례를 종합 분석하는 실무용 시스템")
st.markdown("---")

# ---------------------------------------------------------
# 2. 사이드바: 1. 현장 주소 검색 (Kakao API)
# ---------------------------------------------------------
st.sidebar.header("🏢 1. 현장 주소 검색")

kakao_api_key = st.sidebar.text_input("🔑 카카오 REST API 키", type="password", help="발급받은 REST API 키 입력")
search_query = st.sidebar.text_input("📝 주소 검색 (지번/도로명)", value="부천시 조마루로 231")

if 'set_city' not in st.session_state: st.session_state['set_city'] = "경기도"
if 'set_dist' not in st.session_state: st.session_state['set_dist'] = "부천시"

def fetch_kakao_address(query, api_key):
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {api_key}"}
    try:
        res = requests.get(url, headers=headers, params={"query": query})
        if res.status_code == 200 and res.json().get("documents"):
            addr_info = res.json()["documents"][0]
            return addr_info.get("address_name", ""), addr_info["address_name"].split()[0], addr_info["address_name"].split()[1]
    except Exception:
        return None, None, None
    return None, None, None

if st.sidebar.button("🔍 주소 자동 매핑"):
    if not kakao_api_key:
        st.sidebar.error("⚠️ 카카오 API 키를 입력해주세요.")
    else:
        full_addr, k_city, k_dist = fetch_kakao_address(search_query, kakao_api_key)
        if k_city:
            mapped_city = KAKAO_CITY_MAP.get(k_city, "서울특별시")
            mapped_dist = "기타"
            for d in REGION_DB.get(mapped_city, []):
                if d in k_dist:  
                    mapped_dist = d
                    break
            st.session_state['set_city'] = mapped_city
            st.session_state['set_dist'] = mapped_dist
            st.sidebar.success(f"✅ 자동 매핑 성공: {full_addr}")
        else:
            st.sidebar.warning("❌ 검색 결과가 없습니다.")

st.sidebar.caption("👇 확정된 지자체 (수동 수정 가능)")
city = st.sidebar.selectbox("🏠 시/도", list(REGION_DB.keys()), index=list(REGION_DB.keys()).index(st.session_state['set_city']))
district = st.sidebar.selectbox("📍 시/군/구", REGION_DB[city], index=REGION_DB[city].index(st.session_state['set_dist']) if st.session_state['set_dist'] in REGION_DB[city] else 0)

# ---------------------------------------------------------
# 3. 사이드바: 2. 건축물 개요 및 특례
# ---------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.header("🏢 2. 건축물 개요")
zone = st.sidebar.selectbox("🗺️ 용도지역", ["일반주거지역", "준주거지역", "중심상업지역", "일반상업지역", "기타"])
b_type = st.sidebar.selectbox("🏢 건축물 용도", ["공동주택 (아파트)", "업무시설", "판매시설", "기타 건축물"])

area = st.sidebar.number_input("📐 대지면적 (㎡)", value=13104.0)
fl_area = st.sidebar.number_input("🏢 연면적 (㎡)", value=35000.0)
parking = st.sidebar.number_input("🚙 법정주차대수", value=100)
household_count = st.sidebar.number_input("👨‍👩‍👧‍👦 세대수 (아파트용)", value=321)

st.sidebar.markdown("---")
st.sidebar.header("📋 3. 특례 및 조례 덮어쓰기")
is_district_unit = st.sidebar.checkbox(
    "🚀 지구단위계획 우선 적용 모드", 
    help="[언제 체크하나요?]\n토지이음(eum.go.kr) 조회 결과 해당 대지가 '지구단위계획구역'으로 지정된 경우 체크합니다. 건축조례보다 지구단위계획 지침의 조경률이 최우선 적용됩니다."
)
target_landscape_ratio = st.sidebar.number_input("🎯 지구단위계획 조경률(%)", value=20.0, step=1.0) / 100.0 if is_district_unit else 0.15

use_dynamic_parsing = st.sidebar.checkbox(
    "⚙️ 조례 원문 파싱 모드",
    help="[언제 체크하나요?]\n시스템 DB에 없는 타 지자체 프로젝트이거나, 법령정보센터에서 방금 개정된 최신 조례 원문을 직접 복사/붙여넣기하여 계산하고 싶을 때 체크합니다."
)
raw_law_text = st.sidebar.text_area("📄 조례 원문 붙여넣기", height=80) if use_dynamic_parsing else ""
is_small_scale = st.sidebar.checkbox(
    "🏘️ 소규모재건축 특례 완화(1/2) 적용",
    help="[언제 체크하나요?]\n「빈집 및 소규모주택 정비에 관한 특례법」을 적용받는 가로주택정비사업이나 소규모재건축(대지면적 1만㎡ 미만, 200세대 미만 등)일 때 체크합니다. 법정 조경면적이 50% 완화됩니다."
)

# ---------------------------------------------------------
# 4. 사이드바: 4. 계획 수치 입력
# ---------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.header("🌳 4. 조경 계획 수치")
landscaping_area_plan = st.sidebar.number_input("🟩 지상 계획 조경면적 (㎡)", value=3000.0, step=50.0)
rooftop_plan = st.sidebar.number_input("🏙️ 계획 옥상조경면적 (㎡)", value=0.0, step=50.0)
natural_ground_plan = st.sidebar.number_input("🟫 계획 자연지반면적 (㎡)", value=400.0, step=10.0)
eco_area_plan = st.sidebar.slider("🍃 계획 생태면적률 (%)", min_value=0.0, max_value=100.0, value=23.5)

tree_count = st.sidebar.number_input("🌳 계획 교목 수량 (주)", value=600)
evergreen_tree_count = st.sidebar.number_input("🌲 상록교목 수량 (주)", value=120)
special_tree_count = st.sidebar.number_input("✨ 특성수 수량 (주)", value=60)
shrub_count = st.sidebar.number_input("🌿 계획 관목 수량 (주)", value=3000)

st.sidebar.markdown("---")
st.sidebar.header("🏢 5. 주민공동시설 계획 (총량제)")
play_area_plan = st.sidebar.number_input("🛝 어린이놀이터 (㎡)", value=150.0, step=10.0)
sports_area_plan = st.sidebar.number_input("🏋️ 주민운동시설 (㎡)", value=150.0, step=10.0)
senior_area_plan = st.sidebar.number_input("👴 경로당 (㎡)", value=100.0, step=10.0)
daycare_area_plan = st.sidebar.number_input("👶 어린이집 (㎡)", value=200.0, step=10.0)
library_area_plan = st.sidebar.number_input("📚 작은도서관 (㎡)", value=0.0, step=10.0)
bike_parking_plan = st.sidebar.number_input("🚲 자전거보관소 (대)", value=25)

# ---------------------------------------------------------
# 5. 하이브리드 계산 로직 (법규 판별 및 면적 산출)
# ---------------------------------------------------------
def get_landscape_ratio(c, d, f_area, z):
    if use_dynamic_parsing and raw_law_text:
        match = re.search(r'대지면적의\s*(\d+(?:\.\d+)?)\s*(?:퍼센트|%)', raw_law_text)
        if match: return float(match.group(1)) / 100.0, f"[동적 파싱 적용] {d} 조례 원문 기준"
    
    if is_district_unit: return target_landscape_ratio, "지구단위계획 수립지침 최우선 적용"
    
    if c == "서울특별시": return 0.15 if f_area >= 2000 else 0.10, "서울특별시 건축조례 제24조"
    if c == "인천광역시": return 0.15 if f_area >= 2000 else 0.10 if f_area >= 1000 else 0.05, "인천광역시 건축조례 제27조"
    if d == "부천시": return 0.20, "부천시 건축조례 제24조"
    if d == "수원시": return 0.05 if "중심상업" in z else 0.18 if f_area >= 5000 else 0.15, "수원시 건축조례 제31조"
    if d == "전주시": return 0.18, "전주시 건축조례 제23조"
    
    return 0.15, "국토교통부 건축법 일반 조경기준"

ratio, law_src = get_landscape_ratio(city, district, fl_area, zone)
if is_small_scale: 
    ratio *= 0.5
    law_landscape = f"소규모주택정비법 시행령 제40조 (1/2 완화) 및 {law_src}"
else:
    law_landscape = f"{law_src} 및 건축법 제42조"

legal_landscape_area = area * ratio
rooftop_recognized = rooftop_plan * (2/3)
rooftop_max_allowable = legal_landscape_area * 0.5
applied_rooftop_area = min(rooftop_recognized, rooftop_max_allowable)
total_recognized_landscape = landscaping_area_plan + applied_rooftop_area

legal_natural_ground = legal_landscape_area * 0.10
legal_total_tree = math.ceil(legal_landscape_area * 0.2)
legal_evergreen_tree = math.ceil(legal_total_tree * 0.2)
legal_special_tree = math.ceil(legal_total_tree * 0.1)
legal_total_shrub = math.ceil(legal_landscape_area * 1.0)
legal_bike_parking = math.ceil(parking * 0.20)

# 법적 근거 명확화 텍스트
law_natural = "국토교통부 조경기준 제12조 (자연지반 식재 등)"
law_rooftop = "건축법 시행령 제27조 (옥상조경 인정 기준)"
law_eco = "환경부 고시 생태면적률 적용 지침"
law_total_tree = "국토교통부 조경기준 제10조 (식재수량 및 기준)"
law_evergreen = "국토교통부 조경기준 제13조 (상록수 식재 비율)"
law_community = "주택건설기준 등에 관한 규정 제55조의2 (주민공동시설)"
law_guideline = "국토교통부 주민공동시설 설치총량제 운용 가이드라인"
law_bike = "자전거 이용 활성화에 관한 법률 시행령 제7조 [별표 1]"
law_soil_depth = "국토교통부 조경기준 제12조 (식재토심)"

# 생태면적률 판별 로직 추가
if is_small_scale:
    eco_legal_text = "소규모 사업 등 환경영향평가 비대상 (의무 제외)"
    eco_val_str = f"해당 없음 / {eco_area_plan:.1f} %"
    eco_pass = "N/A"
else:
    eco_legal_text = "대지면적의 30.0% 이상 도입 권장"
    eco_val_str = f"30.0 % / {eco_area_plan:.1f} %"
    eco_pass = eco_area_plan >= 30.0

# 주민공동시설 총량제 판별 로직
if b_type != "공동주택 (아파트)":
    comm_total_text, comm_total_val, comm_total_pass = "해당 없음", "N/A", "N/A"
    senior_text, senior_val, senior_pass = "해당 없음", "N/A", "N/A"
    play_text, play_val, play_pass = "해당 없음", "N/A", "N/A"
    daycare_text, daycare_val, daycare_pass = "해당 없음", "N/A", "N/A"
    sports_text, sports_val, sports_pass = "해당 없음", "N/A", "N/A"
    library_text, library_val, library_pass = "해당 없음", "N/A", "N/A"
else:
    # 1. 총량제
    if household_count < 100:
        comm_total_req = 0
        comm_total_text = "100세대 미만: 총량제 비대상"
    elif household_count < 1000:
        comm_total_req = household_count * 2.5
        comm_total_text = f"총량제 대상 (세대수×2.5㎡): {comm_total_req:,.1f}㎡ 이상 확보"
    else:
        comm_total_req = 500 + (household_count * 2.0)
        comm_total_text = f"총량제 대상 (500㎡+세대수×2㎡): {comm_total_req:,.1f}㎡ 이상 확보"
        
    comm_total_plan = play_area_plan + sports_area_plan + senior_area_plan + daycare_area_plan + library_area_plan
    comm_total_val = f"{comm_total_req:,.1f} ㎡ / {comm_total_plan:,.1f} ㎡"
    comm_total_pass = comm_total_plan >= comm_total_req if comm_total_req > 0 else "N/A"

    # 2. 경로당
    if household_count < 150: senior_text, senior_val, senior_pass = "설치 의무 없음", "N/A", "N/A"
    else:
        senior_req = 50 + (household_count * 0.1)
        senior_text = f"의무대상 권장면적 (50㎡+세대수×0.1㎡): {senior_req:,.1f}㎡ 이상"
        senior_val = f"{senior_req:,.1f} ㎡ / {senior_area_plan:,.1f} ㎡"
        senior_pass = senior_area_plan >= senior_req

    # 3. 어린이놀이터
    if household_count < 150: play_text, play_val, play_pass = "설치 의무 없음", "N/A", "N/A"
    elif household_count < 300:
        play_text = "의무대상 (적정면적 설치 권장)"
        play_val = f"적정확보 / {play_area_plan:,.1f} ㎡"
        play_pass = play_area_plan > 0
    elif household_count < 1000:
        play_req = 200 + (household_count * 1.0)
        play_text = f"의무대상 권장면적 (200㎡+세대수×1㎡): {play_req:,.1f}㎡ 이상"
        play_val = f"{play_req:,.1f} ㎡ / {play_area_plan:,.1f} ㎡"
        play_pass = play_area_plan >= play_req
    else:
        play_req = 500 + (household_count * 0.7)
        play_text = f"의무대상 권장면적 (500㎡+세대수×0.7㎡): {play_req:,.1f}㎡ 이상"
        play_val = f"{play_req:,.1f} ㎡ / {play_area_plan:,.1f} ㎡"
        play_pass = play_area_plan >= play_req

    # 4. 어린이집
    if household_count < 300: daycare_text, daycare_val, daycare_pass = "설치 의무 없음", "N/A", "N/A"
    else:
        daycare_text = "의무대상 (보육정원별 인가면적 적용 권장)"
        daycare_val = f"기준확인 요망 / {daycare_area_plan:,.1f} ㎡"
        daycare_pass = daycare_area_plan > 0

    # 5. 주민운동시설
    if household_count < 500: sports_text, sports_val, sports_pass = "설치 의무 없음", "N/A", "N/A"
    else:
        sports_text = "의무대상 (종목별 경기장 규격 적용 권장)"
        sports_val = f"총량 내 확보 / {sports_area_plan:,.1f} ㎡"
        sports_pass = sports_area_plan > 0

    # 6. 작은도서관
    if household_count < 500: library_text, library_val, library_pass = "설치 의무 없음", "N/A", "N/A"
    else:
        library_text = "의무대상 (문체부 100㎡ 내외 권장)"
        library_val = f"100.0 ㎡ / {library_area_plan:,.1f} ㎡"
        library_pass = library_area_plan >= 100

# ---------------------------------------------------------
# 6. 출력 모듈 구성 (포털 링크 및 법규 리스트)
# ---------------------------------------------------------
st.markdown("### 🔍 실시간 인허가 연동 근거법규 ALL 리스트 및 조회 포털")
col_link1, col_link2, col_link3 = st.columns(3)
with col_link1: st.link_button("🌐 국가법령정보센터", "https://www.law.go.kr/")
with col_link2: st.link_button("🗺️ 토지이음 (지구단위계획)", "http://www.eum.go.kr/")
with col_link3: st.link_button("🍃 환경영향평가 정보시스템", "https://www.eiass.go.kr/")

law_list = [
    {"분류": "지자체/도시계획 조례", "근거 법규 및 지침명": f"{law_src}", "비고": f"{city} 최신 조례 적용"},
    {"분류": "상위 법률", "근거 법규 및 지침명": "건축법 시행령 제27조 (옥상조경 인정 기준)", "비고": "대지면적 한도 반영"},
    {"분류": "대통령령", "근거 법규 및 지침명": "주택건설기준 등에 관한 규정 제55조의2", "비고": "주민공동시설 총량제"},
    {"분류": "환경부 고시", "근거 법규 및 지침명": "생태면적률 적용 지침", "비고": "환경영향평가 대상"},
    {"분류": "국토부 지침", "근거 법규 및 지침명": "주민공동시설 설치총량제 운용 가이드라인", "비고": "세대수별 최소면적"},
    {"분류": "정부 고시", "근거 법규 및 지침명": "국토교통부 조경기준 (식재수량, 상록수, 토심)", "비고": "조경 설계 핵심"}
]
st.table(pd.DataFrame(law_list))

report_data = []
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
    report_data.append({"검토 항목": title, "법적 기준": legal_text, "요구/계획": legal_plan_compare_str, "결과": csv_status})

st.markdown("### 📋 실시간 종합 법규 검토 리포트")
st.info(f"**📍 현장:** {city} {district} | **적용 기준:** {law_src} ({ratio*100:.1f}%)")
st.write("")

h1, h2, h3, h4 = st.columns([1.5, 3.2, 2.3, 0.8])
h1.markdown("**🔍 검토 항목 명칭**")
h2.markdown("**📜 법적 기준 및 산식 근거식**")
h3.markdown("**📊 법정요구 수치 / 내 계획**")
h4.markdown("**📢 결과**")
st.markdown("<div style='border-bottom: 2px solid #2E5A44; margin-bottom: 15px;'></div>", unsafe_allow_html=True)

# 💡 [비율(%) 자동 계산 로직]
plan_landscape_ratio = (total_recognized_landscape / area) * 100 if area > 0 else 0
plan_natural_ratio = (natural_ground_plan / legal_landscape_area) * 100 if legal_landscape_area > 0 else 0

# 1. 면적
print_law_row("1. 면적", "최종 인정 조경면적", f"대지면적의 {ratio*100}% 이상 확보", law_landscape, f"{legal_landscape_area:,.1f} ㎡ / {total_recognized_landscape:,.1f} ㎡ (대지면적의 {plan_landscape_ratio:.1f}%)", total_recognized_landscape >= legal_landscape_area)
if rooftop_plan > 0:
    print_law_row("1. 면적", " └ 옥상조경 산입", f"2/3 인정하되, 법정 조경면적 50%({rooftop_max_allowable:,.1f}㎡) 한도", law_rooftop, f"최대 {rooftop_max_allowable:,.1f} ㎡ / {applied_rooftop_area:,.1f} ㎡ 인정", True)
print_law_row("1. 면적", "자연 지반", "의무 조경면적의 10% 이상", law_natural, f"{legal_natural_ground:,.1f} ㎡ / {natural_ground_plan:,.1f} ㎡ (의무조경의 {plan_natural_ratio:.1f}%)", natural_ground_plan >= legal_natural_ground)

# 💡 생태면적률 복구 
print_law_row("1. 면적", "생태면적률", eco_legal_text, law_eco, eco_val_str, eco_pass)

# 2. 식재
print_law_row("2. 식재", "전체 교목 수량", "조경 1㎡당 0.2주", law_total_tree, f"{legal_total_tree:,.0f} 주 / {tree_count:,.0f} 주", tree_count >= legal_total_tree)
print_law_row("2. 식재", " └ 상록 교목", "교목 의무 수량의 20% 이상", law_evergreen, f"{legal_evergreen_tree:,.0f} 주 / {evergreen_tree_count:,.0f} 주", evergreen_tree_count >= legal_evergreen_tree)
print_law_row("2. 식재", "전체 관목 수량", "조경 1㎡당 1.0주", law_total_tree, f"{legal_total_shrub:,.0f} 주 / {shrub_count:,.0f} 주", shrub_count >= legal_total_shrub)

# 3. 부대시설 (총량제 가이드라인 적용)
if b_type == "공동주택 (아파트)":
    print_law_row("3. 주민시설", "총량 면적", comm_total_text, law_community, comm_total_val, comm_total_pass)
    print_law_row("3. 주민시설", " ├ 경로당", senior_text, law_guideline, senior_val, senior_pass)
    print_law_row("3. 주민시설", " ├ 어린이놀이터", play_text, law_guideline, play_val, play_pass)
    print_law_row("3. 주민시설", " ├ 어린이집", daycare_text, law_guideline, daycare_val, daycare_pass)
    print_law_row("3. 주민시설", " ├ 주민운동시설", sports_text, law_guideline, sports_val, sports_pass)
    print_law_row("3. 주민시설", " └ 작은도서관", library_text, law_guideline, library_val, library_pass)

print_law_row("4. 기타", "자전거 보관소", "법정 주차대수의 20% 이상", law_bike, f"{legal_bike_parking:,.0f} 대 / {bike_parking_plan:,.0f} 대", bike_parking_plan >= legal_bike_parking)
print_law_row("4. 기타", "식재 토심", "아파트 교목 0.9m (인공 1.2m 권장)", law_soil_depth, "권장 사양 확인", True)

st.markdown("---")
df_report = pd.DataFrame(report_data)
st.download_button("📊 검토 결과 엑셀(CSV) 다운로드", df_report.to_csv(index=False).encode('utf-8-sig'), file_name="조경법규검토.csv", mime="text/csv")
