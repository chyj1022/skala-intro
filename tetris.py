import pygame
import random

# 초기화
pygame.init()
   
# 상수의 정의
BLOCK_SIZE = 30
GRID_COLS = 10
GRID_ROWS = 20
SCREEN_WIDTH = GRID_COLS * BLOCK_SIZE + 200 # 스코어 표시용 여백 추가
SCREEN_HEIGHT = GRID_ROWS * BLOCK_SIZE

# 색상 정의 (RGB)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (40, 40, 40)
COLORS = [
    (0, 255, 255),  # 하늘색 (I)
    (255, 255, 0),  # 노란색 (O)
    (128, 0, 128),  # 보라색 (T)
    (0, 255, 0),    # 녹색 (S)
    (255, 0, 0),    # 빨간색 (Z)
    (0, 0, 255),    # 파란색 (J)
    (255, 165, 0)   # 주황색 (L)
]

# 테트리미노 모양 정의 (모양별 2D 리스트 형태)
SHAPES = [
    [[1, 1, 1, 1]], # I
    [[1, 1], [1, 1]], # O
    [[0, 1, 0], [1, 1, 1]], # T
    [[0, 1, 1], [1, 1, 0]], # S
    [[1, 1, 0], [0, 1, 1]], # Z
    [[1, 0, 0], [1, 1, 1]], # J
    [[0, 0, 1], [1, 1, 1]]  # L
]

class Piece:
    def __init__(self, x, y, shape):
        self.x = x
        self.y = y
        self.shape = shape
        self.color = COLORS[SHAPES.index(shape)]

    def rotate(self):
        # 2D 리스트 시계방향 회전 (행과 열을 바꾸고 뒤집기)
        self.shape = [list(row) for row in zip(*self.shape[::-1])]

def create_grid(locked_pos):
    # 20x10의 빈 그리드 생성 (검은색으로 채움)
    grid = [[BLACK for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
    for (x, y), color in locked_pos.items():
        if y >= 0:
            grid[y][x] = color
    return grid

def valid_space(piece, grid):
    # 블록이 그리드 안 공간에 유효하게 위치하는지 확인 (벽 충돌 및 쌓인 블록 충돌 체크)
    for r, row in enumerate(piece.shape):
        for c, val in enumerate(row):
            if val:
                next_x = piece.x + c
                next_y = piece.y + r
                if next_x < 0 or next_x >= GRID_COLS or next_y >= GRID_ROWS:
                    return False
                if next_y >= 0 and grid[next_y][next_x] != BLACK:
                    return False
    return True

def clear_rows(grid, locked_pos):
    # 채워진 행을 지우고 위의 블록들을 아래로 내림
    cleared = 0
    for r in range(GRID_ROWS - 1, -1, -1):
        if BLACK not in grid[r]: # 행에 검은색이 없다면 = 꽉 찼다면
            cleared += 1
            # 고정된 좌표 목록에서 해당 행을 삭제하고 위쪽 블록들의 y값을 1씩 증가시킴
            for c in range(GRID_COLS):
                if (c, r) in locked_pos:
                    del locked_pos[(c, r)]
            
            # 위에 있던 블록들을 한 칸씩 내리기 위해 딕셔너리 재구성
            new_locked = {}
            for (x, y), color in locked_pos.items():
                if y < r:
                    new_locked[(x, y + 1)] = color
                else:
                    new_locked[(x, y)] = color
            locked_pos.clear()
            locked_pos.update(new_locked)
            
    return cleared

def draw_grid(surface, grid):
    # 격자선 그리기
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            pygame.draw.rect(surface, grid[r][c], (c * BLOCK_SIZE, r * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 0)
            pygame.draw.rect(surface, GRAY, (c * BLOCK_SIZE, r * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 1)

def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("파이썬 테트리스 게임")
    clock = pygame.time.Clock()

    locked_positions = {}
    grid = create_grid(locked_positions)

    current_piece = Piece(3, 0, random.choice(SHAPES))
    next_piece = Piece(3, 0, random.choice(SHAPES))
    
    fall_time = 0
    fall_speed = 500 # 블록이 떨어지는 속도 (밀리초 단위)
    score = 0
    running = True

    while running:
        grid = create_grid(locked_positions)
        fall_time += clock.get_rawtime()
        clock.tick()

        # 자동으로 블록 떨어뜨리기
        if fall_time >= fall_speed:
            fall_time = 0
            current_piece.y += 1
            if not valid_space(current_piece, grid):
                current_piece.y -= 1
                # 블록 바닥 고정
                for r, row in enumerate(current_piece.shape):
                    for c, val in enumerate(row):
                        if val:
                            locked_positions[(current_piece.x + c, current_piece.y + r)] = current_piece.color
                current_piece = next_piece
                next_piece = Piece(3, 0, random.choice(SHAPES))
                
                # 라인 삭제 및 스코어 계산
                score += clear_rows(grid, locked_positions) * 100
                
                # 게임 오버 조건 체크 (블록이 화면 최상단 위로 쌓였을 때)
                for (x, y) in locked_positions:
                    if y < 0:
                        running = False

        # 키보드 이벤트 처리
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT: # 좌측 이동
                    current_piece.x -= 1
                    if not valid_space(current_piece, grid):
                        current_piece.x += 1
                        
                elif event.key == pygame.K_RIGHT: # 우측 이동
                    current_piece.x += 1
                    if not valid_space(current_piece, grid):
                        current_piece.x -= 1
                        
                elif event.key == pygame.K_DOWN: # 소프트 드롭 (아래로 빠르게 이동)
                    current_piece.y += 1
                    if not valid_space(current_piece, grid):
                        current_piece.y -= 1
                        
                elif event.key == pygame.K_UP: # 시계 방향 회전
                    old_shape = current_piece.shape
                    current_piece.rotate()
                    if not valid_space(current_piece, grid):
                        current_piece.shape = old_shape # 벽에 부딪히면 회전 취소
                        
                elif event.key == pygame.K_SPACE: # 하드 드롭 (바닥으로 즉시 떨어짐)
                    while valid_space(current_piece, grid):
                        current_piece.y += 1
                    current_piece.y -= 1
                    
                    # 하드 드롭 즉시 고정
                    for r, row in enumerate(current_piece.shape):
                        for c, val in enumerate(row):
                            if val:
                                locked_positions[(current_piece.x + c, current_piece.y + r)] = current_piece.color
                    current_piece = next_piece
                    next_piece = Piece(3, 0, random.choice(SHAPES))
                    score += clear_rows(grid, locked_positions) * 100

        # 현재 조종 중인 블록 그리드에 반영하여 그리기
        for r, row in enumerate(current_piece.shape):
            for c, val in enumerate(row):
                if val:
                    if current_piece.y + r >= 0:
                        grid[current_piece.y + r][current_piece.x + c] = current_piece.color

        # 화면 렌더링
        screen.fill(BLACK)
        draw_grid(screen, grid)

        # 스코어 및 텍스트 UI 표시
        font = pygame.font.SysFont('malgungothic', 25) # 윈도우 기본 맑은고딕 폰트 사용
        score_text = font.render(f"SCORE: {score}", True, WHITE)
        info_text1 = font.render("UP: Rotate", True, WHITE)
        info_text2 = font.render("SPACE: Drop", True, WHITE)
        
        screen.blit(score_text, (GRID_COLS * BLOCK_SIZE + 20, 50))
        screen.blit(info_text1, (GRID_COLS * BLOCK_SIZE + 20, 150))
        screen.blit(info_text2, (GRID_COLS * BLOCK_SIZE + 20, 190))

        pygame.display.update()

    pygame.quit()

if __name__ == '__main__':
    main()
