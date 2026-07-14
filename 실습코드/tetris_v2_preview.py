#
# 교육 환경 설정 및 간단한 파이썬 연습 코드
# 기능 : 개선된 테트리스 #1 — 다음 블록 미리보기 (브랜치: feature/preview → develop)
#
# 작성일 : 2026-07-06
# 작성자 : 백정열, SKALA
#
# 변경일 : 2026-07-06
# 변경 내용 : 추가 기능 확대 - 화면 왼쪽 상단에 다음에 떨어질 블록 미리보기
#
# All Rights Reserved by SK AX, SKALA
#


import pygame
import random

# ─────────────────────────────────────────────
# 상수 설정
# ─────────────────────────────────────────────
BOARD_WIDTH  = 300   # 게임 보드 (10 * 30)
BOARD_HEIGHT = 600
SIDE_WIDTH   = 150   # 사이드 패널
SCREEN_WIDTH = BOARD_WIDTH + SIDE_WIDTH
SCREEN_HEIGHT = BOARD_HEIGHT
BLOCK_SIZE = 30
COLS = 10
ROWS = 20

BLACK  = (0, 0, 0)
WHITE  = (255, 255, 255)
GRAY   = (50, 50, 50)
LIGHT_GRAY = (180, 180, 180)

COLORS = [
    (0, 240, 240),
    (0, 0, 240),
    (240, 160, 0),
    (240, 240, 0),
    (0, 240, 0),
    (160, 0, 240),
    (240, 0, 0),
]

SHAPES = [
    [[1,1,1,1]],
    [[1,0,0],[1,1,1]],
    [[0,0,1],[1,1,1]],
    [[1,1],[1,1]],
    [[0,1,1],[1,1,0]],
    [[0,1,0],[1,1,1]],
    [[1,1,0],[0,1,1]],
]


class Tetromino:
    def __init__(self, index=None):
        self.index = index if index is not None else random.randint(0, len(SHAPES) - 1)
        self.shape = [row[:] for row in SHAPES[self.index]]
        self.color = COLORS[self.index]
        self.x = COLS // 2 - len(self.shape[0]) // 2
        self.y = 0


class Board:
    def __init__(self):
        self.grid = [[None] * COLS for _ in range(ROWS)]

    def is_valid(self, piece, dx=0, dy=0, shape=None):
        s = shape if shape else piece.shape
        for r, row in enumerate(s):
            for c, cell in enumerate(row):
                if cell:
                    nx, ny = piece.x + c + dx, piece.y + r + dy
                    if nx < 0 or nx >= COLS or ny >= ROWS:
                        return False
                    if ny >= 0 and self.grid[ny][nx]:
                        return False
        return True

    def lock(self, piece):
        for r, row in enumerate(piece.shape):
            for c, cell in enumerate(row):
                if cell:
                    self.grid[piece.y + r][piece.x + c] = piece.color

    def clear_lines(self):
        full = [r for r in range(ROWS) if all(self.grid[r])]
        for r in full:
            del self.grid[r]
            self.grid.insert(0, [None] * COLS)
        return len(full)

    def draw(self, surface):
        for r in range(ROWS):
            for c in range(COLS):
                color = self.grid[r][c]
                rect = pygame.Rect(c * BLOCK_SIZE, r * BLOCK_SIZE, BLOCK_SIZE - 1, BLOCK_SIZE - 1)
                if color:
                    pygame.draw.rect(surface, color, rect)
                else:
                    pygame.draw.rect(surface, GRAY, rect, 1)


def draw_piece(surface, piece):
    for r, row in enumerate(piece.shape):
        for c, cell in enumerate(row):
            if cell:
                rect = pygame.Rect(
                    (piece.x + c) * BLOCK_SIZE,
                    (piece.y + r) * BLOCK_SIZE,
                    BLOCK_SIZE - 1, BLOCK_SIZE - 1
                )
                pygame.draw.rect(surface, piece.color, rect)


# ─────────────────────────────────────────────
# [추가] 다음 블록 미리보기 그리기
# ─────────────────────────────────────────────
def draw_next_piece(surface, next_piece, font):
    """사이드 패널 상단에 다음 블록 그리기"""
    panel_x = BOARD_WIDTH + 10
    panel_y = 10

    # "NEXT" 라벨
    label = font.render("NEXT", True, WHITE)
    surface.blit(label, (panel_x + 20, panel_y))

    # 미리보기 박스 배경
    preview_size = BLOCK_SIZE * 4
    box_rect = pygame.Rect(panel_x, panel_y + 30, preview_size + 10, preview_size + 10)
    pygame.draw.rect(surface, GRAY, box_rect, 1)

    # 블록 그리기 (박스 중앙 정렬)
    shape = next_piece.shape
    shape_w = len(shape[0]) * BLOCK_SIZE
    shape_h = len(shape) * BLOCK_SIZE
    offset_x = panel_x + (preview_size - shape_w) // 2 + 5
    offset_y = panel_y + 30 + (preview_size - shape_h) // 2 + 5

    for r, row in enumerate(shape):
        for c, cell in enumerate(row):
            if cell:
                rect = pygame.Rect(
                    offset_x + c * BLOCK_SIZE,
                    offset_y + r * BLOCK_SIZE,
                    BLOCK_SIZE - 1, BLOCK_SIZE - 1
                )
                pygame.draw.rect(surface, next_piece.color, rect)


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("테트리스 (미리보기)")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 20, bold=True)

    board = Board()
    piece = Tetromino()
    next_piece = Tetromino()   # 다음 블록
    fall_time = 0
    fall_speed = 500

    running = True
    game_over = False

    while running:
        dt = clock.tick(60)
        screen.fill(BLACK)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if not game_over and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    if board.is_valid(piece, dx=-1):
                        piece.x -= 1
                elif event.key == pygame.K_RIGHT:
                    if board.is_valid(piece, dx=1):
                        piece.x += 1
                elif event.key == pygame.K_DOWN:
                    if board.is_valid(piece, dy=1):
                        piece.y += 1
                elif event.key == pygame.K_UP:
                    rotated = [
                        [piece.shape[r][c] for r in range(len(piece.shape) - 1, -1, -1)]
                        for c in range(len(piece.shape[0]))
                    ]
                    if board.is_valid(piece, shape=rotated):
                        piece.shape = rotated
                elif event.key == pygame.K_SPACE:
                    while board.is_valid(piece, dy=1):
                        piece.y += 1

        if not game_over:
            fall_time += dt
            if fall_time >= fall_speed:
                fall_time = 0
                if board.is_valid(piece, dy=1):
                    piece.y += 1
                else:
                    board.lock(piece)
                    board.clear_lines()
                    piece = next_piece        # 다음 블록을 현재 블록으로
                    next_piece = Tetromino()  # 새 다음 블록 생성
                    if not board.is_valid(piece):
                        game_over = True

        # ── 그리기 ──
        board.draw(screen)
        if not game_over:
            draw_piece(screen, piece)

        # 구분선
        pygame.draw.line(screen, LIGHT_GRAY, (BOARD_WIDTH, 0), (BOARD_WIDTH, SCREEN_HEIGHT), 1)

        # [추가] 다음 블록 미리보기
        draw_next_piece(screen, next_piece, font)

        if game_over:
            msg = font.render("GAME OVER", True, WHITE)
            screen.blit(msg, (BOARD_WIDTH // 2 - msg.get_width() // 2, SCREEN_HEIGHT // 2))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
