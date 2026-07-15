"""
종합실습 1: 비동기 날씨 데이터 수집 및 저장 프로그램 (asyncio + httpx)
=====================================================================

[프로그램 개요]
공공 API 2종에서 실제 데이터를 비동기(asyncio + httpx)로 수집하고,
Pydantic 스키마(Weather)로 검증한 뒤 CSV / Parquet 파일로 저장·조회한다.
파일 하단에는 pytest 테스트 함수 3개가 함께 들어 있다.

[데이터 출처 (모두 실제 데이터, JSON 응답)]
1. Open-Meteo : 위도/경도 기반 현재 기온
   https://api.open-meteo.com/v1/forecast
2. TimeAPI    : 타임존 기반 현지 시각
   https://timeapi.io/api/time/current/zone

[처리 흐름]
1) 도시 4곳(서울/도쿄/뉴욕/런던)의 기온·현지시각을 동시에(병렬) 요청
2) Weather(Pydantic) 객체로 검증
3) CSV 저장 후 전체 컬럼 읽기        (파일 없으면 FileNotFoundError)
4) Parquet 저장 후 도시·기온만 읽기  (파일 없으면 FileNotFoundError)
5) pytest로 무결성/예외/실시간 기온 검사

[예외 처리 방침]
- API 호출 실패(타임아웃, HTTP 오류, JSON 파싱 오류) 시 해당 값은
  결측치 "N/A" 로 기록하고 프로그램은 중단 없이 계속 진행한다.
- 파일이 없으면 읽기 함수가 FileNotFoundError 를 발생시키고,
  호출부(main)에서 잡아 안내 메시지를 출력한다.

[실행 방법]
※ 아래 명령들은 반드시 이 .py 파일이 있는 폴더 안에서 실행해야 합니다.
   (터미널에서 cd 명령으로 이 파일이 있는 폴더까지 이동한 뒤 실행하세요)
1) 가상환경 생성 및 활성화
   python3 -m venv venv
   source venv/bin/activate

2) 라이브러리 설치
   pip install httpx pydantic pandas pyarrow pytest ruff

3) 프로그램 실행
   python 울산_3반_최유정_day1종합실습.py

4) 테스트 실행
   pytest 울산_3반_최유정_day1종합실습.py -v

5) 코드 정리
   ruff check . && ruff format .
"""

import asyncio
from datetime import datetime
from pathlib import Path

import httpx
import pandas as pd
import pytest
from pydantic import BaseModel

# ---------------------------------------------------------------- 상수 정의
WEATHER_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude={lat}&longitude={lon}&current_weather=true"
)
TIME_URL = "https://timeapi.io/api/time/current/zone?timeZone={tz}"

# 터미널이 어느 폴더에 서 있든, 데이터 파일은 항상 이 .py 파일 옆에 생성한다.
# __file__ = 이 파이썬 파일 자신의 경로, .parent = 그 파일이 담긴 폴더
BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "weather.csv"
PARQUET_PATH = BASE_DIR / "weather.parquet"
TIMEOUT = 10.0  # 요청당 최대 10초 대기
MISSING = "N/A"  # API 실패 시 사용할 결측치 표기

CITIES = [
    {"name": "서울", "lat": 37.5665, "lon": 126.9780, "tz": "Asia/Seoul"},
    {"name": "도쿄", "lat": 35.6762, "lon": 139.6503, "tz": "Asia/Tokyo"},
    {"name": "뉴욕", "lat": 40.7128, "lon": -74.0060, "tz": "America/New_York"},
    {"name": "런던", "lat": 51.5074, "lon": -0.1278, "tz": "Europe/London"},
]


# ------------------------------------------------- 2. Pydantic 스키마 정의
class Weather(BaseModel):
    """도시별 날씨 정보를 담는 스키마.

    기온은 정상 수집 시 float, API 실패 시 "N/A"(str)가 들어갈 수 있어
    float | str 로 선언한다. 현지시각은 "MM/DD/YYYY HH:MM" 형식 문자열.
    """

    도시: str
    기온: float | str
    현지시각: str


# --------------------------------------------- 1. 비동기 데이터 수집 함수들
async def fetch_json(client: httpx.AsyncClient, url: str) -> dict | None:
    """URL에 GET 요청을 보내 JSON(dict)을 반환한다. 실패 시 None 반환.

    타임아웃, HTTP 4xx/5xx, 잘못된 JSON 응답을 모두 여기서 처리하여
    호출부가 예외 걱정 없이 결과만 확인하도록 한다.
    """
    try:
        resp = await client.get(url)
        resp.raise_for_status()  # 4xx/5xx 응답이면 예외 발생
        return resp.json()  # httpx의 .json()은 await가 필요 없다
    except (httpx.HTTPError, ValueError) as e:
        # httpx.HTTPError: 타임아웃/연결 실패/상태코드 오류를 모두 포함하는 부모 예외
        # ValueError    : 응답 본문이 올바른 JSON이 아닐 때 (JSONDecodeError)
        print(f"[경고] 요청 실패: {url} ({type(e).__name__}: {e})")
        return None


def format_local_time(iso_datetime: str) -> str:
    """TimeAPI의 ISO 문자열을 'MM/DD/YYYY HH:MM' 형식으로 변환한다.

    예: "2026-07-10T16:46:32.1234567" -> "07/10/2026 16:46"
    분 단위까지만 필요하므로 앞 16자만 파싱한다.
    (소수점 자릿수가 파이썬 버전별로 파싱 오류를 내는 문제 회피)
    """
    parsed = datetime.strptime(iso_datetime[:16], "%Y-%m-%dT%H:%M")
    return parsed.strftime("%m/%d/%Y %H:%M")


async def fetch_city_weather(client: httpx.AsyncClient, city: dict) -> Weather:
    """한 도시의 기온과 현지시각을 '동시에' 요청해 Weather 객체로 만든다."""
    weather_data, time_data = await asyncio.gather(
        fetch_json(client, WEATHER_URL.format(lat=city["lat"], lon=city["lon"])),
        fetch_json(client, TIME_URL.format(tz=city["tz"])),
    )

    # 응답이 None이거나(요청 실패) JSON 구조가 예상과 다르면 "N/A" 처리
    try:
        기온: float | str = weather_data["current_weather"]["temperature"]
    except (TypeError, KeyError):
        기온 = MISSING
    try:
        현지시각 = format_local_time(time_data["dateTime"])
    except (TypeError, KeyError, ValueError):
        현지시각 = MISSING

    return Weather(도시=city["name"], 기온=기온, 현지시각=현지시각)


async def collect_weather(cities: list[dict]) -> list[Weather]:
    """모든 도시의 날씨를 비동기로 병렬 수집한다.

    도시 4곳 × API 2종 = 총 8개의 요청이 순차가 아닌 동시에 실행된다.
    httpx는 기본적으로 리다이렉트를 따라가지 않으므로 옵션으로 켜 준다.
    """
    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
        tasks = (fetch_city_weather(client, city) for city in cities)
        return await asyncio.gather(*tasks)


# ------------------------------------------------- 3. CSV 저장 / 읽기
def to_dataframe(weathers: list[Weather]) -> pd.DataFrame:
    """Weather 객체 리스트를 DataFrame으로 변환한다. (CSV/Parquet 공용)"""
    return pd.DataFrame([w.model_dump() for w in weathers])


def save_csv(weathers: list[Weather], path: Path = CSV_PATH) -> None:
    """Weather 객체 리스트를 CSV 파일로 저장한다."""
    to_dataframe(weathers).to_csv(path, index=False, encoding="utf-8-sig")
    print(f"[저장 완료] CSV -> {path}")


def load_csv(path: Path = CSV_PATH) -> pd.DataFrame:
    """CSV 파일을 읽어 DataFrame으로 반환한다.

    파일이 없으면 FileNotFoundError 를 발생시킨다.
    """
    if not path.exists():
        raise FileNotFoundError(f"CSV 파일이 존재하지 않습니다: {path}")
    return pd.read_csv(path, encoding="utf-8-sig")


# ------------------------------------------------- 4. Parquet 저장 / 읽기
def save_parquet(weathers: list[Weather], path: Path = PARQUET_PATH) -> None:
    """Weather 객체 리스트를 Parquet 파일로 저장한다.

    Parquet은 컬럼당 단일 타입만 허용하므로 '기온'에 float와 "N/A"(str)가
    섞여 있으면 저장이 실패한다. 이를 막기 위해 숫자로 변환하고
    "N/A"는 결측치(NaN)로 저장한다. (errors="coerce")
    """
    df = to_dataframe(weathers)
    df["기온"] = pd.to_numeric(df["기온"], errors="coerce")
    df.to_parquet(path, index=False)
    print(f"[저장 완료] Parquet -> {path}")


def load_parquet(
    columns: list[str] | None = None, path: Path = PARQUET_PATH
) -> pd.DataFrame:
    """Parquet 파일에서 지정한 컬럼만 읽어 DataFrame으로 반환한다.

    columns=None 이면 전체 컬럼을 읽고, 파일이 없으면 FileNotFoundError.
    """
    if not path.exists():
        raise FileNotFoundError(f"Parquet 파일이 존재하지 않습니다: {path}")
    return pd.read_parquet(path, columns=columns)


# ---------------------------------------------------------------- 진입점
def main() -> None:
    """수집 -> CSV -> Parquet -> 파일 없음 예외 처리 순서로 시연한다."""
    # 1. 공공 API에서 비동기 데이터 수집
    weathers = asyncio.run(collect_weather(CITIES))

    # 3. CSV 저장 후 전체 읽기
    save_csv(weathers)
    print("\n[CSV 전체 읽기]")
    print(load_csv())

    # 4. Parquet 저장 후 '도시', '기온' 컬럼만 읽기
    save_parquet(weathers)
    print("\n[Parquet에서 도시, 기온만 읽기]")
    print(load_parquet(columns=["도시", "기온"]))

    # 파일이 없을 때 예외 처리가 동작하는지 확인
    try:
        load_csv(Path("존재하지_않는_파일.csv"))
    except FileNotFoundError as e:
        print(f"\n[예외 처리 확인] {e}")


# ================================================= 5. pytest 테스트
# 실행: pytest main.py -v   (테스트 함수가 이 파일 안에 있으므로 파일명 지정)
#
# [pytest 동작 원리 요약]
# - pytest는 test_ 로 시작하는 함수를 자동으로 찾아 하나씩 실행한다.
# - assert 문이 True면 PASSED, False면 FAILED로 표시되며,
#   assert 뒤에 적은 메시지가 실패 사유(Fail 메시지)로 출력된다.
# - tmp_path 는 pytest가 제공하는 임시 폴더 fixture로, 테스트마다
#   새 폴더가 생성되어 실제 데이터 파일(weather.parquet)을 건드리지 않는다.


def test_parquet_roundtrip(tmp_path: Path) -> None:
    """Parquet에 저장했다가 다시 읽어도 데이터가 손상되지 않는지 확인."""
    path = tmp_path / "sample.parquet"
    sample = [Weather(도시="서울", 기온=25.0, 현지시각="07/10/2026 16:46")]

    save_parquet(sample, path)
    df = load_parquet(columns=["도시", "기온"], path=path)

    assert df.loc[0, "도시"] == "서울", "Fail: 도시 값이 왜곡되었습니다."
    assert df.loc[0, "기온"] == 25.0, "Fail: 기온 값이 왜곡되었습니다."


def test_load_csv_missing_file() -> None:
    """존재하지 않는 파일을 읽으면 FileNotFoundError가 발생해야 한다."""
    with pytest.raises(FileNotFoundError):
        load_csv(Path("이런_파일은_없음.csv"))


def test_live_temperature_matches_saved() -> None:
    """서울의 실시간 기온과 Parquet에 저장된 기온의 정수 부분을 비교한다.

    실제 기온은 시시각각 변하고 부동소수점 오차도 있으므로,
    '정확히 같음' 대신 정수 부분이 같으면 동일한 값으로 판정한다.
    (예: 저장 25.7 vs 실시간 25.3 -> 둘 다 25 -> Pass)
    """
    if not PARQUET_PATH.exists():
        pytest.skip("weather.parquet 없음. 먼저 `python main.py` 를 실행하세요.")

    # 1) 위도/경도로 실시간 기온을 새로 수집
    live = asyncio.run(collect_weather([CITIES[0]]))[0]
    assert isinstance(live.기온, float), "Fail: 실시간 기온 수집 실패(N/A)."

    # 2) Parquet에서 서울의 저장된 기온 읽기
    df = load_parquet(columns=["도시", "기온"])
    saved = df.loc[df["도시"] == CITIES[0]["name"], "기온"].iloc[0]
    assert pd.notna(saved), "Fail: 저장된 기온이 결측치(N/A)입니다."

    # 3) 정수 부분 비교
    assert int(live.기온) == int(saved), (
        f"Fail: 서울의 실시간 기온 {live.기온}°C 와 "
        f"저장된 기온 {saved}°C 의 정수 부분이 다릅니다."
    )


if __name__ == "__main__":
    main()
