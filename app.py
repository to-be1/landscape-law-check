import streamlit as st
import pandas as pd
import math
import re

# ---------------------------------------------------------
# [핵심] 계층형 지역 DB (필요시 계속 추가 가능)
# ---------------------------------------------------------
REGION_DB = {
    "서울특별시": ["강남구", "은평구", "마포구", "종로구", "송파구", "서초구"],
    "인천광역시": ["부평구", "남동구", "계양구", "연수구", "미추홀구", "서구"],
    "경기도": ["부천시", "수원시", "성남시", "화성시", "안양시", "고양시"],
    "전북특별자치도": ["전주시"],
    "충청북도": ["제천시", "충주시", "청주시"],
    "충청남도": ["천안시", "아산시"]
}

# ---------------------------------------------------------
# 페이지 기본 설정
# ---------------------------------------------------------
st.set_page_config(page_title="조경 법규 마스터 검토 시스템", layout="wide")
st.title("🌿 조경 법규 실시간 종합 검토 시스템")

# ---------------------------------------------------------
# 사이드바: 1. 계층형 주소 선택 및 기본 개요
# ---------------------------------------------------------
st.sidebar.header("🏢 1. 프로젝트 기본 정보")

# 계층형 선택 구현
selected_city = st.sidebar.selectbox("🏠 시/도 선택", list(REGION_DB.keys()))
selected_district = st.sidebar.selectbox("📍 시/군/구 선택", REGION_DB[selected_city])
local_gov_name = selected_district # 검토 로직은 '구' 단위 기준

project_address = f"{selected_city} {selected_district}"

zone_type = st.sidebar.selectbox("🗺️ 용도지역 분류", ["일반주거지역", "준주거지역", "중심상업지역", "일반상업지역", "근린상업지역", "준공업지역", "기타지역"])
special_district = st.sidebar.selectbox("⛰️ 용도지구 분류", ["해당 없음 (일반 지역)", "자연경관지구", "역사문화환경보존지구", "고도지구"])
building_type = st.sidebar.selectbox("🏢 건축물 용도", ["공동주택 (아파트)", "업무시설", "판매시설", "근린생활시설", "기타 건축물"])

site_area = st.sidebar.number_input("📐 계획 대지면적 (㎡)", value=13104.0, step=100.0)
total_floor_area = st.sidebar.number_input("🏢 연면적 합계 (㎡)", value=35000.0, step=500.0)
household_count = st.sidebar.number_input("👨‍👩‍👧‍👦 계획 세대수", value=314, step=10)
legal_parking_count = st.sidebar.number_input("🚙 법정 주차대수", value=100, step=10)
plan_parking_count = st.sidebar.number_input("🚗 계획 주차대수", value=100, step=10)

# ---------------------------------------------------------
# [기능 유지] 특례법 및 원문 파싱 엔진
# ---------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.header("📡 2. 법규 원문 파싱 엔진")
use_dynamic_parsing = st.sidebar.checkbox("⚙️ 동적 원문 파싱 모드", value=False)
raw_law_text = ""
parsed_ratio = None
if use_dynamic_parsing:
    raw_law_text = st.sidebar.text_area("📄 조례 원문 붙여넣기", height=100)
    match_dyn = re.search(r'대지면적의\s*(\d+(?:\.\d+)?)\s*(?:퍼센트|%)', raw_law_text)
    if match_dyn: parsed_ratio = float(match_dyn.group(1)) / 100.0

# ---------------------------------------------------------
# 🧠 조경 비율 매핑 엔진 (계층형 선택 기반)
# ---------------------------------------------------------
def get_landscape_ratio(city, district, floor_area, zone, district_type):
    # 1. 특수지구 우선 적용
    if district_type == "자연경관지구": return 0.30, f"{city} 도시계획조례 (자연경관지구)"
    
    # 2. 지자체별 조례 맵핑
    if city == "서울특별시":
        return (0.15 if floor_area >= 2000 else 0.10), "서울특별시 건축조례 제24조"
    elif city == "인천광역시":
        if floor_area >= 2000: return 0.15, "인천광역시 건축조례 제27조"
        elif floor_area >= 1000: return 0.10, "인천광역시 건축조례 제27조"
        else: return 0.05, "인천광역시 건축조례 제27조"
    elif city == "경기도":
        if district == "부천시": return 0.20, "부천시 건축조례 제24조"
        if district == "수원시":
            if "중심상업" in zone: return 0.05, "수원시 건축조례 제31조"
            return 0.18, "수원시 건축조례 제31조"
        return 0.15, "일반 건축조례 기준"
    elif city == "전북특별자치도":
        return 0.18, "전주시 건축조례 제23조"
    
    return 0.15, "일반 건축법 조경기준"

req_landscape_ratio, law_article = get_landscape_ratio(selected_city, local_gov_name, total_floor_area, zone_type, special_district)

# [사용자가 원문 파싱을 우선할 경우 덮어쓰기]
if use_dynamic_parsing and parsed_ratio:
    req_landscape_ratio = parsed_ratio
    law_article = f"[동적 원문 파싱 적용] {local_gov_name} 조례"

# ---------------------------------------------------------
# 결과 연산 (이후 로직은 동일)
# ---------------------------------------------------------
legal_landscape_area = site_area * req_landscape_ratio
legal_total_tree = math.ceil(legal_landscape_area * 0.2)
legal_total_shrub = math.ceil(legal_landscape_area * 1.0)

# 화면 렌더링 영역 (이전과 동일하게 유지)
st.markdown(f"### 📋 검토 결과 요약")
st.success(f"적용 기준: **{law_article}** (조경의무율: **{req_landscape_ratio*100}%**)")

c1, c2, c3 = st.columns(3)
c1.metric("법정 조경면적", f"{legal_landscape_area:,.1f} ㎡")
c2.metric("법정 교목수량", f"{legal_total_tree} 주")
c3.metric("법정 관목수량", f"{legal_total_shrub} 주")

st.markdown("---")
st.write("※ 상세 검토 리포트 및 나머지 부대시설 로직은 기존과 동일합니다.")
