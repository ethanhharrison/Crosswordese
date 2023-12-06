from crossword import Tile, GameBoard

# Board size
SIZE = 2

# Create tiles
def tile_row():
    row = []
    for _ in range(SIZE-1):
        row.append(Tile(False, "a"))
    row.append(Tile(True, "/"))
    return row


def main():
    tile_grid = [tile_row() for _ in range(SIZE)]
    board = GameBoard(tile_grid)
    print(board)
    while not board.is_complete():
        # Ask for a tile position
        position = None
        while not position or not board.select_tile(*position):
            position = input("Choose a tile to select: ").split(" ")
            position = [int(pos) for pos in position]
        # Ask for a value    
        value = None    
        while not value or not board.update_tile(value):
            value = input("Choose the value of the tile: ")
        # Show board
        print(board)
    print("Congrats!")

if __name__ == "__main__":
    main()