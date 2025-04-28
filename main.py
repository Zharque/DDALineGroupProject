import sys
import pygame

# Setup and Global Settings
pygame.init()
WINDOW_WIDTH, WINDOW_HEIGHT = 1200, 600
LEFT_PANEL_WIDTH = 400        # Increased from 350
COLOR_PANEL_HEIGHT = 200
TABLE_PANEL_HEIGHT = WINDOW_HEIGHT - COLOR_PANEL_HEIGHT
RIGHT_PANEL_WIDTH = WINDOW_WIDTH - LEFT_PANEL_WIDTH
CELL_SIZE = 20

WHITE = (255, 255, 255)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
BLACK = (0, 0, 0)
DEFAULT_LINE_COLOR = BLACK

color_options = [
    {"name": "Black", "color": (0, 0, 0)},
    {"name": "Red", "color": (255, 0, 0)},
    {"name": "Green", "color": (0, 255, 0)},
    {"name": "Blue", "color": (0, 0, 255)},
    {"name": "Yellow", "color": (255, 255, 0)},
    {"name": "Cyan", "color": (0, 255, 255)},
    {"name": "Magenta", "color": (255, 0, 255)},
    {"name": "Orange", "color": (255, 165, 0)}
]

screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("DDA Line Generator")
clock = pygame.time.Clock()

lines = []  # List of finalized lines
point_a = None
hover_cell = None

# Utility Functions
def get_cell(pos, grid_rect, cell_size):
    x, y = pos
    return ((x - grid_rect.x) // cell_size, (y - grid_rect.y) // cell_size) if grid_rect.collidepoint(pos) else None

def dda_line_points(pointA, pointB):
    x1, y1 = pointA
    x2, y2 = pointB
    dx = x2 - x1
    dy = y2 - y1
    steps = max(abs(dx), abs(dy))
    if steps == 0:
        return [pointA]
    x_inc = dx / steps
    y_inc = dy / steps
    pts = []
    for i in range(steps + 1):
        pts.append((int(round(x1 + i * x_inc)), int(round(y1 + i * y_inc))))
    return pts

def get_color_swatches(panel_rect):
    swatch_size, gap, num_cols, num_rows = 40, 10, 4, 2
    total_width = num_cols * swatch_size + (num_cols - 1) * gap
    total_height = num_rows * swatch_size + (num_rows - 1) * gap
    start_x = panel_rect.x + (panel_rect.width - total_width) // 2
    start_y = panel_rect.y + (panel_rect.height - total_height) // 2
    swatches = []
    for idx, option in enumerate(color_options):
        row = idx // num_cols
        col = idx % num_cols
        x = start_x + col * (swatch_size + gap)
        y = start_y + row * (swatch_size + gap)
        swatch_rect = pygame.Rect(x, y, swatch_size, swatch_size)
        swatches.append({"rect": swatch_rect, "color": option["color"]})
    return swatches

# UI Rendering Functions
def draw_color_panel(surface, rect):
    pygame.draw.rect(surface, LIGHT_GRAY, rect)
    pygame.draw.rect(surface, BLACK, rect, 2)
    for swatch in get_color_swatches(rect):
        pygame.draw.rect(surface, swatch["color"], swatch["rect"])
        border = 3 if swatch["color"] == DEFAULT_LINE_COLOR else 1
        pygame.draw.rect(surface, WHITE if swatch["color"] == DEFAULT_LINE_COLOR else BLACK, swatch["rect"], border)

def draw_table_panel(surface, rect):
    pygame.draw.rect(surface, LIGHT_GRAY, rect)
    pygame.draw.rect(surface, BLACK, rect, 2)
    font = pygame.font.SysFont(None, 16)
    # Columns: L#, A, B, dx, dy, St, x_i, y_i, Color, Del
    col_headers = ["L#", "A", "B", "dx", "dy", "St", "x_i", "y_i", "Color", "Del"]
    col_widths = [30, 45, 45, 25, 25, 35, 35, 35, 45, 40]
    x_offset = rect.x + 5
    header_y = rect.y + 5
    for i, header in enumerate(col_headers):
        cell_x = x_offset + sum(col_widths[:i])
        surface.blit(font.render(header, True, BLACK), (cell_x, header_y))
    header_bottom_y = header_y + 18
    pygame.draw.line(surface, BLACK, (rect.x, header_bottom_y), (rect.x + rect.width, header_bottom_y), 2)
    row_y = header_bottom_y + 3
    row_height = 16
    for idx, line in enumerate(lines):
        a = line["start"]
        b = line["end"]
        dx = b[0] - a[0]
        dy = b[1] - a[1]
        steps = max(abs(dx), abs(dy))
        x_inc = dx / steps if steps else 0
        y_inc = dy / steps if steps else 0
        row_values = [str(idx + 1), f"({a[0]},{a[1]})", f"({b[0]},{b[1]})",
                      str(dx), str(dy), str(steps), f"{x_inc:.2f}", f"{y_inc:.2f}"]
        for i, value in enumerate(row_values):
            cell_x = x_offset + sum(col_widths[:i])
            surface.blit(font.render(value, True, BLACK), (cell_x, row_y))
        color_cell_x = x_offset + sum(col_widths[:8])
        color_rect = pygame.Rect(color_cell_x + 5, row_y + 2, col_widths[8] - 10, row_height - 4)
        pygame.draw.rect(surface, line["color"], color_rect)
        pygame.draw.rect(surface, BLACK, color_rect, 1)
        del_cell_x = x_offset + sum(col_widths[:9])
        delete_rect = pygame.Rect(del_cell_x + 5, row_y + 2, col_widths[9] - 10, row_height - 4)
        pygame.draw.rect(surface, (255, 0, 0), delete_rect)
        pygame.draw.rect(surface, BLACK, delete_rect, 1)
        surface.blit(font.render("X", True, WHITE), (delete_rect.x + 10, delete_rect.y + 2))
        line["delete_rect"] = delete_rect
        row_y += row_height

def draw_grid_panel(surface, rect):
    pygame.draw.rect(surface, WHITE, rect)
    pygame.draw.rect(surface, BLACK, rect, 2)
    cols = rect.width // CELL_SIZE
    rows = rect.height // CELL_SIZE
    for col in range(cols + 1):
        pygame.draw.line(surface, LIGHT_GRAY, (rect.x + col * CELL_SIZE, rect.y),
                         (rect.x + col * CELL_SIZE, rect.y + rect.height))
    for row in range(rows + 1):
        pygame.draw.line(surface, LIGHT_GRAY, (rect.x, rect.y + row * CELL_SIZE),
                         (rect.x + rect.width, rect.y + row * CELL_SIZE))
    for line in lines:
        pts = dda_line_points(line["start"], line["end"])
        for pt in pts:
            pygame.draw.rect(surface, line["color"],
                             pygame.Rect(rect.x + pt[0] * CELL_SIZE, rect.y + pt[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE))
    if point_a and hover_cell:
        pts = dda_line_points(point_a, hover_cell)
        for pt in pts:
            pygame.draw.rect(surface, DEFAULT_LINE_COLOR,
                             pygame.Rect(rect.x + pt[0] * CELL_SIZE, rect.y + pt[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE))
    if hover_cell:
        pygame.draw.rect(surface, (180, 180, 255),
                         pygame.Rect(rect.x + hover_cell[0] * CELL_SIZE, rect.y + hover_cell[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE), 2)

def draw_ui_panels(surface):
    color_panel_rect = pygame.Rect(0, 0, LEFT_PANEL_WIDTH, COLOR_PANEL_HEIGHT)
    table_panel_rect = pygame.Rect(0, COLOR_PANEL_HEIGHT, LEFT_PANEL_WIDTH, TABLE_PANEL_HEIGHT)
    grid_panel_rect = pygame.Rect(LEFT_PANEL_WIDTH, 0, RIGHT_PANEL_WIDTH, WINDOW_HEIGHT)
    draw_color_panel(surface, color_panel_rect)
    draw_table_panel(surface, table_panel_rect)
    draw_grid_panel(surface, grid_panel_rect)
    return color_panel_rect, table_panel_rect, grid_panel_rect

# Main Loop
def main():
    global point_a, hover_cell, DEFAULT_LINE_COLOR
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Check for delete button clicks
                for line in lines.copy():
                    if "delete_rect" in line and line["delete_rect"].collidepoint(event.pos):
                        lines.remove(line)
                        break
                if event.pos[0] < LEFT_PANEL_WIDTH:
                    if event.pos[1] < COLOR_PANEL_HEIGHT:
                        for swatch in get_color_swatches(pygame.Rect(0, 0, LEFT_PANEL_WIDTH, COLOR_PANEL_HEIGHT)):
                            if swatch["rect"].collidepoint(event.pos):
                                DEFAULT_LINE_COLOR = swatch["color"]
                                break
                elif event.pos[0] >= LEFT_PANEL_WIDTH:
                    grid_rect = pygame.Rect(LEFT_PANEL_WIDTH, 0, RIGHT_PANEL_WIDTH, WINDOW_HEIGHT)
                    cell = get_cell(event.pos, grid_rect, CELL_SIZE)
                    if cell:
                        if point_a is None:
                            point_a = cell
                        else:
                            lines.append({"start": point_a, "end": cell, "color": DEFAULT_LINE_COLOR})
                            point_a = None
            elif event.type == pygame.MOUSEMOTION:
                if event.pos[0] >= LEFT_PANEL_WIDTH:
                    grid_rect = pygame.Rect(LEFT_PANEL_WIDTH, 0, RIGHT_PANEL_WIDTH, WINDOW_HEIGHT)
                    hover_cell = get_cell(event.pos, grid_rect, CELL_SIZE)
                else:
                    hover_cell = None
        screen.fill(DARK_GRAY)
        draw_ui_panels(screen)
        pygame.display.flip()
        clock.tick(60)
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
