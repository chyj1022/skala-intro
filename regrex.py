import re

def is_valid_password(password):
    # 정규 표현식: 대문자, 소문자, 숫자, 특수문자(@$!%*?&#) 각각 최소 1개 이상, 최소 8자 이상
    pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#])[A-Za-z\d@$!%*?&#]{8,}$"
    return bool(re.match(pattern, password))

# 올바른 비밀번호를 입력할 때까지 무한 반복
while True:
    user_password = input("설정할 비밀번호를 입력하세요: ")
    
    if is_valid_password(user_password):
        print("정상적인 비밀번호입니다. 설정이 완료되었습니다!")
        break  # 조건을 만족하면 반복문 탈출
    else:
        print("비밀번호 조건에 맞지 않습니다. 다시 시도해주세요.")
        print("([조건] 영문 대문자, 소문자, 숫자, 특수문자 각 1개 이상 포함, 최소 8자 이상)\n")