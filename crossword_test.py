import string
import random
from crossword import Tile, GameBoard

# Board size
SIZE = 2

# Create tiles
def tile_row():
    row = []
    for _ in range(SIZE):
        row.append(Tile(False, random.choice(string.ascii_uppercase)))
    return row


def main():
    tile_grid = [tile_row() for _ in range(SIZE)]
    board = GameBoard(tile_grid, None, None)
    print(board)
    while not board.is_complete():
        # Ask for a tile position
        position = None
        while not position or not board.select_tile(*position):
            position = input("Choose a tile to select: ").split(" ")
            position = [int(pos) for pos in position]
        # Ask for a value    
        value = None    
        while not value or not board.fill_tile(value):
            value = input("Choose the value of the tile: ")
        # Show board
        print(board)
    print("Congrats!")

if __name__ == "__main__":
    main()