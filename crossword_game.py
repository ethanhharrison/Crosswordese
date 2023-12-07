from crossword import GameBoard
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
board = GameBoard(rows, cols, clues)
board.assign_clues_to_tiles()
board.assign_blocked_tiles()
board.selected_tile.selected = True
orientation = "across"


while True:
    for event in pygame.event.get():
        # Quit game
        if event.type == pygame.QUIT:
            pygame.quit()
        # Key press
        if event.type == pygame.KEYDOWN:
            # Change orientation
            if event.key == pygame.K_UP:
                if orientation == "across":
                    orientation = "down"
                else:
                    orientation = "across"
            # Change position
            elif event.key == pygame.K_DOWN:
                pass
            elif event.key == pygame.K_LEFT:
                pass
            elif event.key == pygame.K_RIGHT:
                pass


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
    padding = round(0.05 * SCREEN_HEIGHT)
    tile_size = round((0.9 * SCREEN_HEIGHT) // board.rows)
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
        text_display = tile.display_clue_number(
            clue.number, padding, tile_size, clue_number_font)
        display_surface.blit(*text_display)


    # Update screen
    pygame.display.update()
