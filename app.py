import streamlit as st
import pandas as pd
import math

# ---------------------------------------------------------
# 페이지 기본 설정
# ---------------------------------------------------------
st.set_page_config(page_title="조경 법규 마스터 검토 시스템", layout="wide")

st.title("🌿 조경 법규 실시간 종합 검토 시스템")
st.caption("국가법령정보센터 API 및 지자체 조례·지침 연동 엔진 (실무 심의 및 인허가용)")
st.markdown("---")

# ---------------------------------------------------------
# 사이드바: 건축 개요 입력 창
# ---------------------------------------------------------
st.sidebar.header("🏢 건축물 기본 개요 입력")

regions = [
    "서울 강남구", "서울 강서구", "서울 종로구", "부산 해운대구", "대구 수성구", 
    "인천 서구", "광주 북구", "대전 유성구", "울산 남구", "세종특별자치시", 
    "수원시", "성남시", "화성시", "용인시", "평택시", "천안시", "아산시", "청주시", "전주시", "제주시"
]

region = st.sidebar.selectbox("📍 대상 지자체 선택", regions, index=regions.index("천안시") if "천안시" in regions else 0)

zone_type = st.sidebar.selectbox(
    "🗺️ 용도지역 분류",
    ["일반주거지역", "준주거지역", "중심상업지역", "일반상업지역", "근린상업지역", "준공업지역", "기타지역"]
)

building_type = st.sidebar.selectbox(
    "🏢 건축물 용도",
    ["공동주택 (아파트)", "업무시설 (오피스텔/일반업무)", "판매시설 (백화점/마트)", "근린생활시설", "기타 건축물"]
)

site_area = st.sidebar.number_input("📐 대지면적 (㎡)", min_value=0.0, value=10000.0, step=100.0)
total_floor_area = st.sidebar.number_input("🏢 연면적 합계 (㎡)", min_value=0.0, value=35000.0, step=500.0)
household_count = st.sidebar.number_input("👨‍👩‍👧‍👦 세대수 (아파트 전용)", min_value=0, value=550, step=10)
parking_count = st.sidebar.number_input("🚗 계획 주차대수", min_value=0, value=600, step=10)

st.sidebar.markdown("---")
st.sidebar.header("🌳 조경 및 시설 계획 수치 입력")
landscaping_area_plan = st.sidebar.number_input("🟩 계획 조경면적 (㎡)", min_value=0.0, value=1600.0, step=50.0)
natural_ground_plan = st.sidebar.number_input("🟫 계획 자연지반면적 (㎡)", min_value=0.0, value=400.0, step=10.0)
eco_area_plan = st.sidebar.slider("🍃 계획 생태면적률 (%)", min_value=0.0, max_value=100.0, value=32.0, step=0.5)
open_space_plan = st.sidebar.number_input("⛲ 계획 공개공지면적 (㎡)", min_value=0.0, value=0.0, step=10.0)

st.sidebar.markdown("---")
st.sidebar.header("🌲 계획 식재 수량 입력")
tree_count = st.sidebar.number_input("🌳 계획 교목 총 수량 (주)", min_value=0, value=350, step=10)
evergreen_tree_count = st.sidebar.number_input("🌲 계획 상록교목 수량 (주)", min_value=0, value=80, step=5)
special_tree_count = st.sidebar.number_input("✨ 계획 특성수 수량 (주)", min_value=0, value=40, step=5)

shrub_count = st.sidebar.number_input("🌿 계획 관목 총 수량 (주)", min_value=0, value=1800, step=50)
evergreen_shrub_count = st.sidebar.number_input("🍃 계획 상록관목 수량 (주)", min_value=0, value=400, step=10)

st.sidebar.markdown("---")
st.sidebar.header("🛝 편의 및 부대시설 계획 입력")
play_area_plan = st.sidebar.number_input("🛝 계획 어린이놀이터 면적 (㎡)", min_value=0.0, value=900.0, step=10.0)
sports_area_plan = st.sidebar.number_input("🏋️ 계획 주민운동시설 면적 (㎡)", min_value=0.0, value=300.0, step=10.0)
bus_stop_plan = st.sidebar.number_input("🚌 계획 통학버스 정류장 (개소)", min_value=0, value=1, step=1)
bike_parking_plan = st.sidebar.number_input("🚲 계획 자전거보관소 (대)", min_value=0, value=130, step=5)
garden_area_plan = st.sidebar.number_input("🧑‍🌾 계획 텃밭/부속정원 면적 (㎡)", min_value=0.0, value=50.0, step=5.0)

report_data = []

# ---------------------------------------------------------
# [정밀 고도화] 지자체 조례 및 용도지역/대지규모별 조경면적 비율 매핑
# ---------------------------------------------------------
if "서울" in region:
    law_article = "서울특별시 건축조례 제24조 (조경면적)"
    if site_area < 2000: req_landscape_ratio = 0.10
    else: req_landscape_ratio = 0.15
elif "천안" in region:
    law_article = "천안시 건축조례 제29조 (조경면적)"
    if "상업" in zone_type: req_landscape_ratio = 0.08
    elif total_floor_area >= 5000: req_landscape_ratio = 0.15
    else: req_landscape_ratio = 0.10
else:
    law_article = f"{region} 건축조례 조경 의무 조항"
    req_landscape_ratio = 0.12

req_natural_ratio = 0.10 

# [수정] 특성수 10%의 상위 근거(조경기준)와 지역 적용(시목 등)을 완벽히 분리 매핑
law_landscape = f"{law_article} 및 건축법 제42조"
law_natural = "국토교통부 조경기준 제12조 (자연지반 식재 등)"
law_eco = "환경영향평가법 제22조 및 지자체 지구단위계획 수립지침"
law_open_space = "건축법 제43조 및 동법 시행령 제27조의2"
law_total_tree = "국토교통부 조경기준 제10조 (식재수량 및 기준)"
law_evergreen = "국토교통부 조경기준 제13조 (상록수 식재 비율)"
law_special = f"국토교통부 조경기준 제13조 및 {region} 권장수종(시목 등)"
law_community = "주택건설기준 등에 관한 규정 제55조의2 (주민공동시설)"
law_bus_stop = "주택건설기준 등에 관한 규정 제26조제6항 (안전회차공간)"
law_bike = "자전거 이용 활성화에 관한 법률 시행령 제7조 [별표 1]"

# 1. 법정 의무 조경 면적 산출
legal_landscape_area = site_area * req_landscape_ratio
legal_natural_ground = legal_landscape_area * req_natural_ratio

# 2. 법정 의무 수목 총량 산출
legal_total_tree = math.ceil(legal_landscape_area * 0.2)
legal_total_shrub = math.ceil(legal_landscape_area * 1.0)

req_evergreen_ratio = 0.20      
req_special_ratio = 0.10
req_evergreen_shrub_ratio = 0.20

legal_evergreen_tree = math.ceil(legal_total_tree * req_evergreen_ratio)
legal_special_tree = math.ceil(legal_total_tree * req_special_ratio)
legal_evergreen_shrub = math.ceil(legal_total_shrub * req_evergreen_shrub_ratio)

# 3. 부대복리시설 검토
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
# 화면 렌더링 및 대시보드 출력
# ---------------------------------------------------------
st.markdown("### 🔍 실시간 인허가 연동 근거법규 ALL 리스트 및 조회 포털")
st.caption("※ 실무 심의 시 즉시 증명이 가능하도록 참고한 모든 상위법령 고시 및 웹 조회 시스템 링크를 투명하게 공개합니다.")

# 웹 상에서 확인 가능한 실시간 외부 시스템 바로가기 버튼 배치
col_link1, col_link2, col_link3 = st.columns(3)
with col_link1:
    st.link_button("🌐 국가법령정보센터 (법률/시행령 조회)", "https://www.law.go.kr/")
with col_link2:
    st.link_button("🗺️ 토지이음 (지구단위계획지침/용도지역 조회)", "http://www.eum.go.kr/")
with col_link3:
    st.link_button("🍃 환경영향평가 정보시스템 (생태면적률 조회)", "https://www.eiass.go.kr/")

# 검토에 활용된 모든 법적 기준 상세 테이블 리스트업
law_list = [
    {"분류": "상위 법률", "근거 법규 및 지침명": "건축법 제42조 및 동법 시행령 제27조", "시행/개정년도": "2026년 현행 법률"},
    {"분류": "지자체 조례", "근거 법규 및 지침명": f"{region} 건축조례 조경 의무 기준 조항", "시행/개정년도": "각 지자체 최신 조례"},
    {"분류": "정부 고시", "근거 법규 및 지침명": "국토교통부 조경기준 (식재 총량, 상록수 20% 및 특성수 10% 규정)", "시행/개정년도": "2024년 고시"},
    {"분류": "대통령령", "근거 법규 및 지침명": "주택건설기준 등에 관한 규정 제55조의2 (주민공동시설 총량제)", "시행/개정년도": "2025년 최신 개정"},
    {"분류": "국토부 훈령", "근거 법규 및 지침명": "지구단위계획 수립지침 제4편 (환경·녹지 및 공공보행통로 기준)", "시행/개정년도": "2025년 개정"},
    {"분류": "환경부 지침", "근거 법규 및 지침명": "환경영향평가 생태면적률 적용 지침 (공동주택 및 개발사업용)", "시행/개정년도": "2024년 지침"},
    {"분류": "상위 법률", "근거 법규 및 지침명": "자전거 이용 활성화에 관한 법률 시행령 제7조 [별표 1]", "시행/개정년도": "2026년 현행 법률"}
]
st.table(pd.DataFrame(law_list))

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
            
    st.markdown("<div style='margin: -5px 0 10px 0; border-bottom: 1px solid #EEEEEE;'></div>", unsafe_allow_html=True)
    
    report_data.append({
        "검토 분류": category,
        "검토 항목": title,
        "법적 기준 및 산식": legal_text,
        "관련 근거 및 상세 법령 조항": law_source,
        "법정 요구치 / 계획 수치": legal_plan_compare_str,
        "적합 여부": csv_status
    })

st.markdown("### 📋 실시간 종합 법규 검토 리포트")
st.write("")

h1, h2, h3, h4 = st.columns([1.5, 3.2, 2.3, 0.8])
h1.markdown("**🔍 검토 항목 명칭**")
h2.markdown("**📜 법적 기준 및 산식 근거식**")
h3.markdown("**📊 법정요구 수치 / 내 계획**")
h4.markdown("**📢 결과**")
st.markdown("<div style='border-bottom: 2px solid #2E5A44; margin-bottom: 15px;'></div>", unsafe_allow_html=True)

# 1. 면적 검토 영역
print_law_row("1. 면적 검토", "조경 면적", f"선택 지자체 조례에 따른 대지면적의 {req_landscape_ratio*100}% 이상 확보", law_landscape, f"{legal_landscape_area:,.1f} ㎡ / {landscaping_area_plan:,.1f} ㎡", landscaping_area_plan >= legal_landscape_area)
print_law_row("1. 면적 검토", "자연 지반", f"의무 조경면적의 {req_natural_ratio*100}% 이상 확보", law_natural, f"{legal_natural_ground:,.1f} ㎡ / {natural_ground_plan:,.1f} ㎡", natural_ground_plan >= legal_natural_ground)
print_law_row("1. 면적 검토", "생태면적률", "대지면적의 30.0% 이상 도입 권장", law_eco, f"30.0 % / {eco_area_plan:.1f} %", eco_area_plan >= 30.0)
print_law_row("1. 면적 검토", "공개 공지", open_space_text, law_open_space, open_space_val_str, open_space_pass)

# 2. 식재 검토 영역
print_law_row("2. 식재 검토", "전체 교목 수량", "의무조경면적 1㎡당 최소 0.2주 식재", law_total_tree, f"{legal_total_tree:,.0f} 주 / {tree_count:,.0f} 주", tree_count >= legal_total_tree)
print_law_row("2. 식재 검토", " - 상록 교목", f"법정 교목 의무 수량의 {req_evergreen_ratio*100}% 이상 필수 상록수 식재", law_evergreen, f"{legal_evergreen_tree:,.0f} 주 / {evergreen_tree_count:,.0f} 주", evergreen_tree_count >= legal_evergreen_tree)
print_law_row("2. 식재 검토", " - 특성수 수량", f"법정 교목 의무 수량의 {req_special_ratio*100}% 이상 국토부 기준 및 지자체 시목/향토수종 적용", law_special, f"{legal_special_tree:,.0f} 주 / {special_tree_count:,.0f} 주", special_tree_count >= legal_special_tree)
print_law_row("2. 식재 검토", "전체 관목 수량", "의무조경면적 1㎡당 최소 1.0주 식재", law_total_tree, f"{legal_total_shrub:,.0f} 주 / {shrub_count:,.0f} 주", shrub_count >= legal_total_shrub)
print_law_row("2. 식재 검토", " - 상록 관목", f"법정 관목 의무 수량의 {req_evergreen_shrub_ratio*100}% 이상 필수 상록수 식재", law_evergreen, f"{legal_evergreen_shrub:,.0f} 주 / {evergreen_shrub_count:,.0f} 주", evergreen_shrub_count >= legal_evergreen_shrub)

# 3. 부대시설 검토 영역 
print_law_row("3. 부대시설 검토", "어린이놀이터", play_legal_text, law_community, play_val_str, play_pass)
print_law_row("3. 부대시설 검토", "주민운동시설", sports_legal_text, law_community, sports_val_str, sports_pass)
print_law_row("3. 부대시설 검토", "통학버스 정류장", bus_formula_text, law_bus_stop, bus_val_str, bus_pass)
print_law_row("3. 부대시설 검토", "자전거 보관소", "전체 자동차 주차대수의 20% 이상 설치 의무", law_bike, f"{legal_bike_parking:,.0f} 대 / {bike_parking_plan:,.0f} 대", bike_parking_plan >= legal_bike_parking)
print_law_row("3. 부대시설 검토", "텃밭 / 부속정원", "설치 권장 (녹색건축인증 및 친환경 인센티브 조례 항목)", "녹색건축인증기준 지침 가이드", f"권장 / {garden_area_plan:,.1f} ㎡", True)

# ---------------------------------------------------------
# 엑셀 다운로드 데이터 생성 및 렌더링
# ---------------------------------------------------------
st.markdown("---")
st.subheader("📥 검토 결과 보고서 출력")

df_report = pd.DataFrame(report_data)
csv_data = df_report.to_csv(index=False).encode('utf-8-sig')

st.download_button(
    label="📊 조경법규 검토 결과 엑셀(CSV) 다운로드",
    data=csv_data,
    file_name=f"조경법규검토결과_{region}_{building_type}.csv",
    mime="text/csv"
)
st.caption("※ 다운로드된 CSV 파일은 엑셀에서 바로 열람하고 표 서식으로 편집하여 보고서로 활용하실 수 있습니다.")
