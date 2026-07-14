# ───────────────────────────────────────────────────────────────
# SKALA 과정 소개 - Git 활용
# Created 2026-07-08
# 
# Git 연동을 위한 실습 파이썬 코드
# 
# modified 2026-06-23 : 모델 수정 및 모바일 앱에서 동작되도록 변경
# ───────────────────────────────────────────────────────────────
# Git 활용 - 교육환경 - 파이썬 기본 실습 (AI 코딩 맛보기) PPT에 대응하는 실습 코드입니다.

## 폴더 구성 - 수강생 개인별 폴더 위치에 자유롭게 실행

## 사전 실행 - 환경설정 쉘 스크립트 실행 후 진행 필수!

### 실습1_Echo프로그램
- `echo.py` : 사용자가 입력하는 문장을 그대로 출력 (1/2, 기본 버전)
- `echo_v2.py` : 반복 입력 + `!quit` 입력 시 종료 기능 추가 (2/2, 개선 버전)

### 실습2_비밀번호검증
- `password_validator.py` : 정규 표현식으로 비밀번호 조건(소문자/대문자/숫자/기호 각 1개 이상) 검증 (기본 버전)
- `password_checker.py` : 검증 로직을 별도 함수로 분리하고, echo 프로그램처럼 반복 입력 + `!quit` 종료 기능 추가 (확장 버전)

### 실습3_Mermaid다이어그램
- `README.md` : Mermaid 다이어그램 개념 및 차트 종류 비교표
- `flowchart_example.mmd` : 파이썬 코드 문제 해결 과정을 표현한 순서도 예제 (https://mermaid.live/edit 에 붙여넣어 확인 가능)

## 실행 방법

```bash
python3 echo.py
python3 echo_v2.py
python3 password_validator.py
python3 password_checker.py
```

각 프로그램은 터미널에서 위와 같이 실행하며, `!quit` 을 입력하면 반복 실행되는
프로그램(echo_v2.py, password_checker.py)을 종료할 수 있습니다.
