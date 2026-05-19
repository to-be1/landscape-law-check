import streamlit as st
import pandas as pd
import math

# ---------------------------------------------------------
# 페이지 기본 설정 및 스타일
# ---------------------------------------------------------
st.set_page_config(page_title="조경 법규 자동 검토 시스템", layout="wide")

st.title("🌿 조경 법규 실시간 자동 검토 시스템")
st.caption("국토교통부 조경기준 및 지자체 조례 기반 자동 연산 엔진 (실시간 엑셀 출력 지원)")
st.markdown("---")

# ---------------------------------------------------------
# 사이드바: 건축 개요 입력 창
# ---------------------------------------------------------
st.sidebar.header("🏢 건축물 기본 개요 입력")

# 1. 대한민국 전체 지자체 리스트 적용
regions = [
    # --- 서울특별시 (25개구) ---
    "서울 강남구", "서울 강동구", "서울 강북구", "서울 강서구", "서울 관악구", "서울 광진구", "서울 구로구", "서울 금천구", "서울 노원구", "서울 도봉구", 
    "서울 동대문구", "서울 동작구", "서울 마포구", "서울 서대문구", "서울 서초구", "서울 성동구", "서울 성북구", "서울 송파구", "서울 양천구", "서울 영등포구", 
    "서울 용산구", "서울 은평구", "서울 종로구", "서울 중구", "서울 중랑구",
    
    # --- 부산광역시 (16개 군·구) ---
    "부산 강서구", "부산 금정구", "부산 기장군", "부산 남구", "부산 동구", "부산 동래구", "부산 부산진구", "부산 북구", "부산 사상구", "부산 사하구", 
    "부산 서구", "부산 수영구", "부산 연제구", "부산 영도구", "부산 중구", "부산 해운대구",
    
    # --- 대구광역시 (9개 군·구) ---
    "대구 군위군", "대구 남구", "대구 달서구", "대구 달성군", "대구 동구", "대구 북구", "대구 서구", "대구 수성구", "대구 중구",
    
    # --- 인천광역시 (10개 군·구) ---
    "인천 강화군", "인천 계양구", "인천 남동구", "인천 동구", "인천 미추홀구", "인천 부평구", "인천 서구", "인천 연수구", "인천 옹진군", "인천 중구",
    
    # --- 광주광역시 (5개구) ---
    "광주 광산구", "광주 남구", "광주 동구", "광주 북구", "광주 서구",
    
    # --- 대전광역시 (5개구) ---
    "대전 대덕구", "대전 동구", "대전 서구", "대전 유성구", "대전 중구",
    
    # --- 울산광역시 (5개 군·구) ---
    "울산 남구", "울산 동구", "울산 북구", "울산 울주군", "울산 중구",
    
    # --- 세종 및 제주 ---
    "세종특별자치시", "제주시", "서귀포시",
    
    # --- 경기도 (31개 시·군) ---
    "가평군", "고양시", "과천시", "광명시", "광주시", "구리시", "군포시", "김포시", "남양주시", "동두천시", 
    "부천시", "성남시", "수원시", "시흥시", "안산시", "안성시", "안양시", "양주시", "양평군", "여주시", 
    "연천군", "오산시", "용인시", "의왕시", "의정부시", "이천시", "파주시", "평택시", "포천시", "하남시", "화성시",
    
    # --- 강원특별자치도 ---
    "강릉시", "고성군", "동해시", "삼척시", "속초시", "양구군", "양양군", "영월군", "원주시", "인제군", 
    "정선군", "철원군", "춘천시", "태백시", "평창군", "홍천군", "화천군", "횡성군",
    
    # --- 충청북도 ---
    "괴산군", "단양군", "보은군", "영동군", "옥천군", "음성군", "제천시", "증평군", "진천군", "청주시", "충주시",
    
    # --- 충청남도 ---
    "계룡시", "공주시", "금산군", "논산시", "당진시", "보령시", "부여군", "서산시", "서천군", "아산시", 
    "예산군", "천안시", "청양군", "태안군", "홍성군",
    
    # --- 전북특별자치도 ---
    "고창군", "군산시", "김제시", "남원시", "무주군", "부안군", "순창군", "완주군", "익산시", "임실군", 
    "장수군", "전주시", "정읍시", "진안군",
    
    # --- 전라남도 ---
    "강진군", "고흥군", "곡성군", "광양시", "구례군", "나주시", "담양군", "목포시", "무안군", "보성군", 
    "순천시", "신안군", "여수시", "영광군", "영암군", "완도군", "장성군", "장흥군", "진도군", "함평군", 
    "해남군", "화순군",
    
    # --- 경상북도 ---
    "경산시", "경주시", "고령군", "구미시", "김천시", "문경시", "봉화군", "상주시", "성주군", "안동시", 
    "영덕군", "영양군", "영주시", "영천시", "예천군", "울릉군", "울진군", "의성군", "청도군", "청송군", 
    "칠곡군", "포항시",
    
    # --- 경상남도 ---
    "거제시", "거창군", "고성군", "김해시", "남해군", "밀양시", "사천시", "산청군", "양산시", "의령군", 
    "진주시", "창녕군", "창원시", "통영시", "하동군", "함안군", "함양군", "합천군"
]

region = st.sidebar.selectbox("📍 대상 지자체 선택", regions, index=regions.index("천안시") if "천안시" in regions else 0)

zone_type = st.sidebar.selectbox(
    "🗺️ 용도지역 분류",
    ["일반주거지역", "준주거지역", "중심상업지역", "일반상업지역", "근린상업지역", "유통상업지역", "준공업지역", "기타지역"]
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

# 엑셀 출력을 위한 데이터 저장용 리스트
report_data = []

# ---------------------------------------------------------
# 법규 계산 로직 (수목 식재 및 어린이놀이터 총량제 정밀 교정 완료)
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

# 1. 법정 의무 조경 면적 산출
legal_landscape_area = site_area * req_landscape_ratio
legal_natural_ground = legal_landscape_area * req_natural_ratio

# 2. 법정 의무 수목 총량 산출 (법정 조경면적 기준: 교목 0.2주/㎡, 관목 1.0주/㎡)
legal_total_tree = math.ceil(legal_landscape_area * 0.2)
legal_total_shrub = math.ceil(legal_landscape_area * 1.0)

# [교정 핵심] 법정요구치는 내 계획 수량이 아니라, '법정 의무 총량' 기준으로 고정됩니다.
req_evergreen_ratio = 0.20      
req_special_ratio = 0.10
req_evergreen_shrub_ratio = 0.20

legal_evergreen_tree = math.ceil(legal_total_tree * req_evergreen_ratio)
legal_special_tree = math.ceil(legal_total_tree * req_special_ratio)
legal_evergreen_shrub = math.ceil(legal_total_shrub * req_evergreen_shrub_ratio)

law_total_tree = "국토교통부 조경기준 제10조"
law_evergreen = "국토교통부 조경기준 제13조"
law_special = "지자체 조경기준 가이드라인"

law_housing = "주택건설기준 등에 관한 규정"
law_bike = "자전거이용 활성화에 관한 법률 시행령"

# 3. 부대복리시설 검토 - 주민공동시설 총량 규제 시스템 적용
if building_type != "공동주택 (아파트)":
    play_val_str, play_pass, play_formula_text = "해당사항 없음", "N/A", "비대상 건축물"
    sports_val_str, sports_pass, sports_formula_text = "해당사항 없음", "N/A", "비대상 건축물"
    bus_val_str, bus_pass, bus_formula_text = "해당사항 없음", "N/A", "비대상 건축물"
else:
    # 주민공동시설 총량제 기준 산식 적용 (제55조의2)
    if household_count < 100:
        total_community_legal = 0
        play_formula_text = "100세대 미만: 총량제 의무 없음"
    elif household_count < 1000:
        total_community_legal = household_count * 2.5
        play_formula_text = f"총량제 대상(100~1000미만): 세대수×2.5㎡ (총 의무: {total_community_legal:,.1f}㎡)"
    else:
        total_community_legal = (household_count * 3.0) + 500
        play_formula_text = f"총량제 대상(1000세대 이상): 500㎡+(세대수×3㎡) (총 의무: {total_community_legal:,.1f}㎡)"
        
    # 어린이놀이터 및 주민운동시설은 총량 범위 내에서 배치하므로 계획면적 기록 표기
    play_val_str = f"총량내 확보 / {play_area_plan:,.1f} ㎡"
    play_pass = True if play_area_plan > 0 else False
    
    if household_count < 300:
        sports_formula_text = "300세대 미만: 의무 없음"
        sports_val_str, sports_pass = f"0 ㎡ / {sports_area_plan:,.1f} ㎡", True
    else:
        sports_formula_text = "주민공동시설 총량제 포함 설치 필수"
        sports_val_str, sports_pass = f"총량내 확보 / {sports_area_plan:,.1f} ㎡", sports_area_plan > 0
        
    if household_count < 500:
        bus_formula_text = "500세대 미만: 의무 없음"
        bus_val_str, bus_pass = f"0 개소 / {bus_stop_plan} 개소", True
    else:
        bus_formula_text = "500세대 이상: 1개소 이상 의무"
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
# 출력 및 데이터 수집 헬퍼 함수
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
    
    report_data.append({
        "검토 분류": category,
        "검토 항목": title,
        "법적 기준 및 산식": legal_text,
        "관련 근거(법령/조례)": law_source,
        "법정 요구치 / 계획 수치": legal_plan_compare_str,
        "적합 여부": pass_result
    })

# ---------------------------------------------------------
# 화면 렌더링 및 엑셀 데이터 적재
# ---------------------------------------------------------
st.markdown("### 📋 실시간 종합 법규 검토 리포트")
st.info(f"검토 조건: {region} | {zone_type} | {building_type} | 대지면적: {site_area:,.1f}㎡")
st.write("")

st.markdown("#### 1. 대지, 조경 및 생태 면적 검토")
cat1 = "1. 면적 검토"
print_row(cat1, "조경 면적", f"대지면적의 {req_landscape_ratio*100}%", law_landscape, f"{legal_landscape_area:,.1f} ㎡ / {landscaping_area_plan:,.1f} ㎡", landscaping_area_plan >= legal_landscape_area)
print_row(cat1, "자연 지반", f"조경면적의 {req_natural_ratio*100}%", law_natural, f"{legal_natural_ground:,.1f} ㎡ / {natural_ground_plan:,.1f} ㎡", natural_ground_plan >= legal_natural_ground)
print_row(cat1, "생태면적률", "대지면적의 30.0% 이상", law_eco, f"30.0 % / {eco_area_plan:.1f} %", eco_area_plan >= 30.0)
print_row(cat1, "공개 공지", open_space_text, "건축법 제43조", open_space_val_str, open_space_pass)

st.markdown("---")
st.markdown("#### 2. 수목 식재 총량 및 세부 수량 검토 (법정 의무량 대비 계산)")
cat2 = "2. 식재 검토"
print_row(cat2, "전체 교목 수량", "의무조경면적 1㎡당 0.2주", law_total_tree, f"{legal_total_tree:,.0f} 주 / {tree_count:,.0f} 주", tree_count >= legal_total_tree)
print_row(cat2, " - 상록 교목", f"교목 의무량의 {req_evergreen_ratio*100}% 이상", law_evergreen, f"{legal_evergreen_tree:,.0f} 주 / {evergreen_tree_count:,.0f} 주", evergreen_tree_count >= legal_evergreen_tree)
print_row(cat2, " - 특성수 수량", f"교목 의무량의 {req_special_ratio*100}% 이상", law_special, f"{legal_special_tree:,.0f} 주 / {special_tree_count:,.0f} 주", special_tree_count >= legal_special_tree)
print_row(cat2, "전체 관목 수량", "의무조경면적 1㎡당 1.0주", law_total_tree, f"{legal_total_shrub:,.0f} 주 / {shrub_count:,.0f} 주", shrub_count >= legal_total_shrub)
print_row(cat2, " - 상록 관목", f"관목 의무량의 {req_evergreen_shrub_ratio*100}% 이상", law_evergreen, f"{legal_evergreen_shrub:,.0f} 주 / {evergreen_shrub_count:,.0f} 주", evergreen_shrub_count >= legal_evergreen_shrub)

st.markdown("---")
st.markdown("#### 3. 부대 및 복리시설 검토 (공동주택 기준)")
cat3 = "3. 부대/복리시설 검토"
print_row(cat3, "어린이놀이터", play_formula_text, "주택건설기준 규정 제55조의2 (총량제)", play_val_str, play_pass)
print_row(cat3, "주민운동시설", sports_formula_text, "주택건설기준 규정 제55조의2 (총량제)", sports_val_str, sports_pass)
print_row(cat3, "통학버스 정류장", bus_formula_text, law_housing, bus_val_str, bus_pass)
print_row(cat3, "자전거 보관소", "자동차 주차대수의 20% 이상", law_bike, f"{legal_bike_parking:,.0f} 대 / {bike_parking_plan:,.0f} 대", bike_parking_plan >= legal_bike_parking)
print_row(cat3, "텃밭 / 부속정원", "설치 권장 (녹색건축인증 / 지자체 조례)", "녹색건축인증(G-SEED) 등", f"권장 / {garden_area_plan:,.1f} ㎡", True)

# ---------------------------------------------------------
# 엑셀 다운로드 데이터 생성 및 버튼 (NameError 완전 해결)
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
