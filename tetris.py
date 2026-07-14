import pygame
import random
import sys

# ---------------------------------------------------------
# 초기 설정
# ---------------------------------------------------------
pygame.init()

# 보드 크기
COLS, ROWS = 10, 20
CELL = 30
BOARD_W, BOARD_H = COLS * CELL, ROWS * CELL

# 화면 크기 (오른쪽에 다음 블록/점수 표시용 여백 추가)
SIDE_PANEL = 180
SCREEN_W = BOARD_W + SIDE_PANEL
SCREEN_H = BOARD_H

screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Tetris")
clock = pygame.time.Clock()

font = pygame.font.SysFont("arial", 24)
big_font = pygame.font.SysFont("arial", 48, bold=True)

# 색상
BLACK = (15, 15, 15)
GRAY = (40, 40, 40)
WHITE = (240, 240, 240)
RED = (200, 30, 30)

# 테트로미노 정의 (각 모양은 4x4 좌표 리스트로 표현, 회전 상태별로 미리 정의하지 않고
# 회전 함수를 이용해 매번 계산)
SHAPES = {
    'I': [[1, 1, 1, 1]],
    'O': [[1, 1],
          [1, 1]],
    'T': [[0, 1, 0],
          [1, 1, 1]],
    'S': [[0, 1, 1],
          [1, 1, 0]],
    'Z': [[1, 1, 0],
          [0, 1, 1]],
    'J': [[1, 0, 0],
          [1, 1, 1]],
    'L': [[0, 0, 1],
          [1, 1, 1]],
}

COLORS = {
    'I': (0, 240, 240),
    'O': (240, 240, 0),
    'T': (160, 0, 240),
    'S': (0, 240, 0),
    'Z': (240, 0, 0),
    'J': (0, 0, 240),
    'L': (240, 160, 0),
}

# ---------------------------------------------------------
# 블록(피스) 클래스
# ---------------------------------------------------------
class Piece:
    def __init__(self, kind):
        self.kind = kind
        self.shape = [row[:] for row in SHAPES[kind]]
        self.color = COLORS[kind]
        # 시작 위치: 보드 상단 중앙
        self.col = COLS // 2 - len(self.shape[0]) // 2
        self.row = 0

    def cells(self, shape=None, row=None, col=None):
        """현재(또는 지정된) 모양이 차지하는 (r, c) 좌표 리스트 반환"""
        shape = self.shape if shape is None else shape
        row = self.row if row is None else row
        col = self.col if col is None else col
        result = []
        for r, line in enumerate(shape):
            for c, v in enumerate(line):
                if v:
                    result.append((row + r, col + c))
        return result

    def rotated_shape(self):
        """시계방향으로 90도 회전한 모양 반환 (원본은 변경하지 않음)"""
        # zip(*shape[::-1]) 이 시계방향 회전 공식
        return [list(row) for row in zip(*self.shape[::-1])]


# ---------------------------------------------------------
# 게임 보드 관련 함수
# ---------------------------------------------------------
def create_board():
    return [[None for _ in range(COLS)] for _ in range(ROWS)]


def valid_position(board, cells):
    for r, c in cells:
        if c < 0 or c >= COLS:
            return False
        if r >= ROWS:
            return False
        if r >= 0 and board[r][c] is not None:
            return False
    return True


def lock_piece(board, piece):
    for r, c in piece.cells():
        if r >= 0:
            board[r][c] = piece.color


def clear_lines(board):
    """꽉 찬 줄을 지우고 지운 줄 수를 반환"""
    new_board = [row for row in board if any(cell is None for cell in row)]
    cleared = ROWS - len(new_board)
    for _ in range(cleared):
        new_board.insert(0, [None for _ in range(COLS)])
    return new_board, cleared


def new_piece():
    kind = random.choice(list(SHAPES.keys()))
    return Piece(kind)


# ---------------------------------------------------------
# 그리기 함수
# ---------------------------------------------------------
def draw_board(board):
    screen.fill(BLACK)

    # 격자
    for r in range(ROWS):
        for c in range(COLS):
            rect = pygame.Rect(c * CELL, r * CELL, CELL, CELL)
            color = board[r][c] if board[r][c] else GRAY
            pygame.draw.rect(screen, color, rect, 0 if board[r][c] else 1)

    pygame.draw.rect(screen, WHITE, (0, 0, BOARD_W, BOARD_H), 2)


def draw_piece(piece):
    for r, c in piece.cells():
        if r >= 0:
            rect = pygame.Rect(c * CELL, r * CELL, CELL, CELL)
            pygame.draw.rect(screen, piece.color, rect)
            pygame.draw.rect(screen, BLACK, rect, 1)


def draw_ghost(board, piece):
    """블록이 떨어질 위치를 미리 보여주는 그림자"""
    ghost = Piece(piece.kind)
    ghost.shape = [row[:] for row in piece.shape]
    ghost.row, ghost.col = piece.row, piece.col
    while valid_position(board, ghost.cells(row=ghost.row + 1)):
        ghost.row += 1
    for r, c in ghost.cells():
        if r >= 0:
            rect = pygame.Rect(c * CELL, r * CELL, CELL, CELL)
            pygame.draw.rect(screen, (90, 90, 90), rect, 2)


def draw_score_topright(score):
    """화면(보드) 오른쪽 상단에 획득한 점수를 반투명 박스로 보여준다."""
    box_margin = 10
    box_w, box_h = 130, 60
    box_x = BOARD_W - box_w - box_margin

    # 반투명 배경 박스
    overlay = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (box_x, box_margin))
    pygame.draw.rect(screen, WHITE, (box_x, box_margin, box_w, box_h), 2)

    # 라벨
    label = font.render("점수", True, WHITE)
    screen.blit(label, (box_x + 10, box_margin + 6))

    # 점수 값
    score_text = font.render(f"{score}", True, WHITE)
    screen.blit(score_text, (box_x + 10, box_margin + 32))


def draw_next_preview_topleft(next_piece):
    """화면(보드) 왼쪽 상단에 다음 블록을 반투명 박스로 미리 보여준다."""
    box_margin = 10
    box_w, box_h = 130, 110

    # 반투명 배경 박스
    overlay = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (box_margin, box_margin))
    pygame.draw.rect(screen, WHITE, (box_margin, box_margin, box_w, box_h), 2)

    # 라벨
    label = font.render("다음 블록", True, WHITE)
    screen.blit(label, (box_margin + 10, box_margin + 8))

    # 블록 미리보기 (작은 셀 크기로 축소해서 표시)
    preview_cell = 20
    shape = next_piece.shape
    color = next_piece.color
    shape_w = len(shape[0]) * preview_cell
    shape_h = len(shape) * preview_cell
    start_x = box_margin + (box_w - shape_w) // 2
    start_y = box_margin + 40 + (box_h - 40 - shape_h) // 2

    for r, line in enumerate(shape):
        for c, v in enumerate(line):
            if v:
                rect = pygame.Rect(start_x + c * preview_cell, start_y + r * preview_cell,
                                    preview_cell, preview_cell)
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, BLACK, rect, 1)


def draw_side_panel(score, level, game_over):
    x0 = BOARD_W + 20

    level_text = font.render(f"레벨: {level}", True, WHITE)
    screen.blit(level_text, (x0, 20))

    help_lines = [
        "조작법",
        "←/→ : 이동",
        "↑ : 회전",
        "↓ : 소프트 드롭",
        "Space : 하드 드롭",
        "R : 재시작",
    ]
    for i, line in enumerate(help_lines):
        t = font.render(line, True, (180, 180, 180))
        screen.blit(t, (x0, 110 + i * 28))

    if game_over:
        over_text = big_font.render("GAME OVER", True, RED)
        rect = over_text.get_rect(center=(BOARD_W // 2, BOARD_H // 2))
        # 반투명 배경
        overlay = pygame.Surface((BOARD_W, BOARD_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        screen.blit(over_text, rect)
        restart_text = font.render("R 키를 눌러 재시작", True, WHITE)
        r_rect = restart_text.get_rect(center=(BOARD_W // 2, BOARD_H // 2 + 50))
        screen.blit(restart_text, r_rect)


# ---------------------------------------------------------
# 점수/레벨 계산
# ---------------------------------------------------------
LINE_SCORES = {1: 100, 2: 300, 3: 500, 4: 800}


def compute_fall_speed(level):
    """레벨이 오를수록 낙하 간격(ms)이 짧아짐"""
    return max(100, 800 - (level - 1) * 70)


# ---------------------------------------------------------
# 메인 게임 루프
# ---------------------------------------------------------
def main():
    board = create_board()
    current = new_piece()
    next_piece = new_piece()

    score = 0
    lines_cleared_total = 0
    level = 1

    fall_time = 0
    fall_speed = compute_fall_speed(level)

    move_delay = 0  # 좌우 연속 이동 시 딜레이 처리용
    down_pressed = False

    game_over = False

    running = True
    while running:
        dt = clock.tick(60)
        fall_time += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    # 재시작
                    board = create_board()
                    current = new_piece()
                    next_piece = new_piece()
                    score = 0
                    lines_cleared_total = 0
                    level = 1
                    fall_speed = compute_fall_speed(level)
                    fall_time = 0
                    game_over = False
                    continue

                if game_over:
                    continue

                if event.key == pygame.K_LEFT:
                    new_cells = current.cells(col=current.col - 1)
                    if valid_position(board, new_cells):
                        current.col -= 1

                elif event.key == pygame.K_RIGHT:
                    new_cells = current.cells(col=current.col + 1)
                    if valid_position(board, new_cells):
                        current.col += 1

                elif event.key == pygame.K_UP:
                    # 시계방향 회전
                    rotated = current.rotated_shape()
                    new_cells = current.cells(shape=rotated)
                    if valid_position(board, new_cells):
                        current.shape = rotated
                    else:
                        # 벽에 부딪히면 좌우로 살짝 밀어보는 간단한 wall-kick
                        kicked = False
                        for dx in (-1, 1, -2, 2):
                            new_cells = current.cells(shape=rotated, col=current.col + dx)
                            if valid_position(board, new_cells):
                                current.shape = rotated
                                current.col += dx
                                kicked = True
                                break
                        # 회전이 불가능하면 그대로 유지

                elif event.key == pygame.K_DOWN:
                    new_cells = current.cells(row=current.row + 1)
                    if valid_position(board, new_cells):
                        current.row += 1
                        fall_time = 0

                elif event.key == pygame.K_SPACE:
                    # 하드 드롭: 바닥까지 즉시 이동
                    while valid_position(board, current.cells(row=current.row + 1)):
                        current.row += 1
                    lock_piece(board, current)
                    board, cleared = clear_lines(board)
                    if cleared:
                        score += LINE_SCORES.get(cleared, 0) * level
                        lines_cleared_total += cleared
                        level = lines_cleared_total // 10 + 1
                        fall_speed = compute_fall_speed(level)

                    current = next_piece
                    next_piece = new_piece()
                    fall_time = 0

                    if not valid_position(board, current.cells()):
                        game_over = True

        if not game_over:
            # 자동 낙하
            if fall_time >= fall_speed:
                fall_time = 0
                new_cells = current.cells(row=current.row + 1)
                if valid_position(board, new_cells):
                    current.row += 1
                else:
                    # 바닥에 닿음 -> 고정
                    lock_piece(board, current)
                    board, cleared = clear_lines(board)
                    if cleared:
                        score += LINE_SCORES.get(cleared, 0) * level
                        lines_cleared_total += cleared
                        level = lines_cleared_total // 10 + 1
                        fall_speed = compute_fall_speed(level)

                    current = next_piece
                    next_piece = new_piece()

                    if not valid_position(board, current.cells()):
                        game_over = True

        # ---------------- 그리기 ----------------
        draw_board(board)
        if not game_over:
            draw_ghost(board, current)
            draw_piece(current)
        draw_next_preview_topleft(next_piece)
        draw_score_topright(score)
        draw_side_panel(score, level, game_over)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()