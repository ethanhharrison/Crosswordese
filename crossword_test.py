from crossword_parser import parse_crossword_json
from crossword import BlockedTileError, GameBoard


def main() -> None:
    rows, cols, clues = parse_crossword_json('nyt_crosswords-master/2017/05/15.json')
    board = GameBoard(rows, cols, clues)
    board.assign_clues_to_tiles()
    board.assign_blocked_tiles()
    print(board)
    while not board.is_complete():
        try:
            # Ask for a tile position
            position = input("Choose a tile to select: ").split(" ")
            position = [int(pos) for pos in position]
            board.change_selected_tile(*position)
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