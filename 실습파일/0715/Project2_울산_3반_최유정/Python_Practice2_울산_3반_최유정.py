# -*- coding: utf-8 -*-
"""
================================================================================
[실습 2] 파일 I/O · 예외 처리 · Pydantic 검증 파이프라인
================================================================================
프로그램 개요
--------------------------------------------------------------------------------
Python_Practice2_Data.json 의 판매(Sales) 데이터를 안전하게 읽어와,
Pydantic v2 스키마 검증 → valid/errors 분리 → 결과 파일 저장 → 재로딩 검증의
4단계 파이프라인을 수행한다.

  1) 예외 처리 + 파일 읽기
     - safe_load_csv() : 파일 없으면 None 반환·logger.error,
       성공 시 dict 리스트 반환·logger.info, finally 에서 '로딩 종료' 출력
  2) Pydantic v2 스키마 정의
     - SalesRecord 모델
       · month·region : 필수 (비어 있으면 안 됨)
       · amount       : 0 초과
       · category     : 선택 (없어도 됨)
  3) 검증 파이프라인 (valid / errors 분리)
     - raw_data 순회하며 SalesRecord 로 변환
     - 성공 → valid 리스트, 실패(ValidationError) → errors({row, error}) 리스트
  4) 결과 파일 저장 + 재로딩 확인
     - valid → CSV 저장, errors → JSON 저장(ensure_ascii=False)
     - 저장 파일을 다시 읽어 건수를 assert 로 검증

Checkpoint (통과 조건)
--------------------------------------------------------------------------------
  - safe_load_csv 동작 + (없는 파일에 대해) None 반환 assert 통과
  - ValidationError 발생 시 오류 내용 출력 (오류가 없으면 errors 0건)
  - valid + errors == 입력 건수 assert 통과 (누락/중복 없이 분리)
  - 재로딩 후 len(reloaded) == 저장 전 valid 건수 통과

변경 내역 (Change History)
--------------------------------------------------------------------------------
  2024-01-01  v1.0  최초 작성 (safe_load_csv + SalesRecord + 파이프라인)
  2024-01-02  v1.1  스키마 필수 필드 date → month·region 으로 변경 (요구사항 반영)
  2024-01-03  v1.2  데이터 파일을 Python_Practice2_Data.json 으로 교체
                    (최상위가 리스트 형태 — safe_load_csv 가 dict/list 모두 지원)
  2024-01-04  v1.3  인위적 오류 주입 제거 — 실제 데이터 전체를 그대로 검증하고,
                    assert 를 실제 건수 기준 동적 검증으로 변경

작성 규칙 (평가 기준 반영)
--------------------------------------------------------------------------------
  - 파일 입출력은 반드시 with + try-except(-finally) 로 감싼다.
  - 검증 실패는 Exception 이 아닌 'ValidationError' 로 구체적으로 잡는다.
  - 저장 시 모델 → dict 변환은 model_dump() 를 사용한다.
  - json.dump 는 ensure_ascii=False 로 한글 깨짐을 방지한다.
================================================================================
"""

import os
import csv
import json
import logging
from typing import Optional

from pydantic import BaseModel, Field, ValidationError, field_validator

# ------------------------------------------------------------------------------
# 로거 설정: print 대신 logger 로 로딩 성공/실패를 기록한다.
# ------------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# [1] 예외 처리 + 파일 읽기
#     - 파일 없음 → logger.error 후 None 반환
#     - 성공     → logger.info 후 dict 리스트 반환
#     - finally  → 성공/실패와 무관하게 '로딩 종료' 출력
# ------------------------------------------------------------------------------
def safe_load_csv(path: str) -> Optional[list]:
    """JSON 데이터 파일을 안전하게 읽어 dict 리스트(또는 실패 시 None)를 반환한다."""
    try:
        with open(path, encoding="utf-8") as f:  # with: 파일 자동 닫기
            data = json.load(f)
    except FileNotFoundError:
        logger.error(f"파일을 찾을 수 없습니다: {path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"JSON 형식 오류: {e}")
        return None
    else:
        # 최상위가 {"Sales": [...]} 이면 Sales 를, 아니면 data 자체를 사용
        rows = data.get("Sales", data) if isinstance(data, dict) else data
        logger.info(f"로딩 성공: {len(rows)}건")
        return rows
    finally:
        print("로딩 종료")  # 감점 방지: finally 블록 필수


# ------------------------------------------------------------------------------
# [2] Pydantic v2 스키마 정의
#     - month·region : 필수, 공백/빈 문자열 금지
#     - amount       : 0 초과 (gt=0)
#     - category     : 선택 필드 (없어도 됨)
# ------------------------------------------------------------------------------
class SalesRecord(BaseModel):
    month: str = Field(min_length=1)          # 필수: 비어 있으면 안 됨
    region: str = Field(min_length=1)         # 필수: 비어 있으면 안 됨
    amount: int = Field(gt=0)                 # 0 초과만 허용
    category: Optional[str] = None            # 선택: 없어도 됨

    @field_validator("month", "region")
    @classmethod
    def not_blank(cls, v: str) -> str:
        """공백만 있는 문자열('  ')도 '비어 있음'으로 간주해 거부한다."""
        if not v.strip():
            raise ValueError("빈 문자열은 허용되지 않습니다")
        return v.strip()


# ------------------------------------------------------------------------------
# [3] 검증 파이프라인 (valid / errors 분리)
#     - 성공 → valid(SalesRecord 리스트)
#     - 실패 → errors({row, error} dict 리스트)  ※ ValidationError 로 구체적으로 캐치
# ------------------------------------------------------------------------------
def validate_records(raw_data: list) -> tuple[list, list]:
    """raw_data 를 SalesRecord 로 변환해 (valid, errors) 두 리스트로 분리한다."""
    valid, errors = [], []
    for i, row in enumerate(raw_data):
        try:
            valid.append(SalesRecord(**row))
        except ValidationError as e:  # Exception 이 아닌 ValidationError 로 캐치
            errors.append({"row": row, "error": str(e)})
            print(f"[ValidationError] {i}번 행 검증 실패 → {row}")
            print(f"    {e.errors(include_url=False)}")
    return valid, errors


# ------------------------------------------------------------------------------
# [4] 결과 파일 저장 + 재로딩 확인
#     - valid  → CSV  (model_dump() 로 dict 변환 후 DictWriter 저장)
#     - errors → JSON (ensure_ascii=False 로 한글 보존)
# ------------------------------------------------------------------------------
def save_results(valid: list, errors: list, csv_path: str, json_path: str) -> None:
    """valid 는 CSV, errors 는 JSON 으로 저장한다."""
    fieldnames = list(SalesRecord.model_fields)  # 모델 정의 순서 그대로 헤더 구성
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rec.model_dump() for rec in valid)  # model_dump() 사용

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(errors, f, ensure_ascii=False, indent=2)   # 한글 깨짐 방지


def reload_and_verify(csv_path: str, json_path: str) -> tuple[list, list]:
    """저장한 CSV/JSON 을 다시 읽어 (reloaded, reloaded_errors)를 반환한다."""
    try:  # 재로딩도 '파일 읽기'이므로 예외 처리로 감싼다 (감점 방지)
        with open(csv_path, newline="", encoding="utf-8") as f:
            reloaded = list(csv.DictReader(f))
        with open(json_path, encoding="utf-8") as f:
            reloaded_errors = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"재로딩 실패: {e}")
        raise SystemExit("[오류] 저장 파일 재로딩에 실패했습니다.")
    return reloaded, reloaded_errors


# ------------------------------------------------------------------------------
# 메인 실행 흐름
# ------------------------------------------------------------------------------
def main():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_PATH = os.path.join(BASE_DIR, "Python_Practice2_Data.json")
    CSV_PATH = os.path.join(BASE_DIR, "valid_records.csv")
    JSON_PATH = os.path.join(BASE_DIR, "error_records.json")

    # ==== [1] 예외 처리 + 파일 읽기 ============================================
    print("=" * 60)
    print("[1] 예외 처리 + 파일 읽기 (safe_load_csv)")
    print("=" * 60)

    # Checkpoint ①: 없는 파일이면 None 이 반환되어야 한다.
    assert safe_load_csv(os.path.join(BASE_DIR, "no_such_file.json")) is None
    print("    ✓ 없는 파일 → None 반환 assert 통과\n")

    all_rows = safe_load_csv(DATA_PATH)
    if all_rows is None:  # 실제 데이터 로딩 실패 시 즉시 종료
        raise SystemExit("[오류] 데이터 로딩 실패로 프로그램을 종료합니다.")

    # 실제 데이터 '전체'를 그대로 검증 파이프라인에 투입한다.
    # (오류 레코드가 없으면 errors 는 0건 — 빈 JSON 파일이 저장되는 것이 정상)
    raw_data = all_rows
    print(f"    검증 대상: {len(raw_data)}건 (실제 데이터 전체)\n")

    # ==== [2] Pydantic v2 스키마 정의 ==========================================
    print("=" * 60)
    print("[2] Pydantic v2 스키마 정의 (SalesRecord)")
    print("=" * 60)
    print("    필드 구성:", ", ".join(SalesRecord.model_fields))
    print("    규칙: month·region 필수(빈 값 금지) / amount > 0 / category 선택\n")

    # ==== [3] 검증 파이프라인 (valid / errors 분리) ============================
    print("=" * 60)
    print("[3] 검증 파이프라인 (valid / errors 분리)")
    print("=" * 60)
    valid, errors = validate_records(raw_data)
    if not errors:
        print("    (검증 실패 레코드 없음 — 전체 통과)")
    print(f"\n    [검증 결과] valid: {len(valid)}건 / errors: {len(errors)}건")

    # Checkpoint ②: 분리 결과의 합이 입력 건수와 일치해야 한다 (누락/중복 없음)
    assert len(valid) + len(errors) == len(raw_data), "valid+errors 합계 불일치!"
    print("    ✓ valid + errors == 입력 건수 assert 통과\n")

    # ==== [4] 결과 파일 저장 + 재로딩 확인 =====================================
    print("=" * 60)
    print("[4] 결과 파일 저장 + 재로딩 확인")
    print("=" * 60)
    save_results(valid, errors, CSV_PATH, JSON_PATH)
    print(f"    저장 완료 → {os.path.basename(CSV_PATH)} / {os.path.basename(JSON_PATH)}")

    reloaded, reloaded_errors = reload_and_verify(CSV_PATH, JSON_PATH)
    print(f"    [재로딩] CSV: {len(reloaded)}건 / errors JSON: {len(reloaded_errors)}건")

    # Checkpoint ③: 재로딩 건수가 저장 전 건수와 정확히 일치해야 한다
    assert len(reloaded) == len(valid), "재로딩 CSV 건수 불일치!"
    assert len(reloaded_errors) == len(errors), "재로딩 errors 건수 불일치!"
    print(f"    ✓ 재로딩 len(reloaded)=={len(valid)} assert 통과")

    # 재로딩 데이터가 원본 valid 와 내용까지 일치하는지 확인 (amount 는 CSV 에서 str)
    assert [int(r["amount"]) for r in reloaded] == [v.amount for v in valid]
    print("    ✓ 재로딩 amount 값 일치 assert 통과")


if __name__ == "__main__":
    main()