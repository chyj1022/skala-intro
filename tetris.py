import pygame
import random

# 초기화
pygame.init()

# 상수의 정의
BLOCK_SIZE = 30
GRID_COLS = 10
GRID_ROWS = 20

# 레이아웃 설정 (왼쪽에 170px 크기의 사이드바 추가)
GRID_OFFSET_X = 170 
SCREEN_WIDTH = GRID_OFFSET_X + GRID_COLS * BLOCK_SIZE + 30 # 총 500px 너비
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

# 테트리미노 모양 정의
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
        self.shape = [list(row) for row in zip(*self.shape[::-1])]

def create_grid(locked_pos):
    grid = [[BLACK for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
    for (x, y), color in locked_pos.items():
        if y >= 0:
            grid[y][x] = color
    return grid

def valid_space(piece, grid):
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
    cleared = 0
    for r in range(GRID_ROWS - 1, -1, -1):
        if BLACK not in grid[r]:
            cleared += 1
            for c in range(GRID_COLS):
                if (c, r) in locked_pos:
                    del locked_pos[(c, r)]
            
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
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            pygame.draw.rect(surface, grid[r][c], (GRID_OFFSET_X + c * BLOCK_SIZE, r * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 0)
            pygame.draw.rect(surface, GRAY, (GRID_OFFSET_X + c * BLOCK_SIZE, r * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 1)

def draw_next_piece(surface, piece):
    font = pygame.font.SysFont('malgungothic', 18, bold=True)
    label = font.render("NEXT BLOCK", True, WHITE)
    label_rect = label.get_rect(center=(GRID_OFFSET_X // 2, 40))
    surface.blit(label, label_rect)
    
    shape_width = len(piece.shape[0])
    shape_height = len(piece.shape)
    
    start_x = (GRID_OFFSET_X // 2) - (shape_width * BLOCK_SIZE) // 2
    start_y = 110 - (shape_height * BLOCK_SIZE) // 2
    
    for r, row in enumerate(piece.shape):
        for c, val in enumerate(row):
            if val:
                pygame.draw.rect(surface, piece.color, (start_x + c * BLOCK_SIZE, start_y + r * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 0)
                pygame.draw.rect(surface, GRAY, (start_x + c * BLOCK_SIZE, start_y + r * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 1)

def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("파이썬 테트리스 게임")
    clock = pygame.time.Clock()

    locked_positions = {}
    grid = create_grid(locked_positions)

    current_piece = Piece(3, 0, random.choice(SHAPES))
    next_piece = Piece(3, 0, random.choice(SHAPES))
    
    fall_time = 0
    fall_speed = 500
    score = 0
    running = True

    while running:
        grid = create_grid(locked_positions)
        fall_time += clock.get_rawtime()
        clock.tick()

        if fall_time >= fall_speed:
            fall_time = 0
            current_piece.y += 1
            if not valid_space(current_piece, grid):
                current_piece.y -= 1
                for r, row in enumerate(current_piece.shape):
                    for c, val in enumerate(row):
                        if val:
                            locked_positions[(current_piece.x + c, current_piece.y + r)] = current_piece.color
                
                current_piece = next_piece
                next_piece = Piece(3, 0, random.choice(SHAPES))
                score += clear_rows(grid, locked_positions) * 100
                
                for (x, y) in locked_positions:
                    if y < 0:
                        running = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    current_piece.x -= 1
                    if not valid_space(current_piece, grid):
                        current_piece.x += 1
                        
                elif event.key == pygame.K_RIGHTNormally I can help with things like this, but I don't seem to have access to that content. You can try again or ask me for something else.