import streamlit as st
import pandas as pd
import math
import re

# ---------------------------------------------------------
# 1. 시스템 설정 및 데이터셋 정의
# ---------------------------------------------------------
st.set_page_config(page_title="Pro 조경 법규 검토 시스템", layout="wide")

# 계층형 지역 DB (수정 시 여기만 건드리면 됩니다)
REGION_DB = {
    "서울특별시": ["강남구", "은평구", "마포구", "종로구", "송파구", "서초구", "기타"],
    "인천광역시": ["부평구", "남동구", "계양구", "연수구", "미추홀구", "서구"],
    "경기도": ["부천시", "수원시", "성남시", "화성시", "안양시", "고양시", "기타"],
    "전북특별자치도": ["전주시"],
    "충청북도": ["제천시", "충주시", "청주시"],
    "충청남도": ["천안시", "아산시"],
    "광주광역시": ["광산구", "북구", "서구", "남구", "동구"],
    "부산광역시": ["해운대구", "수영구", "동래구", "부산진구", "기타"],
    "대구광역시": ["수성구", "달서구", "중구", "동구", "기타"],
    "대전광역시": ["유성구", "서구", "중구", "동구", "기타"]
}

st.title("🌿 조경 법규 실시간 종합 검토 시스템")
st.markdown("---")

# ---------------------------------------------------------
# 2. 사이드바 입력 엔진
# ---------------------------------------------------------
st.sidebar.header("🏢 1. 건축물 기본 개요")
selected_city = st.sidebar.selectbox("🏠 시/도 선택", list(REGION_DB.keys()))
selected_district = st.sidebar.selectbox("📍 시/군/구 선택", REGION_DB[selected_city])

zone_type = st.sidebar.selectbox("🗺️ 용도지역 분류", ["일반주거지역", "준주거지역", "중심상업지역", "일반상업지역", "근린상업지역", "준공업지역", "기타지역"])
special_district = st.sidebar.selectbox("⛰️ 용도지구 분류", ["해당 없음 (일반 지역)", "자연경관지구", "역사문화환경보존지구", "고도지구"])
building_type = st.sidebar.selectbox("🏢 건축물 용도", ["공동주택 (아파트)", "업무시설", "판매시설", "근린생활시설", "기타 건축물"])

site_area = st.sidebar.number_input("📐 대지면적 (㎡)", value=13104.0, step=100.0)
total_floor_area = st.sidebar.number_input("🏢 연면적 (㎡)", value=35000.0, step=500.0)
household_count = st.sidebar.number_input("👨‍👩‍👧‍👦 세대수", value=314, step=10)
legal_parking = st.sidebar.number_input("🚙 법정 주차대수", value=100, step=10)

st.sidebar.markdown("---")
st.sidebar.header("📋 2. 법규/계획 적용 엔진")
is_district_unit = st.sidebar.checkbox("🚀 지구단위계획 우선 적용 모드")
target_landscape_ratio = st.sidebar.number_input("🎯 지구단위계획 조경률(%)", value=20.0, step=1.0) / 100.0 if is_district_unit else 0.15

use_dynamic_parsing = st.sidebar.checkbox("⚙️ 조례 원문 파싱 모드")
raw_law_text = st.sidebar.text_area("📄 조례 원문 붙여넣기", height=80) if use_dynamic_parsing else ""

project_category = st.sidebar.radio("사업 성격", ["일반 신축", "소규모재건축/가로주택"])
is_small_scale = (project_category == "소규모재건축/가로주택")

# ---------------------------------------------------------
# 3. 로직 처리 엔진 (계산 핵심)
# ---------------------------------------------------------
def get_rules(city, district, floor_area, zone, district_type):
    if use_dynamic_parsing and raw_law_text:
        match = re.search(r'대지면적의\s*(\d+(?:\.\d+)?)\s*(?:퍼센트|%)', raw_law_text)
        if match: return float(match.group(1)) / 100.0, "원문 파싱 적용"
    
    if is_district_unit: return target_landscape_ratio, "지구단위계획 시행지침"
    
    if district_type == "자연경관지구": return 0.30, "도시계획조례(자연경관지구)"
    
    # 지자체 매핑
    if city == "서울특별시": return (0.15 if floor_area >= 2000 else 0.10), "서울특별시 건축조례"
    if city == "인천광역시": return (0.15 if floor_area >= 2000 else 0.10 if floor_area >= 1000 else 0.05), "인천광역시 건축조례"
    if city == "경기도":
        if district == "부천시": return 0.20, "부천시 건축조례"
        if district == "수원시": return (0.05 if "중심상업" in zone else 0.18 if floor_area >= 5000 else 0.15), "수원시 건축조례"
        return 0.15, "일반 건축조례"
    if city == "전북특별자치도": return 0.18, "전주시 건축조례"
    
    return 0.15, "건축법 조경기준"

ratio, law_source = get_rules(selected_city, selected_district, total_floor_area, zone_type, special_district)
if is_small_scale: ratio *= 0.5

# 계산
landscape_area = site_area * ratio
total_tree = math.ceil(landscape_area * 0.2)
total_shrub = math.ceil(landscape_area * 1.0)
bike_park = math.ceil(legal_parking * 0.20)

# ---------------------------------------------------------
# 4. 결과 출력
# ---------------------------------------------------------
st.markdown("### 📋 실시간 검토 리포트")
st.info(f"적용 기준: **{law_source}** | 조경의무율: **{ratio*100:.1f}%**")

cols = st.columns(4)
cols[0].metric("법정 조경면적", f"{landscape_area:,.1f} ㎡")
cols[1].metric("법정 교목수량", f"{total_tree:,} 주")
cols[2].metric("법정 관목수량", f"{total_shrub:,} 주")
cols[3].metric("법정 자전거 보관소", f"{bike_park:,} 대")

st.markdown("---")
if is_small_scale: st.warning("⚠️ 소규모 주택정비 특례(조경 1/2 완화)가 적용 중입니다.")

# 엑셀 다운로드 (Report Data)
report_df = pd.DataFrame([{
    "항목": "조경면적", "법적기준": f"{ratio*100}%", "법정수량": landscape_area
}, {
    "항목": "교목수량", "법적기준": "0.2주/㎡", "법정수량": total_tree
}])
st.download_button("📊 보고서 다운로드(CSV)", report_df.to_csv(index=False), "조경검토결과.csv")
