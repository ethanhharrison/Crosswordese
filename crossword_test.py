from crossword_parser import parse_crossword_json
from crossword import BlockedTileError, Crossword


def main() -> None:
    rows, cols, clues = parse_crossword_json('nyt_crosswords-master/2017/05/15.json')
    crossword = Crossword(rows, cols, clues)
    board = crossword.board
    print(board)
    while not board.is_complete():
        try:
            # Ask for a tile position
            position = input("Choose a tile to select: ").split(" ")
            position = [int(pos) for pos in position]
            board.change_selected_tile(*position)
            # Ask for a value    
            value = input("Choose the value of the tile: ")
            if value == "delete":
                board.selected_tile.remove()
            else:
                board.selected_tile.fill(value)
        except ValueError as verr:
            print(verr)
        except BlockedTileError as bterr:
            print(bterr)
        finally:
            # Show board
            print(board)

if __name__ == "__main__":
    main()