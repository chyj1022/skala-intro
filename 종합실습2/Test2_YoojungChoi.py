# // ==============================================================================
# //  FILE:         Test2_YoojungChoi.py
# //  AUTHOR:       최 유 정
# //  PURPOSE:      데이터 분석을 위한 Python 이해
# //  LAST UPDATED: 2026-07-16
# //  COPYRIGHT:    Copyright (c) SK AX SKALA (SK AI Leader Academy)
# // ==============================================================================

# ─── HISTORY ──────────────────────────────────────────────────────────────────
# - [2026-07-16] 최 유 정 : 최초 생성 및 베이스라인 모델 구축 완료
# - [2026-07-16] 최 유 정 : 채점 범위 확정 반영 — 모델 학습·성능 확인를
#                           '파이프라인 작성' 범위에 포함하기로 확정하고 유지

# ─── HOW TO RUN (설치 및 실행 방법) ────────────────────────────────────────────
# 1. 요구 환경  : Python 3.10 이상
#                 데이터 파일('서울시 상권분석서비스(추정매출-상권).csv')을
#                 본 스크립트와 같은 폴더에 배치 (CP949 인코딩 원본 그대로 사용)
# 2. 패키지 설치 :
#       python -m venv .venv
#       .venv\Scripts\activate            # Windows  (macOS/Linux: source .venv/bin/activate)
#       pip install pandas matplotlib scikit-learn
# 3. 실행 방법  :
#       python Test2_YoojungChoi.py
#       (CSV가 다른 위치에 있다면: python Test2_YoojungChoi.py <CSV_파일_경로>)
#    실행 결과 확인 :
#       - 콘솔 출력 : 데이터 로드 요약 → 업종별 매출 상위 10개 → 모델 성능 지표
#       - 생성 파일 : age_group_sales_bar_chart.png (스크립트와 같은 폴더에 저장)

# ─── DESCRIPTION ──────────────────────────────────────────────────────────────
# - **요구사항 출처:** 종합실습가이드_데이터분석을위한 Python이해(윤선영).pdf
# - [1] CSV에서 분석에 필요한 칼럼만 선택하여 DataFrame 생성
# - [2] 서비스_업종_코드_명별 당월_매출_금액 합계 → 내림차순 상위 10개 추출
# - [3] 연령대(10/20/30) 매출 칼럼별 합계 bar 그래프 작성 후 PNG 파일 저장
# - [4] 파이프라인 작성
#       1) 수치형: 결측치(중앙값 대체) + 표준화 스케일링
#       2) 범주형: 결측치('missing' 대체) + 원-핫 인코딩
#       3) 두 파이프라인을 ColumnTransformer 로 결합
#       4) 회귀 모델을 연결하여 최종 모델 파이프라인 완성
# - [5] 입력값(연령대 10/20/30 매출, 상권_구분_코드_명) → 결과값(당월_매출_금액)
#       베이스라인 선형회귀 모델 학습 및 성능(R², RMSE, MAE) 확인
#       ※ [추가 구현 사항] 강의안의 과제 5(파이프라인)와 6(모델 성능 확인)이
#          하나의 흐름이므로 모델 학습·성능 확인까지 포함하여 구현함
# ──────────────────────────────────────────────────────────────────────────────

import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # GUI 없는 환경(서버/CI)에서도 그래프 저장이 가능하도록 설정
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


# ==============================================================================
#  전역 상수 정의 (분석 조건이 바뀌면 이 영역만 수정하면 되도록 한곳에 모음)
# ==============================================================================

# --- 파일 경로 관련 ---
DEFAULT_CSV_FILE_NAME = "서울시 상권분석서비스(추정매출-상권).csv"
CHART_FILE_NAME = "age_group_sales_bar_chart.png"
CSV_ENCODING_CANDIDATES = ("cp949", "utf-8-sig")  # 서울시 공공데이터는 CP949가 기본

# --- [1] 사용할 칼럼 지정 ---
SELECTED_COLUMNS = [
    "상권_코드_명", "상권_구분_코드_명", "서비스_업종_코드", "서비스_업종_코드_명",
    "당월_매출_금액",
    "남성_매출_금액", "여성_매출_금액",
    "연령대_10_매출_금액", "연령대_20_매출_금액", "연령대_30_매출_금액",
]

# --- [2] 그룹 기준 / 집계 대상 칼럼 ---
SERVICE_TYPE_COLUMN = "서비스_업종_코드_명"
MONTHLY_SALES_COLUMN = "당월_매출_금액"
TOP_N = 10

# --- [3] 그래프 대상 칼럼 ---
AGE_SALES_COLUMNS = ["연령대_10_매출_금액", "연령대_20_매출_금액", "연령대_30_매출_금액"]
AGE_SALES_LABELS = ["10대", "20대", "30대"]
KRW_EOK = 100_000_000  # 1억 원 (그래프 축 단위 환산용)

# --- [4] 모델 입력값 / 결과값 및 학습 조건 ---
NUMERIC_FEATURES = ["연령대_10_매출_금액", "연령대_20_매출_금액", "연령대_30_매출_금액"]
CATEGORICAL_FEATURES = ["상권_구분_코드_명"]
TARGET_COLUMN = "당월_매출_금액"
TEST_SIZE = 0.2       # 학습 80% : 평가 20%
RANDOM_STATE = 42     # 재현 가능한 결과를 위한 시드 고정

# --- 콘솔 출력 형식 ---
SECTION_DIVIDER = "=" * 78


# ==============================================================================
#  공통 유틸리티 함수
# ==============================================================================

def print_section(title: str) -> None:
    """콘솔 출력에서 각 과제 단계를 구분하는 섹션 제목을 출력한다."""
    print(f"\n{SECTION_DIVIDER}\n {title}\n{SECTION_DIVIDER}")


def setup_korean_font() -> None:
    """실행 환경(OS)에 설치된 한글 폰트를 탐색하여 matplotlib에 적용한다.

    Windows(Malgun Gothic) → macOS(AppleGothic) → Linux(Nanum/Noto 계열) 순으로
    탐색하며, 한글 폰트가 없으면 경고만 출력하고 실행은 계속한다.
    """
    font_candidates = [
        "Malgun Gothic",        # Windows 기본
        "AppleGothic",          # macOS 기본
        "NanumGothic",          # Linux (나눔글꼴 설치 시)
        "Noto Sans CJK KR",     # Linux (Noto 글꼴 설치 시)
        "Noto Sans CJK JP",     # Noto CJK 통합 글꼴 (한글 글리프 포함)
    ]
    installed_fonts = {font.name for font in font_manager.fontManager.ttflist}

    for font_name in font_candidates:
        if font_name in installed_fonts:
            plt.rcParams["font.family"] = font_name
            break
    else:
        print("[경고] 한글 폰트를 찾지 못해 그래프의 한글이 깨질 수 있습니다.")

    plt.rcParams["axes.unicode_minus"] = False  # 마이너스 기호 깨짐 방지


def resolve_csv_path() -> Path:
    """분석 대상 CSV 경로를 결정한다.

    우선순위: (1) 명령행 인자로 받은 경로 → (2) 스크립트와 같은 폴더의 기본 파일명
    """
    if len(sys.argv) > 1:
        csv_path = Path(sys.argv[1])
    else:
        csv_path = Path(__file__).resolve().parent / DEFAULT_CSV_FILE_NAME

    if not csv_path.exists():
        raise FileNotFoundError(
            f"CSV 파일을 찾을 수 없습니다: {csv_path}\n"
            f"→ 데이터 파일을 스크립트와 같은 폴더에 두거나, "
            f"실행 시 경로를 인자로 지정해 주세요."
        )
    return csv_path


# ==============================================================================
#  [1] 사용할 칼럼 지정 및 DataFrame 생성
# ==============================================================================

def load_selected_columns(csv_path: Path) -> pd.DataFrame:
    """CSV에서 분석에 필요한 칼럼(SELECTED_COLUMNS)만 읽어 DataFrame으로 생성한다.

    - 원본 파일은 읽기 전용으로만 사용하며 어떤 경우에도 수정하지 않는다.
    - 공공데이터 특성상 CP949 인코딩을 우선 시도하고, 실패 시 UTF-8-SIG로 재시도한다.
    """
    for encoding in CSV_ENCODING_CANDIDATES:
        try:
            return pd.read_csv(csv_path, usecols=SELECTED_COLUMNS, encoding=encoding)
        except UnicodeDecodeError:
            continue

    raise ValueError(
        f"지원 인코딩 {CSV_ENCODING_CANDIDATES} 으로 파일을 읽을 수 없습니다: {csv_path}"
    )


# ==============================================================================
#  [2] 서비스_업종_코드_명별 당월_매출_금액 합계 → 내림차순 상위 10개
# ==============================================================================

def get_top_sales_by_service_type(df: pd.DataFrame) -> pd.Series:
    """서비스_업종_코드_명별로 당월_매출_금액 합계를 구하고,

    내림차순 정렬 후 상위 TOP_N(10)개 업종만 반환한다.
    """
    return (
        df.groupby(SERVICE_TYPE_COLUMN)[MONTHLY_SALES_COLUMN]
        .sum()
        .sort_values(ascending=False)
        .head(TOP_N)
    )


def print_top_sales(top_sales: pd.Series) -> None:
    """상위 업종별 매출 합계를 순위 형식으로 보기 좋게 출력한다."""
    for rank, (service_name, total_sales) in enumerate(top_sales.items(), start=1):
        print(f"  {rank:>2}위 | {service_name} | {total_sales:>24,} 원")


# ==============================================================================
#  [3] 연령대(10/20/30) 매출 칼럼별 합계 bar 그래프 작성 및 파일 저장
# ==============================================================================

def plot_age_group_sales(df: pd.DataFrame, output_path: Path) -> pd.Series:
    """연령대 3개 칼럼의 칼럼별 합계를 bar 그래프로 그리고 PNG 파일로 저장한다.

    금액 단위가 매우 크므로(조 단위) y축은 '억 원' 단위로 환산하여 표시한다.
    반환값: 원(KRW) 단위의 칼럼별 합계 Series (콘솔 출력용)
    """
    age_sales_sum = df[AGE_SALES_COLUMNS].sum()
    sums_in_eok = age_sales_sum / KRW_EOK

    fig, ax = plt.subplots(figsize=(9, 6))
    bars = ax.bar(AGE_SALES_LABELS, sums_in_eok, color=["#8ecae6", "#219ebc", "#023047"])

    # 각 막대 위에 합계 수치(억 원)를 표기하여 그래프만으로 값을 읽을 수 있게 한다
    ax.bar_label(bars, labels=[f"{value:,.0f}" for value in sums_in_eok], padding=3)

    ax.set_title("연령대별 매출 금액 합계 (10대 · 20대 · 30대)", fontsize=14, pad=12)
    ax.set_xlabel("연령대")
    ax.set_ylabel("매출 금액 합계 (억 원)")
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)  # 메모리 누수 방지를 위해 그린 Figure는 즉시 해제

    return age_sales_sum


# ==============================================================================
#  [4] 파이프라인 작성 (수치형 + 범주형 → 결합 → 최종 모델 파이프라인)
# ==============================================================================

def build_numeric_pipeline() -> Pipeline:
    """5-1) 수치형 파이프라인: 결측치를 중앙값(median)으로 대체 → 표준화 스케일링."""
    return Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])


def build_categorical_pipeline() -> Pipeline:
    """5-2) 범주형 파이프라인: 결측치를 'missing'으로 대체 → 원-핫 인코딩."""
    return Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])


def build_preprocessor() -> ColumnTransformer:
    """5-3) 수치형/범주형 두 파이프라인을 하나의 전처리기로 결합한다."""
    return ColumnTransformer(transformers=[
        ("numeric", build_numeric_pipeline(), NUMERIC_FEATURES),
        ("categorical", build_categorical_pipeline(), CATEGORICAL_FEATURES),
    ])


def build_model_pipeline() -> Pipeline:
    """5-4) 전처리기 + 회귀 모델을 연결하여 최종 모델 파이프라인을 완성한다.

    모델은 해석이 쉽고 학습이 빠른 선형회귀(LinearRegression)를
    베이스라인으로 채택한다.
    """
    return Pipeline(steps=[
        ("preprocessor", build_preprocessor()),
        ("regressor", LinearRegression()),
    ])


# ==============================================================================
#  [5] 모델 학습 및 성능 확인 (R², RMSE, MAE)
#  ※ [추가 구현] 5(파이프라인)와 과제 6(모델 성능 확인)이 하나의 흐름이므로
#     함께 구현함. 파이프라인이 실제로 동작하는지 검증하는 역할도 겸한다.
# ==============================================================================

def train_and_evaluate(df: pd.DataFrame) -> Pipeline:
    """입력값(연령대 매출 3종 + 상권 구분)으로 당월_매출_금액을 예측하는

    모델 파이프라인을 학습하고, 테스트 세트 성능 지표를 출력한다.

    [참고] 입력값인 연령대별 매출은 결과값(당월 매출)의 구성 요소이므로
    설명력(R²)이 높게 나오는 것이 자연스러운 과제 설계이다.
    """
    features = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    target = df[TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        features, target, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )

    model_pipeline = build_model_pipeline()
    model_pipeline.fit(X_train, y_train)
    predictions = model_pipeline.predict(X_test)

    r2 = r2_score(y_test, predictions)
    rmse = math.sqrt(mean_squared_error(y_test, predictions))  # 구버전 sklearn 호환
    mae = mean_absolute_error(y_test, predictions)

    print(f"  - 학습/평가 데이터 : {len(X_train):,}행 / {len(X_test):,}행")
    print(f"  - R²   (설명력, 1에 가까울수록 좋음) : {r2:.4f}")
    print(f"  - RMSE (평균 제곱근 오차)            : {rmse:>20,.0f} 원")
    print(f"  - MAE  (평균 절대 오차)              : {mae:>20,.0f} 원")

    return model_pipeline


# ==============================================================================
#  메인 실행 흐름 (1 → 2 → 3 → 4·5 순서로 진행)
# ==============================================================================

def main() -> None:
    """전체 과제를 순서대로 실행하는 엔트리 포인트."""
    setup_korean_font()
    csv_path = resolve_csv_path()
    chart_path = Path(__file__).resolve().parent / CHART_FILE_NAME

    # --- [1] 필요한 칼럼만 DataFrame으로 생성 --------------------------------
    print_section("[1] 사용할 칼럼 지정 및 DataFrame 생성")
    df = load_selected_columns(csv_path)
    print(f"  - 로드 파일   : {csv_path.name}")
    print(f"  - 데이터 크기 : {df.shape[0]:,}행 × {df.shape[1]}열 (지정 칼럼만 로드)")

    # --- [2] 업종별 매출 합계 상위 10개 -------------------------------------
    print_section(f"[2] {SERVICE_TYPE_COLUMN}별 매출 합계 상위 {TOP_N}개 (내림차순)")
    top_sales = get_top_sales_by_service_type(df)
    print_top_sales(top_sales)

    # --- [3] 연령대별 매출 합계 bar 그래프 저장 ------------------------------
    print_section("[3] 연령대(10/20/30) 매출 합계 bar 그래프 저장")
    age_sales_sum = plot_age_group_sales(df, chart_path)
    for column_name, total in age_sales_sum.items():
        print(f"  - {column_name} 합계 : {total:>24,} 원")
    print(f"  - 그래프 저장 완료 : {chart_path}")

    # --- [4·5] 파이프라인 구축 → 모델 학습 및 성능 확인 ----------------------
    print_section("[4·5] 전처리 파이프라인 + 베이스라인 모델 학습 및 성능 확인")
    train_and_evaluate(df)

    print(f"\n{SECTION_DIVIDER}\n 모든 과제 수행이 완료되었습니다.\n{SECTION_DIVIDER}")


if __name__ == "__main__":
    main()
