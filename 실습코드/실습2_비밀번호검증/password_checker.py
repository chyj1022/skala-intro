#
# 교육 환경 설정 및 간단한 파이썬 연습 코드
# [실습2] echo 프로그램으로 비밀번호 검증하기
# - 비밀번호 검증은 별도의 함수를 통해 구현
# - 조건: 최소 하나의 영문 소문자, 영문 대문자, 숫자 및 기호가 포함되어야 함
# - !quit을 입력하면 프로그램 종료
#
# 작성일 : 2026-07-06
# 작성자 : 백정열, SKALA
#
# 변경일 : 
#
# All Rights Reserved by SK AX, SKALA
#

import re


def is_valid_password(password: str) -> bool:
    """비밀번호가 조건(소문자, 대문자, 숫자, 기호 각 1개 이상 포함)을 만족하는지 검사"""
    pattern = re.compile(
        r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};:\'",.<>/?\\|`~]).+$'
    )
    return bool(pattern.match(password))


def main():
    while True:
        password = input("비밀번호를 입력하세요 (!quit 입력 시 종료): ")

        if password == "!quit":
            print("프로그램을 종료합니다. 안녕히 가세요!")
            break

        if is_valid_password(password):
            print("사용 가능한 비밀번호입니다.")
        else:
            print("비밀번호는 영문 소문자, 대문자, 숫자, 기호를 각각 최소 1개 이상 포함해야 합니다.")


if __name__ == "__main__":
    main()
