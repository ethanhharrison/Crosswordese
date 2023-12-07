from crossword import create_board
from crossword_parser import parse_crossword_json
import pygame

# initialize pygame
pygame.init()

# create screen
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
display_surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))


# select font
entry_font = pygame.font.Font("freesansbold.ttf", 32)
clue_number_font = pygame.font.Font("freesansbold.ttf", 12)


# get board
rows, cols, clues = parse_crossword_json("nyt_crosswords-master/2017/05/15.json")
board = create_board(rows, cols, clues)
orientation = "across"


padding = round(0.05 * SCREEN_HEIGHT)
tile_size = round((0.9 * SCREEN_HEIGHT) // board.rows)


while True:
    for event in pygame.event.get():
        # Quit game
        if event.type == pygame.QUIT:
            pygame.quit()
        # Key press
        if event.type == pygame.KEYDOWN:
            pressed_key = pygame.key.get_pressed()
            # Move up and down
            if pressed_key[pygame.K_UP] or pressed_key[pygame.K_DOWN]:
                if orientation == "across":
                    orientation = "down"
                else:
                    pass
            # Move left and right
            elif pressed_key[pygame.K_LEFT] or pressed_key[pygame.K_RIGHT]:
                if orientation == "down":
                    orientation = "across"
                else:
                    pass
            # Type character
            else:
                for i in range(pygame.K_a, pygame.K_z + 1):
                    if pressed_key[i]:
                        char = pygame.key.name(i)
                        pass
        # Mouse click
        if event.type == pygame.MOUSEBUTTONDOWN:
            x_pos, y_pos = pygame.mouse.get_pos()
            num_across = (x_pos - padding) // tile_size
            num_down = (y_pos - padding) // tile_size
            try:
                board.change_selected_tile(num_down, num_across)
            except BaseException as be:
                print(be)

    # Change background color
    bg_color = pygame.Color("white")
    display_surface.fill(bg_color)

    # Draw board
    board_color, board_rect = board.display_board(SCREEN_HEIGHT)
    pygame.draw.rect(display_surface, board_color, board_rect)

    # Update highlighted tiles
    for row in board.tiles:
        for tile in row:
            tile.highlight(orientation)

    # Draw tiles
    display = board.display_tiles(padding, tile_size, entry_font)
    for border_display, text_display in display:
        # Draw borders
        for color, rect in border_display:
            pygame.draw.rect(display_surface, color, rect)
        # Draw entry text
        for text, text_rect in text_display:
            display_surface.blit(text, text_rect)

    # Draw clue text
    for clue in clues:
        tile = board.get_tile(clue.num_down, clue.num_across)
        text_display = tile.display_clue_number(clue.number, padding, tile_size, clue_number_font)
        display_surface.blit(*text_display)

    # Update screen
    pygame.display.update()
