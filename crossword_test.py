import string
from crossword import BlockedTileError, Tile, GameBoard, Clue

# Board size
SIZE = 5

# Create tiles
def tile_row():
    row = []
    for _ in range(SIZE):
        row.append(Tile(False))
    return row
tile_grid = [tile_row() for _ in range(SIZE)]

# Create clues
clues = [Clue(1, "Fun fact: Starfish see out of their ____", "ARMS", "across", (0, 0), []),
         Clue(1, "First 3 of 25", "ABC", "down", (0, 0), []),
         Clue(2, "Mercilessly make fun of", "ROAST", "down", (0, 1), []),
         Clue(3, "Attachment to the back of a boat", "MOTOR", "down", (0, 2), []),
         Clue(4, "Move around an ice rink", "SKATE", "down", (0, 3), []),
         Clue(5, "You might get lost in one at night", "BOOK", "across", (1, 0), []),
         Clue(6, "Board game where players accumulate wood, brick, sheep, wheat and ore", "CATAN", "across", (2, 0), []),
         Clue(7, "Rejections", "NOS", "down", (2, 4), []),
         Clue(8, "Juan ___, three-time baseball All-Star from 2021-23", "SOTO", "across", (3, 1), []),
         Clue(9, "Very, in French", "TRES", "across", (4, 1), [])]


def main():
    board = GameBoard(tile_grid, clues)
    board.assign_clues_to_tiles()
    board.assign_blocked_tiles()
    
    print(board)
    while not board.is_complete():
        # Ask for a tile position
        try:
            position = input("Choose a tile to select: ").split(" ")
            position = [int(pos) for pos in position]
            board.change_selected_tile(*position)
            # Show current position and clues
            print("Chosen Position:", position)
            board.selected_tile.display_clues()
            # Ask for a value    
            value = input("Choose the value of the tile: ")
            board.update_tile_entry(value)
        except ValueError as verr:
            print(verr)
        except BlockedTileError as bterr:
            print(bterr)
        finally:
            # Show board
            print(board)

if __name__ == "__main__":
    main()