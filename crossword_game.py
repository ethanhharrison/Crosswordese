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
font = pygame.font.Font('freesansbold.ttf', 32)


# get board
options = parse_crossword_json('nyt_crosswords-master/2018/03/09.json')
board = GameBoard(*options)
board.assign_clues_to_tiles()
board.assign_blocked_tiles()
board.get_tile(0, 0).current_entry = "A"


while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            # end game
            pygame.quit()
            
    # Change background color    
    bg_color = pygame.Color(255, 255, 255)
    display_surface.fill(bg_color)
    
    
    # Draw board
    board_color, board_rect = board.display_board(SCREEN_HEIGHT)
    pygame.draw.rect(display_surface, board_color, board_rect)
    
    
    # Draw tiles
    padding = round(0.05 * SCREEN_HEIGHT)
    tile_size = round((0.9 * SCREEN_HEIGHT) // board.rows)
    tiles_display = board.display_tiles(padding, tile_size)
    for color, rect in tiles_display:
        pygame.draw.rect(display_surface, color, rect)
        
        
    # Draw text
    text_display = board.display_current_entries(padding, tile_size, font)
    for text, text_rect in text_display:
        display_surface.blit(text, text_rect) # type: ignore
    
    
    # Update screen
    pygame.display.update()
            
            
