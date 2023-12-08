from crossword import create_board
from crossword_parser import parse_crossword_json
import pygame


# get board
rows, cols, clues = parse_crossword_json("nyt_crosswords-master/2017/05/15.json")
board = create_board(rows, cols, clues)
orientation = "across"


# initialize pygame
pygame.init()


# create screen
SCREEN_HEIGHT = 750
padding = round(0.05 * SCREEN_HEIGHT)
tile_size = round((0.9 * SCREEN_HEIGHT) // board.rows)
screen_width = tile_size * board.cols + 2 * padding
display_surface = pygame.display.set_mode((screen_width, SCREEN_HEIGHT + 100))


# select font
entry_font_size = SCREEN_HEIGHT // 25
clue_font_size = entry_font_size // 2
arialunicode = pygame.font.match_font("arialunicode")
entry_font = pygame.font.Font(arialunicode, entry_font_size)
clue_number_font = pygame.font.Font(arialunicode, clue_font_size)
clue_question_font = pygame.font.Font(arialunicode, 18)


while True:
    for event in pygame.event.get():
        # Quit game
        if event.type == pygame.QUIT:
            pygame.quit()
        # Mouse click
        elif event.type == pygame.MOUSEBUTTONDOWN:
            x_pos, y_pos = pygame.mouse.get_pos()
            num_across = (x_pos - padding) // tile_size
            num_down = (y_pos - padding) // tile_size
            try:
                if board.get_tile(num_down, num_across).selected:
                    if orientation == "across":
                        orientation = "down"
                    else:
                        orientation = "across"
                else:
                    board.change_selected_tile(num_down, num_across)
            except BaseException as be:
                print(be)
        # Key press
        elif event.type == pygame.KEYDOWN:
            pressed_key = pygame.key.get_pressed()
            # Move up and down
            if pressed_key[pygame.K_UP] or pressed_key[pygame.K_DOWN]:
                if orientation == "across":
                    orientation = "down"
                elif pressed_key[pygame.K_UP]:
                    board.move(orientation, -1)
                elif pressed_key[pygame.K_DOWN]:
                    board.move(orientation, 1)
            # Move left and right
            elif pressed_key[pygame.K_LEFT] or pressed_key[pygame.K_RIGHT]:
                if orientation == "down":
                    orientation = "across"
                elif pressed_key[pygame.K_LEFT]:
                    board.move(orientation, -1)
                elif pressed_key[pygame.K_RIGHT]:
                    board.move(orientation, 1)
            # Go to next clue
            elif pressed_key[pygame.K_RETURN]:
                board.move_to_next_clue(orientation, 1)
            # Type character
            else:
                if pressed_key[pygame.K_BACKSPACE]:
                    if board.selected_tile.current_entry:
                        board.selected_tile.remove()
                    board.move(orientation, -1)
                for i in range(pygame.K_a, pygame.K_z + 1):
                    if pressed_key[i]:
                        char = pygame.key.name(i)
                        try:
                            board.selected_tile.fill(char)
                        except BaseException as be:
                            print(be)
                        board.move(orientation, 1)
                        break


    # Change background color
    bg_color = pygame.Color("white")
    display_surface.fill(bg_color)

    # Draw board
    board_color, board_rect = board.display_board(padding, tile_size, 4)
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
        if text_display:
            for text, text_rect in text_display:
                display_surface.blit(text, text_rect)

    # Draw clue text
    for clue in clues:
        tile = board.get_tile(clue.num_down, clue.num_across)
        text_display = tile.display_clue_number(clue.number, padding, tile_size, clue_number_font)
        display_surface.blit(*text_display)
        
    # Show selected clue's question
    clue_display, clue_text_display = board.display_question(orientation, padding, tile_size, clue_question_font)
    pygame.draw.rect(display_surface, *clue_display)
    display_surface.blit(*clue_text_display)

    # Update screen
    pygame.display.update()
