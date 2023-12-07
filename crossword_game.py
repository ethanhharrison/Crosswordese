from crossword import GameBoard
from crossword_parser import parse_crossword_json
import pygame

# initialize pygame
pygame.init()

# create screen
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 750
display_surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))


# select font
entry_font = pygame.font.Font('freesansbold.ttf', 32)
clue_number_font = pygame.font.Font('freesansbold.ttf', 12)

# get board
rows, cols, clues = parse_crossword_json("nyt_crosswords-master/2017/05/15.json")
board = GameBoard(rows, cols, clues)
board.assign_clues_to_tiles()
board.assign_blocked_tiles()
board.selected_tile.selected = True


while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            # end game
            pygame.quit()
            
    # Change background color    
    bg_color = pygame.Color("white")
    display_surface.fill(bg_color)
    
    
    # Draw board
    board_color, board_rect = board.display_board(SCREEN_HEIGHT)
    pygame.draw.rect(display_surface, board_color, board_rect)
    
    
    # Draw tiles
    padding = round(0.05 * SCREEN_HEIGHT)
    tile_size = round((0.9 * SCREEN_HEIGHT) // board.rows)
    display = board.display_tiles(padding, tile_size, entry_font)
    for clue in clues:
        clue.highlight_clue()
    for border_display, text_display in display:
        # Draw borders
        for color, rect in border_display:
            pygame.draw.rect(display_surface, color, rect)
        # Draw entry text
        for text, text_rect in text_display:
            display_surface.blit(text, text_rect)
    
    
    # Draw clue text
    for clue in clues:
        num_down, num_across = clue.position
        tile = board.get_tile(num_down, num_across)
        x_pos = padding + tile_size * num_across
        y_pos = padding + tile_size * num_down + 3
        text_display = tile.display_clue_number(clue.number, x_pos, y_pos, clue_number_font)
        display_surface.blit(*text_display)
    
    
    # Update screen
    pygame.display.update()
            
            
