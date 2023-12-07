from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import string
import pygame


class InvalidPuzzleError(BaseException):
    pass


class BlockedTileError(BaseException):
    pass


class NoSelectedTileError(BaseException):
    pass


@dataclass
class Tile:
    """Class for keeping track of a game tile"""

    blocked: bool
    num_down: int
    num_across: int
    correct_entry: str = " "
    current_entry: str = " "
    empty: bool = True
    selected: bool = False
    highlighted: bool = False
    down_clue: Optional[Clue] = None
    across_clue: Optional[Clue] = None

    def assign_clue(self, clue: Clue, orientation: str) -> None:
        """Attach tile to an associated clue"""
        if orientation == "down":
            self.down_clue = clue
        elif orientation == "across":
            self.across_clue = clue
            
    def highlight(self, orientation: str) -> None:
        if orientation == "across" and self.across_clue: 
            self.highlighted = any([tile.selected for tile in self.across_clue.tiles])
        elif orientation == "down" and self.down_clue:
            self.highlighted = any([tile.selected for tile in self.down_clue.tiles])
        else:
            self.highlighted = False

    def is_correct(self) -> bool:
        """Checks if the tile is correctly filled in"""
        return self.blocked or self.correct_entry == self.current_entry

    def fill(self, value: str) -> None:
        """Fills the tile's current entry with the given value"""
        if self.blocked:
            raise BlockedTileError("Cannot fill blocked tile")
        elif len(value) > 1:
            raise ValueError("Value is too long")
        elif value not in string.ascii_uppercase:
            raise ValueError("Invalid character")
        else:
            self.current_entry = value
            self.empty = True

    def remove(self) -> None:
        """Removes the tile's current entry"""
        if self.empty:
            self.current_entry = " "
            self.empty = False

    def display_border(self, padding: int, size: int, border_width: int):
        x_pos = padding + size * self.num_across
        y_pos = padding + size * self.num_down
        black_rect = pygame.Rect(x_pos, y_pos, size, size)
        yield pygame.Color("black"), black_rect
        inner_rect = pygame.Rect(
            x_pos + border_width,
            y_pos + border_width,
            size - border_width * 2,
            size - border_width * 2)
        if self.selected:
            yield pygame.Color(255, 217, 2), inner_rect
        elif self.highlighted:
            yield pygame.Color(167, 216, 254), inner_rect
        elif not self.blocked:
            yield pygame.Color(255, 255, 255), inner_rect

    def display_current_entry(self, padding: int, size: int, font):
        x_pos = padding + size * self.num_across
        y_pos = padding + size * self.num_down
        if self.current_entry != " ":
            text = font.render(self.current_entry, True, "black")
            text_rect = text.get_rect()
            text_rect.center = (x_pos + size // 2 - 1, y_pos + size // 2 + 1)
            yield text, text_rect

    def display_clue_number(self, number: int, padding: int, size: int, font):
        x_pos = padding + size * self.num_across
        y_pos = padding + size * self.num_down
        text = font.render(str(number), True, "black")
        text_rect = text.get_rect()
        text_rect.topleft = (x_pos + 4, y_pos + 3)
        return text, text_rect

    def print_clues(self):
        """Display the clues for the player"""
        if self.down_clue:
            print("Down:", self.down_clue)
        if self.across_clue:
            print("Across:", self.across_clue)

    def __str__(self) -> str:
        if self.blocked:
            return "[/]"
        else:
            return f"[{self.current_entry}]"


@dataclass
class Clue:
    """Class for defining clues and their associated tiles"""

    number: int
    question: str
    solution: str
    orientation: str
    num_down: int
    num_across: int
    tiles: list[Tile] = field(default_factory=list)
    
    def connect_tiles(self, tiles: list[Tile]) -> None:
        self.tiles = tiles

    def update_tile_solutions(self) -> None:
        """Updates the solution for each tile of that clue"""
        if self.tiles == []:
            raise ValueError("No tiles connected to clue")
        for value, tile in zip(self.solution, self.tiles):
            if tile.correct_entry == " " or tile.correct_entry == value:
                tile.assign_clue(self, self.orientation)
                tile.correct_entry = value
            else:
                raise InvalidPuzzleError("Puzzle has conflicting clues")       

    def __str__(self) -> str:
        output = f"{self.question}:\n"
        for tile in self.tiles:
            output += f"[{tile.num_down}, {tile.num_across}] "
        return output


class GameBoard:
    """Class for creating the game board"""

    def __init__(self, rows: int, cols: int, clues: list[Clue]) -> None:
        self.rows = rows
        self.cols = cols
        self.clues = clues
        self.tiles = self.make_tile_grid(rows, cols)
        self.selected_tile = self.get_tile(0, 0)
        

    def make_tile_grid(self, rows: int, cols: int) -> list[list[Tile]]:
        """Make a tile grid for the board"""
        return [[Tile(False, i, j) for j in range(cols)] for i in range(rows)]

    def assign_clues_to_tiles(self) -> None:
        """Assigns clues to tiles in the grid then updates the tiles' solutionsxs"""
        if self.clues is None:
            return
        for clue in self.clues:
            sol_size = len(clue.solution)
            if clue.orientation == "across":
                tiles = [self.get_tile(clue.num_down, clue.num_across + i) for i in range(sol_size)]
            else:
                tiles = [self.get_tile(clue.num_down + i, clue.num_across) for i in range(sol_size)]
            clue.connect_tiles(tiles)
            clue.update_tile_solutions()

    def assign_blocked_tiles(self) -> None:
        """Make any tile with an empty correct solution a blocked tile"""
        for row in self.tiles:
            for tile in row:
                if tile.correct_entry == " ":
                    tile.blocked = True

    def is_complete(self) -> bool:
        """Check if board is complete"""
        for row in self.tiles:
            if any([not tile.is_correct() for tile in row]):
                return False
        return True

    def get_tile(self, num_down: int, num_across: int) -> Tile:
        """Given the x and y coordinates, selects a tile on the board"""
        if num_down < 0 or num_across < 0:
            raise ValueError("Invalid tile position")
        elif num_down >= self.rows or num_across >= self.cols:
            raise ValueError("Invalid tile position")
        elif self.tiles[num_down][num_across].blocked:
            raise BlockedTileError("Cannot select a blocked tile")
        else:
            return self.tiles[num_down][num_across]

    def change_selected_tile(self, num_down: int, num_across: int) -> None:
        """Change the selected tile"""
        new_tile = self.get_tile(num_down, num_across)
        self.selected_tile.selected = False
        self.selected_tile = new_tile
        self.selected_tile.selected = True
        
    def move(self, orientation: str, direction: int) -> None:
        num_down = self.selected_tile.num_down
        num_across = self.selected_tile.num_across
        if orientation == "across":
            try:
                new_tile = self.get_tile(num_down, num_across + direction)
                pass
            except BlockedTileError:
                num_across += direction
            self.change_selected_tile(num_down, num_across)
        elif orientation == "down":
            pass
            self.change_selected_tile(num_down, num_across)

    def update_tile_entry(self, value: str) -> None:
        """Adds or removes value to the selected tile"""
        if value == "delete":
            self.selected_tile.remove()
        else:
            self.selected_tile.fill(value)

    def display_board(self, screen_height: int):
        padding = round(0.05 * screen_height)
        tile_size = round((0.9 * screen_height) // self.rows)
        board_width = tile_size * self.cols + 4
        board_height = tile_size * self.rows + 4
        board_rect = pygame.Rect(padding - 2, padding - 2, board_width, board_height)
        board_color = pygame.Color("black")
        return board_color, board_rect

    def display_tiles(self, padding: int, tile_size: int, font):
        for i in range(len(self.tiles)):
            row = self.tiles[i]
            for j in range(len(row)):
                tile = row[j]
                tile_display = tile.display_border(padding, tile_size, 2)
                text_display = tile.display_current_entry(padding, tile_size, font)
                yield tile_display, text_display

    def __str__(self) -> str:
        output = ""
        for clue in self.clues:
            output += f"{clue}\n"
        for row in self.tiles:
            for tile in row:
                output += str(tile)
            output += "\n"
        return output

def create_board(rows: int, cols: int, clues: list[Clue]) -> GameBoard:
    board = GameBoard(rows, cols, clues)
    board.assign_clues_to_tiles()
    board.assign_blocked_tiles()
    board.selected_tile.selected = True
    return board