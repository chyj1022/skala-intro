# -*- coding: utf-8 -*-
"""
================================================================================
[실습 1] 자료구조 집계 · 컴프리헨션 · 제너레이터
================================================================================
프로그램 개요
--------------------------------------------------------------------------------
Python_Practice1_Data.json 의 판매(Sales) 데이터를 읽어와,
파이썬 자료구조와 표준 라이브러리를 활용해 아래 4가지 집계를 수행한다.

  1) 리스트/딕셔너리 컴프리헨션
     - amount >= 1000 거래만 필터링
     - 지역별 총매출 dict 를 '딕셔너리 컴프리헨션'으로 계산
  2) Counter + defaultdict
     - Counter        : 지역별 거래 '건수'
     - defaultdict    : 카테고리별 amount '리스트'
  3) 제너레이터 — 메모리 비교
     - amount > 1000 인 행만 yield 하는 제너레이터 작성
     - 리스트 버전과 sys.getsizeof 로 메모리 크기 비교
  4) 종합 — 월별·카테고리 매출 집계
     - (month, category) 기준 그룹핑하여 총매출 dict 완성 (컴프리헨션 + defaultdict)

변경 내역 (Change History)
--------------------------------------------------------------------------------
  2024-01-01  v1.0  최초 작성 (4개 집계 + Checkpoint assert + 예외 처리)

작성 규칙 (평가 기준 반영)
--------------------------------------------------------------------------------
  - 반복 로직은 for 문 대신 '컴프리헨션'을 사용한다.
  - 조건부 누적은 'if key not in dict' 대신 collections 자료구조를 사용한다.
  - 파일 입출력/파싱은 예외 처리로 감싼다.
================================================================================
"""

import os
import sys
import json
from collections import Counter, defaultdict


# ------------------------------------------------------------------------------
# [0] 데이터 로딩
#     - 파일이 없거나(FileNotFoundError) JSON 형식이 깨진 경우(JSONDecodeError)를
#       구분해 안내한다. (예외/오류 처리)
#     - 슬라이드 표기 'json(Sales)' 에 맞춰 최상위 키 "Sales" 를 우선 조회하되,
#       파일이 곧바로 리스트인 경우도 허용한다.
# ------------------------------------------------------------------------------
def load_sales(path: str) -> list:
    """JSON 파일을 읽어 판매 레코드 리스트(list[dict])를 반환한다."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        raise SystemExit(f"[오류] 데이터 파일을 찾을 수 없습니다: {path}")
    except json.JSONDecodeError as e:
        raise SystemExit(f"[오류] JSON 형식이 올바르지 않습니다: {e}")

    # 최상위가 {"Sales": [...]} 형태이면 Sales를, 아니면 data 자체를 사용
    sales = data.get("Sales", data) if isinstance(data, dict) else data

    if not isinstance(sales, list) or not sales:
        raise SystemExit("[오류] 판매 데이터(list)가 비어 있거나 형식이 다릅니다.")
    return sales


# ------------------------------------------------------------------------------
# [1] 리스트/딕셔너리 컴프리헨션
#     ① amount >= 1000 필터링  (리스트 컴프리헨션)
#     ② 지역별 총매출 dict      (딕셔너리 컴프리헨션)
# ------------------------------------------------------------------------------
def summarize_region_total(sales: list) -> tuple[list, dict]:
    """1000 이상 거래 리스트와 '지역별 총매출' dict 를 반환한다."""
    # ① 리스트 컴프리헨션: 고액 거래(amount >= 1000)만 남긴다.
    high_value = [row for row in sales if row["amount"] >= 1000]

    # ② 딕셔너리 컴프리헨션: 지역 집합을 순회하며 지역별 합계를 계산한다.
    #    (고액 거래 기준 집계)
    regions = {row["region"] for row in high_value}
    region_total = {
        region: sum(r["amount"] for r in high_value if r["region"] == region)
        for region in regions
    }
    return high_value, region_total


# ------------------------------------------------------------------------------
# [2] Counter + defaultdict
#     - Counter    : 지역별 거래 '건수' (수동 카운팅 금지)
#     - defaultdict: 카테고리별 amount '리스트' (if key 패턴 금지)
# ------------------------------------------------------------------------------
def count_and_group(sales: list) -> tuple[Counter, defaultdict]:
    """지역별 거래 건수(Counter)와 카테고리별 금액 리스트(defaultdict)를 반환한다."""
    # Counter: 지역 값만 뽑아 한 번에 카운팅
    region_counter = Counter(row["region"] for row in sales)

    # defaultdict(list): 카테고리 키가 없어도 자동으로 빈 리스트 생성
    category_amounts = defaultdict(list)
    for row in sales:  # 그룹 '누적'은 컴프리헨션 대상이 아니므로 append 사용
        category_amounts[row["category"]].append(row["amount"])

    return region_counter, category_amounts


# ------------------------------------------------------------------------------
# [3] 제너레이터 — 메모리 비교
#     - amount > 1000 행만 yield 하는 제너레이터
#     - 동일 조건 리스트와 sys.getsizeof 비교
#       (주의) 제너레이터를 list()로 변환하면 메모리 이점이 사라지므로,
#              제너레이터 '객체 자체'의 크기를 리스트와 비교한다.
# ------------------------------------------------------------------------------
def high_amount_gen(sales: list):
    for row in sales:
        if row["amount"] > 1000:
            yield row  # 조건에 맞는 행을 한 건 내어주고 일시정지


def compare_memory(sales: list) -> tuple[int, int]:
    """(제너레이터 크기, 리스트 크기) 바이트를 반환한다."""
    gen = high_amount_gen(sales)                          # 지연 평가 → 항목을 담지 않음
    lst = [row for row in sales if row["amount"] > 1000]  # 즉시 평가 → 전 항목 적재

    gen_size = sys.getsizeof(gen)   # 제너레이터 객체 자체 크기
    list_size = sys.getsizeof(lst)  # 리스트 컨테이너 크기
    return gen_size, list_size


# ------------------------------------------------------------------------------
# [4] 종합 — 월별·카테고리 매출 집계
#     - (month, category) 로 그룹핑하여 총매출 dict 완성
#     - defaultdict 로 누적 후, 딕셔너리 컴프리헨션으로 '금액 내림차순' dict 구성
#       (top3 는 이 결과의 앞 3개가 된다)
# ------------------------------------------------------------------------------
def monthly_category_total(sales: list) -> dict:
    """{(month, category): 총매출} dict 를 '금액 내림차순'으로 반환한다."""
    grouped = defaultdict(int)
    for row in sales:  # (month, category) 키에 amount 누적
        grouped[(row["month"], row["category"])] += row["amount"]

    # 딕셔너리 컴프리헨션: 금액(value) 기준 내림차순으로 정렬된 결과 dict 생성
    # (파이썬 3.7+ 은 dict 가 삽입 순서를 유지하므로 정렬 순서가 보존된다)
    return {
        key: total
        for key, total in sorted(grouped.items(), key=lambda kv: kv[1], reverse=True)
    }


# ------------------------------------------------------------------------------
# 메인 실행 흐름
# ------------------------------------------------------------------------------
def main():
    # 이 스크립트가 있는 폴더를 기준으로 경로를 만든다.
    # (터미널 실행 위치와 무관하게 항상 같은 폴더의 데이터 파일을 찾도록 함)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_PATH = os.path.join(BASE_DIR, "Python_Practice1_Data.json")
    sales = load_sales(DATA_PATH)
    print(f"[로딩] 총 거래 건수: {len(sales)}건\n")

    # ---- [1] 리스트/딕셔너리 컴프리헨션 --------------------------------------
    #      ① 필터링된 거래 '전체'를 먼저 보여주고, ② 지역별 총매출을 계산한다.
    high_value, region_total = summarize_region_total(sales)
    print(f"[1-①] amount>=1000 필터링 결과: {len(high_value)}건 (전체 출력)")
    for i, row in enumerate(high_value, 1):
        print(f"    {i:2d}. {row['region']} | {row['category']} | "
              f"{row['amount']:,} | {row['month']}")
    print(f"\n[1-②] 지역별 총매출: {region_total}")

    # Checkpoint: region_total 값 정확 (독립적 재계산과 일치하는지 assert)
    expected = defaultdict(int)
    for row in high_value:
        expected[row["region"]] += row["amount"]
    assert region_total == dict(expected), "region_total 계산 불일치!"
    print("    ✓ region_total assert 통과\n")

    # ---- [2] Counter + defaultdict ------------------------------------------
    region_counter, category_amounts = count_and_group(sales)
    print("[2] 지역별 거래건수(most_common):", region_counter.most_common())
    print("    카테고리별 금액 개수:",
          {cat: len(amts) for cat, amts in category_amounts.items()})

    # Checkpoint: most_common() 은 건수 내림차순 정렬되어야 한다.
    counts_only = [cnt for _, cnt in region_counter.most_common()]
    assert counts_only == sorted(counts_only, reverse=True), "most_common 정렬 오류!"
    print("    ✓ most_common 내림차순 assert 통과\n")

    # ---- [3] 제너레이터 메모리 비교 -----------------------------------------
    gen_size, list_size = compare_memory(sales)
    print(f"[3] 제너레이터 크기: {gen_size} bytes / 리스트 크기: {list_size} bytes")

    # Checkpoint: generator 크기 < list 크기
    assert gen_size < list_size, "제너레이터가 리스트보다 크거나 같습니다!"
    print("    ✓ generator < list assert 통과\n")

    # ---- [4] 월별·카테고리 매출 집계 (금액 내림차순) --------------------------
    #      결과 dict 자체가 내림차순이므로 앞 3개가 곧 top3 이다.
    mc_total = monthly_category_total(sales)
    print("[4] 월별·카테고리 매출 집계 (금액 내림차순):")
    for rank, ((month, cat), total) in enumerate(mc_total.items(), 1):
        marker = " ★ top3" if rank <= 3 else ""
        print(f"    {rank:2d}. {month} | {cat} : {total:,}{marker}")

    # Checkpoint: top3 금액 내림차순 정렬 정확 (결과 dict 의 앞 3개로 확인)
    top3_values = [total for total in list(mc_total.values())[:3]]
    assert top3_values == sorted(top3_values, reverse=True), "top3 정렬 오류!"
    # 추가 검증: 전체 결과가 내림차순인지도 확인
    all_values = list(mc_total.values())
    assert all_values == sorted(all_values, reverse=True), "전체 내림차순 정렬 오류!"
    print("    ✓ top3(및 전체) 내림차순 assert 통과")


if __name__ == "__main__":
    main()
