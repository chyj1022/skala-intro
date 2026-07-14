print("--- 무한 메아리 프로그램 (종료하려면 !quit 입력) ---")

# 무한히 반복하기 위해 while True를 사용합니다.
while True:
    # 1. 사용자로부터 문장을 입력받습니다.
    user_input = input("문장을 입력하세요: ")
    
    # 2. 만약(if) 사용자가 입력한 글자가 '!quit'이라면?
    if user_input == "!quit":
        print("프로그램을 종료합니다. 다음에 또 만나요!")
        break  # 반복문(while)을 즉시 탈출(종료)합니다.
        
    # 3. '!quit'이 아니라면 입력받은 문장을 그대로 출력합니다.
    print(f"출력된 문장: {user_input}")
    print("-" * 30) # 줄바꿈선으로 깔끔하게 구분