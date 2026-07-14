#
# 교육 환경 설정 및 간단한 파이썬 연습 코드
# [실습1] Echo 프로그램 (2/2) - 개선 버전
# 사용자가 문장을 반복적으로 입력할 수 있고, !quit 입력 시 프로그램 종료
#
# 작성일 : 2026-07-06
# 작성자 : 백정열, SKALA
#
# 변경일 : 
#
# All Rights Reserved by SK AX, SKALA
#

while True:
    sentence = input("문장을 입력하세요 (!quit 입력 시 종료): ")

    if sentence == "!quit":
        print("프로그램을 종료합니다. 안녕히 가세요!")
        break

    print("입력하신 문장은:", sentence)
