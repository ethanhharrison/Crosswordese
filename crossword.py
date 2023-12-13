from __future__ import annotations
from dataclasses import dataclass, field
from typing import Generator, Optional
from textwrap import TextWrapper
from string import ascii_letters
from pygame import Color, Rect, Surface
from pygame.font import Font



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
    correct_entry: str = ""
    current_entry: str = ""
    selected: bool = False
    highlighted: bool = False
    down_clue: Optional[Clue] = None
    across_clue: Optional[Clue] = None

    def assign_clue(self, clue: Clue) -> None:
        """Attach tile to an associated clue"""
        if clue.orientation == "down":
            self.down_clue = clue
        else:
            self.across_clue = clue

    def highlight(self, orientation: str) -> None:
        """Checks if the the tile should be highlighted"""
        if orientation == "across" and self.across_clue:
            selected_clue = self.across_clue
        elif self.down_clue:
            selected_clue = self.down_clue
        else:
            self.highlighted = False
            return
        self.highlighted = any([tile.selected for tile in selected_clue.tiles])

    def is_correct(self) -> bool:
        """Checks if the tile is correctly filled in"""
        return self.blocked or self.correct_entry == self.current_entry

    def fill(self, value: str) -> None:
        """Fills the tile's current entry with the given value"""
        if self.blocked:
            raise BlockedTileError("Cannot fill blocked tile")
        elif len(value) > 1:
            raise ValueError("Value is too long")
        elif value not in ascii_letters:
            raise ValueError("Invalid character")
        else:
            self.current_entry = value.upper()

    def remove(self) -> None:
        """Removes the tile's current entry"""
        self.current_entry = ""

    def display_border(
        self, 
        padding: int, 
        size: int, 
        border_width: int, 
        show_error: bool
    ) -> Generator[tuple[Color, Rect], None, None]:
        x_pos: int = padding + size * self.num_across
        y_pos: int = padding + size * self.num_down
        inner_x: int = x_pos + border_width
        inner_y: int = y_pos + border_width
        inner_size: int = size - border_width * 2
        
        outer_rect: Rect = Rect(x_pos, y_pos, size, size)
        inner_rect: Rect = Rect(inner_x, inner_y, inner_size, inner_size)
        if self.blocked:
            yield Color("black"), outer_rect
        else:
            yield Color(161, 161, 161), outer_rect # gray border
        if self.selected:
            yield Color(255, 217, 2), inner_rect   # yellow box
        elif show_error and self.current_entry:
            if self.current_entry == self.correct_entry:
                yield Color("green"), inner_rect   # green box
            else:
                yield Color("red"), inner_rect     # red box
        elif self.highlighted:
            yield Color(167, 216, 254), inner_rect # blue box
        elif not self.blocked:
            yield Color(255, 255, 255), inner_rect # white box

    def display_current_entry(
        self, 
        padding: int, 
        size: int, 
        font: Font
    ) -> Generator[tuple[Surface, Rect], None, None]:
        x_pos: int = padding + size * self.num_across
        y_pos: int = padding + size * self.num_down
        if self.current_entry:
            text: Surface = font.render(self.current_entry, True, "black")
            text_rect: Rect = text.get_rect()
            text_rect.center = (x_pos + size // 2 - 1, y_pos + size // 2 + 5)
            yield text, text_rect

    def display_clue_number(
        self, 
        number: int, 
        padding: int, 
        size: int, 
        font: Font
    ) -> tuple[Surface, Rect]:
        x_pos: int = padding + size * self.num_across
        y_pos: int = padding + size * self.num_down
        text: Surface = font.render(str(number), True, "black")
        text_rect: Rect = text.get_rect()
        text_rect.topleft = (x_pos + 4, y_pos - 1)
        return text, text_rect

    def __str__(self) -> str:
        if self.blocked:
            return "[/]"
        elif self.current_entry:
            return f"[{self.current_entry}]"
        else:
            return "[ ]"


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

    def update_tiles(self) -> None:
        """Updates the solution for each tile of that clue"""
        if self.tiles == []:
            raise ValueError("No tiles connected to clue")
        for value, tile in zip(self.solution, self.tiles):
            if tile.correct_entry == "" or tile.correct_entry == value:
                tile.assign_clue(self)
                tile.correct_entry = value
            else:
                raise InvalidPuzzleError("Puzzle has conflicting clues")

    def display_question_text(
        self, 
        x_pos: int, 
        y_pos: int, 
        width: int, 
        height: int, 
        font: Font
    ) -> list[tuple[Surface, Rect]]:
        clue_text: str = f"{self.number}{self.orientation[0].upper()}"
        clue_text += f"     {self.question}"

        wrapper: TextWrapper = TextWrapper(width=75, subsequent_indent="          ")
        clue_text_lines: list[str] = wrapper.wrap(clue_text)

        line_height: int = font.get_height()
        text_height: int = line_height * len(clue_text_lines)
        y_offset: int = (height - text_height) // 2

        clue_lines: list[tuple[Surface, Rect]] = []
        for i, line in enumerate(clue_text_lines):
            text: Surface = font.render(line, True, "black")
            text_rect: Rect = text.get_rect()
            text_rect.topleft = (x_pos + 25, y_pos + y_offset + i * line_height)
            clue_lines.append((text, text_rect))
        return clue_lines

    def display_question_box(
        self, 
        x_pos: int, 
        y_pos: int, 
        width: int, 
        height: int
    ) -> tuple[Color, Rect]:
        clue_bg_color: Color = Color(221, 239, 255)
        clue_rect: Rect = Rect(x_pos, y_pos, width, height)
        return clue_bg_color, clue_rect

    def __str__(self) -> str:
        output: str = f"{self.question}:\n"
        for tile in self.tiles:
            output += f"[{tile.num_down}, {tile.num_across}] "
        return output


class GameBoard:
    """Class for creating the game board"""

    def __init__(self, rows: int, cols: int) -> None:
        self.rows = rows
        self.cols = cols
        self.tiles = self.make_tile_grid(rows, cols)
        self.selected_tile = self.get_tile(0, 0)
        self.selected_tile.selected = True

    def make_tile_grid(self, rows: int, cols: int) -> list[list[Tile]]:
        """Make a tile grid for the board"""
        return [[Tile(False, i, j) for j in range(cols)] for i in range(rows)]

    def is_complete(self) -> bool:
        """Check if board is complete"""
        for row in self.tiles:
            if any([not tile.is_correct() for tile in row]):
                return False
        return True
    
    # record the accuracy of the board (total correct / total tiles)
    def accuracy(self) -> float:
        total_correct = 0
        total_tiles = 0
        for row in self.tiles:
            for tile in row:
                if not tile.blocked and tile.current_entry:
                    if tile.is_correct():
                        total_correct += 1
                    total_tiles += 1
        if total_tiles == 0:
            return 0
        return total_correct / total_tiles

    def in_bounds(self, num_down: int, num_across: int) -> bool:
        if num_down < 0 or num_across < 0:
            return False
        elif num_down >= self.rows or num_across >= self.cols:
            return False
        else:
            return True

    def get_tile(self, num_down: int, num_across: int) -> Tile:
        """Given the x and y coordinates, selects a tile on the board"""
        if not self.in_bounds(num_down, num_across):
            raise ValueError("Invalid tile position")
        elif self.tiles[num_down][num_across].blocked:
            raise BlockedTileError("Cannot select a blocked tile")
        else:
            return self.tiles[num_down][num_across]

    def change_selected_tile(self, num_down: int, num_across: int) -> None:
        """Change the selected tile"""
        new_tile: Tile = self.get_tile(num_down, num_across)
        self.selected_tile.selected = False
        self.selected_tile = new_tile
        self.selected_tile.selected = True

    def display_board(
        self, 
        padding: int, 
        tile_size: int, 
        border_width: int
    ) -> tuple[Color, Rect]:
        board_width = tile_size * self.cols + border_width
        board_height = tile_size * self.rows + border_width
        offset = padding - border_width // 2
        board_rect: Rect = Rect(offset, offset, board_width, board_height)
        board_color: Color = Color("black")
        return board_color, board_rect

    def display_tiles(
        self, 
        padding: int, 
        tile_size: int, 
        font: Font, 
        show_errors: bool
    ) -> Generator[tuple[list[tuple[Color, Rect]], list[tuple[Surface, Rect]]], None, None]:
        for i in range(len(self.tiles)):
            row: list[Tile] = self.tiles[i]
            for j in range(len(row)):
                tile: Tile = row[j]
                tile_display = tile.display_border(padding, tile_size, 1, show_errors)
                text_display = tile.display_current_entry(padding, tile_size, font)
                yield list(tile_display), list(text_display)

    def display_clue(
        self, 
        orientation: str, 
        padding: int, 
        tile_size: int, 
        font: Font
    ) -> tuple[tuple[Color, Rect], list[tuple[Surface, Rect]]]:
        x_pos: int = padding
        y_pos: int = padding + tile_size * self.rows + 10
        width: int = tile_size * self.cols

        if orientation == "down" and self.selected_tile.down_clue:
            selected_clue: Clue = self.selected_tile.down_clue
        elif orientation == "across" and self.selected_tile.across_clue:
            selected_clue: Clue = self.selected_tile.across_clue
        else:
            raise ValueError("No clue associated with tile")

        clue_box: tuple[Color, Rect] = selected_clue.display_question_box(
            x_pos, y_pos, width, 75)
        clue_lines: list[tuple[Surface, Rect]] = selected_clue.display_question_text(
            x_pos, y_pos, width, 75, font)

        return clue_box, clue_lines

    def __str__(self) -> str:
        output: str = ""
        for row in self.tiles:
            for tile in row:
                output += str(tile)
            output += "\n"
        return output


class Crossword:
    """Class for representing the crossword puzzle"""

    def __init__(self, rows: int, cols: int, clues: list[Clue]) -> None:
        self.board = GameBoard(rows, cols)
        self.clues = clues
        self.assign_clues_to_tiles()
        self.assign_blocked_tiles()

    def assign_blocked_tiles(self) -> None:
        """Make any tile with an empty correct solution a blocked tile"""
        for row in self.board.tiles:
            for tile in row:
                if tile.correct_entry == "":
                    tile.blocked = True

    def assign_clues_to_tiles(self) -> None:
        """Assigns clues to tiles in the grid then updates the tiles' solutionsxs"""
        for clue in self.clues:
            sol_size: int = len(clue.solution)
            for i in range(sol_size):
                if clue.orientation == "across":
                    tile: Tile = self.board.get_tile(clue.num_down, clue.num_across + i)
                else:
                    tile: Tile = self.board.get_tile(clue.num_down + i, clue.num_across)
                clue.tiles.append(tile)
            clue.update_tiles()

    def move(self, orientation: str, direction: int) -> None:
        num_down: int = self.board.selected_tile.num_down
        num_across: int = self.board.selected_tile.num_across
        still_moving: bool = True
        while still_moving:
            if orientation == "across":
                num_across += direction
            else:
                num_down += direction
            if num_down < 0 or num_across < 0:
                self.move_to_next_clue(orientation, -1)
                still_moving = True
            elif num_down >= self.board.rows or num_across >= self.board.cols:
                self.move_to_next_clue(orientation, 1)
                still_moving = True
            if not self.board.in_bounds(num_down, num_across):
                still_moving = False
            else:
                try:
                    self.board.change_selected_tile(num_down, num_across)
                    still_moving = False
                except BaseException:
                    pass

    def move_to_next_clue(self, orientation: str, direction: int) -> None:
        if orientation == "across":
            current_clue = self.board.selected_tile.across_clue
        else:
            current_clue = self.board.selected_tile.down_clue
        if not current_clue:
            return
        clues_list: list[Clue] = [clue for clue in self.clues if clue.orientation == orientation]
        current_index: int = clues_list.index(current_clue)
        next_index: int = (current_index + direction) % len(clues_list)
        next_clue: Clue = clues_list[next_index]
        self.board.change_selected_tile(next_clue.num_down, next_clue.num_across)