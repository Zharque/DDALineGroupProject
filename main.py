import sys
import pygame

# -------------------------
# Setup and Global Settings
# -------------------------

pygame.init()

# Overall window dimensions
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 600

# Left panel dimensions and layout
LEFT_PANEL_WIDTH = 350  # Hosts the color selection panel and the table
COLOR_PANEL_HEIGHT = 200
TABLE_PANEL_HEIGHT = WINDOW_HEIGHT - COLOR_PANEL_HEIGHT  # 400

# Right panel dimensions (for the grid)
RIGHT_PANEL_WIDTH = WINDOW_WIDTH - LEFT_PANEL_WIDTH  # 850

# Grid settings
CELL_SIZE = 20

# Colors
WHITE      = (255, 255, 255)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY  = (100, 100, 100)
BLACK      = (0, 0, 0)

# Default drawing line color (modifiable via color selection)
DEFAULT_LINE_COLOR = BLACK

# (No custom title buttons now, so we remove that code)

# Color palette for the color selection panel
# Now 8 colors arranged in 2 rows with 4 colors each.
color_options = [
    {"name": "Black",   "color": (0, 0, 0)},
    {"name": "Red",     "color": (255, 0, 0)},
    {"name": "Green",   "color": (0, 255, 0)},
    {"name": "Blue",    "color": (0, 0, 255)},
    {"name": "Yellow",  "color": (255, 255, 0)},
    {"name": "Cyan",    "color": (0, 255, 255)},
    {"name": "Magenta", "color": (255, 0, 255)},
    {"name": "Orange",  "color": (255, 165, 0)}
]

# Create window and clock
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("DDA Line Generator")
clock = pygame.time.Clock()

# -------------------------
# Global Drawing State
# -------------------------
lines = []            # List of finalized lines (each stores 'start', 'end', and 'color')
point_a = None        # Starting grid cell for the current DDA line
hover_cell = None     # Current grid cell under the mouse in the grid

# -------------------------
# Utility Functions
# -------------------------
def get_cell(pos, grid_rect, cell_size):
    """
    Converts a pixel position to grid cell coordinates within grid_rect.
    Returns (cell_x, cell_y) if inside grid_rect; otherwise returns None.
    """
    x, y = pos
    if grid_rect.collidepoint(pos):
        cell_x = (x - grid_rect.x) // cell_size
        cell_y = (y - grid_rect.y) // cell_size
        return (cell_x, cell_y)
    return None

def dda_line_points(pointA, pointB):
    """
    Computes the list of grid cell positions from pointA to pointB using the DDA algorithm.
    Both points are in grid cell coordinates.
    """
    x1, y1 = pointA
    x2, y2 = pointB
    dx = x2 - x1
    dy = y2 - y1
    steps = max(abs(dx), abs(dy))
    if steps == 0:
        return [pointA]
    x_inc = dx / steps
    y_inc = dy / steps
    points = []
    x, y = x1, y1
    for _ in range(steps + 1):
        points.append((int(round(x)), int(round(y))))
        x += x_inc
        y += y_inc
    return points

def get_color_swatches(panel_rect):
    """
    Computes and returns a list of swatches (each with a rectangle and color)
    for the given color panel. Swatches are arranged in 2 rows with 4 per row.
    """
    swatch_size = 40
    gap = 10
    num_cols = 4
    num_rows = 2
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
        swatches.append({'rect': swatch_rect, 'color': option['color']})
    return swatches

# -------------------------
# UI Panel Rendering Functions
# -------------------------
def draw_color_panel(surface, rect):
    """
    Draws the color selection panel (top left section).
    """
    pygame.draw.rect(surface, LIGHT_GRAY, rect)
    pygame.draw.rect(surface, BLACK, rect, 2)
    
    swatches = get_color_swatches(rect)
    for swatch in swatches:
        pygame.draw.rect(surface, swatch['color'], swatch['rect'])
        # Draw a thicker white border if this color is selected
        if swatch['color'] == DEFAULT_LINE_COLOR:
            pygame.draw.rect(surface, WHITE, swatch['rect'], 3)
        else:
            pygame.draw.rect(surface, BLACK, swatch['rect'], 1)

def draw_table_panel(surface, rect):
    """
    Draws the table panel (lower left) with headers and DDA computation details.
    Now includes an extra column for the line color.
    """
    pygame.draw.rect(surface, LIGHT_GRAY, rect)
    pygame.draw.rect(surface, BLACK, rect, 2)
    
    font = pygame.font.SysFont(None, 16)
    
    # Column Headers: L#, A, B, dx, dy, St, x_i, y_i, Color
    col_headers = ["L#", "A", "B", "dx", "dy", "St", "x_i", "y_i", "Color"]
    # Define column widths so that they fit within LEFT_PANEL_WIDTH (350px)
    col_widths = [30, 45, 45, 25, 25, 35, 35, 35, 45]  # Total ~30+45+45+25+25+35+35+35+45 = 320
    
    x_offset = rect.x + 5
    header_y = rect.y + 5
    
    # Render header row
    for i, header in enumerate(col_headers):
        cell_x = x_offset + sum(col_widths[:i])
        rendered = font.render(header, True, BLACK)
        surface.blit(rendered, (cell_x, header_y))
    
    # Underline header
    header_bottom_y = header_y + 18
    pygame.draw.line(surface, BLACK, (rect.x, header_bottom_y), (rect.x + rect.width, header_bottom_y), 2)
    
    # Render data rows for each finalized line
    row_y = header_bottom_y + 3
    row_height = 16
    for idx, line in enumerate(lines):
        a = line['start']
        b = line['end']
        dx = b[0] - a[0]
        dy = b[1] - a[1]
        steps = max(abs(dx), abs(dy))
        if steps != 0:
            x_inc = dx / steps
            y_inc = dy / steps
        else:
            x_inc, y_inc = 0, 0
        
        # Create row values for columns 1-8 (text)
        row_values = [
            str(idx + 1),
            f"({a[0]},{a[1]})",
            f"({b[0]},{b[1]})",
            str(dx),
            str(dy),
            str(steps),
            f"{x_inc:.2f}",
            f"{y_inc:.2f}"
        ]
        
        for i, value in enumerate(row_values):
            cell_x = x_offset + sum(col_widths[:i])
            rendered = font.render(value, True, BLACK)
            surface.blit(rendered, (cell_x, row_y))
        
        # For the ninth column, draw a small swatch for the line color
        color_cell_x = x_offset + sum(col_widths[:8])
        swatch_rect = pygame.Rect(color_cell_x + 5, row_y + 2, col_widths[8] - 10, row_height - 4)
        pygame.draw.rect(surface, line['color'], swatch_rect)
        pygame.draw.rect(surface, BLACK, swatch_rect, 1)
        
        row_y += row_height

def draw_grid_panel(surface, rect):
    """
    Draws the grid panel (right column) including:
      • The grid background and lines,
      • Finalized DDA lines,
      • A temporary line (if drawing is in progress),
      • And a highlight for the hovered cell.
    """
    pygame.draw.rect(surface, WHITE, rect)
    pygame.draw.rect(surface, BLACK, rect, 2)
    
    cols = rect.width // CELL_SIZE
    rows = rect.height // CELL_SIZE
    
    # Draw vertical grid lines
    for col in range(cols + 1):
        start = (rect.x + col * CELL_SIZE, rect.y)
        end = (rect.x + col * CELL_SIZE, rect.y + rect.height)
        pygame.draw.line(surface, LIGHT_GRAY, start, end)
    
    # Draw horizontal grid lines
    for row in range(rows + 1):
        start = (rect.x, rect.y + row * CELL_SIZE)
        end = (rect.x + rect.width, rect.y + row * CELL_SIZE)
        pygame.draw.line(surface, LIGHT_GRAY, start, end)
    
    # Draw finalized lines using DDA
    for line in lines:
        pts = dda_line_points(line['start'], line['end'])
        for pt in pts:
            cell_rect = pygame.Rect(rect.x + pt[0] * CELL_SIZE, rect.y + pt[1] * CELL_SIZE,
                                    CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(surface, line['color'], cell_rect)
    
    # Draw temporary line (if in progress)
    if point_a and hover_cell:
        pts = dda_line_points(point_a, hover_cell)
        for pt in pts:
            cell_rect = pygame.Rect(rect.x + pt[0] * CELL_SIZE, rect.y + pt[1] * CELL_SIZE,
                                    CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(surface, DEFAULT_LINE_COLOR, cell_rect)
    
    # Highlight the hovered cell
    if hover_cell:
        cell_rect = pygame.Rect(rect.x + hover_cell[0] * CELL_SIZE, rect.y + hover_cell[1] * CELL_SIZE,
                                CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(surface, (180, 180, 255), cell_rect, 2)

def draw_ui_panels(surface):
    """
    Draws all UI panels:
      - Left column: top (color panel) and bottom (table panel)
      - Right column: grid panel
    """
    # Left column panels
    color_panel_rect = pygame.Rect(0, 0, LEFT_PANEL_WIDTH, COLOR_PANEL_HEIGHT)
    table_panel_rect = pygame.Rect(0, COLOR_PANEL_HEIGHT, LEFT_PANEL_WIDTH, TABLE_PANEL_HEIGHT)
    # Right panel (grid)
    grid_panel_rect = pygame.Rect(LEFT_PANEL_WIDTH, 0, RIGHT_PANEL_WIDTH, WINDOW_HEIGHT)
    
    draw_color_panel(surface, color_panel_rect)
    draw_table_panel(surface, table_panel_rect)
    draw_grid_panel(surface, grid_panel_rect)
    
    return color_panel_rect, table_panel_rect, grid_panel_rect

# -------------------------
# Main Application Loop
# -------------------------
def main():
    global point_a, hover_cell, DEFAULT_LINE_COLOR

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Left column clicks (for color selection and table panel; only color panel matters here)
                if event.pos[0] < LEFT_PANEL_WIDTH:
                    if event.pos[1] < COLOR_PANEL_HEIGHT:
                        color_panel_rect = pygame.Rect(0, 0, LEFT_PANEL_WIDTH, COLOR_PANEL_HEIGHT)
                        swatches = get_color_swatches(color_panel_rect)
                        for swatch in swatches:
                            if swatch['rect'].collidepoint(event.pos):
                                DEFAULT_LINE_COLOR = swatch['color']
                                break
                    # Clicks in the table panel are not used for drawing.
                # Right column: Grid clicks for drawing lines
                elif event.pos[0] >= LEFT_PANEL_WIDTH:
                    grid_panel_rect = pygame.Rect(LEFT_PANEL_WIDTH, 0, RIGHT_PANEL_WIDTH, WINDOW_HEIGHT)
                    cell = get_cell(event.pos, grid_panel_rect, CELL_SIZE)
                    if cell:
                        if point_a is None:
                            point_a = cell  # Set start point A
                        else:
                            lines.append({'start': point_a, 'end': cell, 'color': DEFAULT_LINE_COLOR})
                            point_a = None

            elif event.type == pygame.MOUSEMOTION:
                # Update hover_cell only when mouse is in the grid panel
                if event.pos[0] >= LEFT_PANEL_WIDTH:
                    grid_panel_rect = pygame.Rect(LEFT_PANEL_WIDTH, 0, RIGHT_PANEL_WIDTH, WINDOW_HEIGHT)
                    hover_cell = get_cell(event.pos, grid_panel_rect, CELL_SIZE)
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
