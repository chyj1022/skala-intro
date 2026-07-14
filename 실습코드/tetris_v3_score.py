#
# 교육 환경 설정 및 간단한 파이썬 연습 코드
# 기능 : 개선된 테트리스 #2 — 점수 표시 (브랜치: feature/score → develop)
#
# 작성일 : 2026-07-06
# 작성자 : 백정열, SKALA
#
# 변경일 : 2026-07-06
# 변경 내용 : 추가 기능 확대 - 화면 오른쪽 상단에 획득한 점수 표시, 
#           점수 규칙: 1줄 = 100점, 2줄 = 300점, 3줄 = 500점, 4줄(테트리스) = 800점
#
# All Rights Reserved by SK AX, SKALA
#

import pygame
import random

# ─────────────────────────────────────────────
# 상수
# ─────────────────────────────────────────────
BOARD_WIDTH   = 300
BOARD_HEIGHT  = 600
SIDE_WIDTH    = 150
SCREEN_WIDTH  = BOARD_WIDTH + SIDE_WIDTH
SCREEN_HEIGHT = BOARD_HEIGHT
BLOCK_SIZE = 30
COLS = 10
ROWS = 20

BLACK      = (0, 0, 0)
WHITE      = (255, 255, 255)
GRAY       = (50, 50, 50)
LIGHT_GRAY = (180, 180, 180)
YELLOW     = (255, 215, 0)

COLORS = [
    (0, 240, 240), (0, 0, 240), (240, 160, 0), (240, 240, 0),
    (0, 240, 0), (160, 0, 240), (240, 0, 0),
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

# 줄 삭제 점수표
LINE_SCORES = {1: 100, 2: 300, 3: 500, 4: 800}


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


def draw_next_piece(surface, next_piece, font):
    panel_x = BOARD_WIDTH + 10
    panel_y = 10
    label = font.render("NEXT", True, WHITE)
    surface.blit(label, (panel_x + 20, panel_y))
    preview_size = BLOCK_SIZE * 4
    box_rect = pygame.Rect(panel_x, panel_y + 30, preview_size + 10, preview_size + 10)
    pygame.draw.rect(surface, GRAY, box_rect, 1)
    shape = next_piece.shape
    shape_w = len(shape[0]) * BLOCK_SIZE
    shape_h = len(shape) * BLOCK_SIZE
    offset_x = panel_x + (preview_size - shape_w) // 2 + 5
    offset_y = panel_y + 30 + (preview_size - shape_h) // 2 + 5
    for r, row in enumerate(shape):
        for c, cell in enumerate(row):
            if cell:
                rect = pygame.Rect(
                    offset_x + c * BLOCK_SIZE, offset_y + r * BLOCK_SIZE,
                    BLOCK_SIZE - 1, BLOCK_SIZE - 1
                )
                pygame.draw.rect(surface, next_piece.color, rect)


# ─────────────────────────────────────────────
# [추가] 점수 표시
# ─────────────────────────────────────────────
def draw_score(surface, score, lines, font, small_font):
    """사이드 패널 하단에 점수 및 줄 수 표시"""
    panel_x = BOARD_WIDTH + 10
    y = 200   # next 블록 아래부터

    # 구분선
    pygame.draw.line(surface, LIGHT_GRAY, (panel_x, y), (panel_x + 130, y), 1)
    y += 15

    # SCORE 라벨
    label = font.render("SCORE", True, YELLOW)
    surface.blit(label, (panel_x + 10, y))
    y += 30

    # 점수 숫자
    score_text = small_font.render(str(score), True, WHITE)
    surface.blit(score_text, (panel_x + 10, y))
    y += 40

    # LINES 라벨
    lines_label = font.render("LINES", True, LIGHT_GRAY)
    surface.blit(lines_label, (panel_x + 10, y))
    y += 30

    lines_text = small_font.render(str(lines), True, WHITE)
    surface.blit(lines_text, (panel_x + 10, y))


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("테트리스 (점수 표시)")
    clock = pygame.time.Clock()
    font       = pygame.font.SysFont("Arial", 20, bold=True)
    small_font = pygame.font.SysFont("Arial", 28, bold=True)

    board      = Board()
    piece      = Tetromino()
    next_piece = Tetromino()
    fall_time  = 0
    fall_speed = 500

    score      = 0    # [추가] 점수
    total_lines = 0   # [추가] 총 줄 수

    running   = True
    game_over = False

    while running:
        dt = clock.tick(60)
        screen.fill(BLACK)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if not game_over and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    if board.is_valid(piece, dx=-1): piece.x -= 1
                elif event.key == pygame.K_RIGHT:
                    if board.is_valid(piece, dx=1): piece.x += 1
                elif event.key == pygame.K_DOWN:
                    if board.is_valid(piece, dy=1): piece.y += 1
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
                    cleared = board.clear_lines()
                    # [추가] 점수 계산
                    if cleared > 0:
                        score += LINE_SCORES.get(cleared, 0)
                        total_lines += cleared
                    piece = next_piece
                    next_piece = Tetromino()
                    if not board.is_valid(piece):
                        game_over = True

        board.draw(screen)
        if not game_over:
            draw_piece(screen, piece)

        pygame.draw.line(screen, LIGHT_GRAY, (BOARD_WIDTH, 0), (BOARD_WIDTH, SCREEN_HEIGHT), 1)

        draw_next_piece(screen, next_piece, font)
        # [추가] 점수 그리기
        draw_score(screen, score, total_lines, font, small_font)

        if game_over:
            overlay = pygame.Surface((BOARD_WIDTH, 80), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, SCREEN_HEIGHT // 2 - 40))
            msg  = font.render("GAME OVER", True, WHITE)
            msg2 = small_font.render(f"Score: {score}", True, YELLOW)
            screen.blit(msg,  (BOARD_WIDTH // 2 - msg.get_width() // 2,  SCREEN_HEIGHT // 2 - 30))
            screen.blit(msg2, (BOARD_WIDTH // 2 - msg2.get_width() // 2, SCREEN_HEIGHT // 2 + 5))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
