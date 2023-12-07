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
            
            
    def display_border(self, x_pos: int, y_pos: int, size: int):
        black_rect = pygame.Rect(x_pos, y_pos, size, size)
        yield pygame.Color("black"), black_rect
        if self.selected:
            gold_rect = pygame.Rect(x_pos + 2, y_pos + 2, size - 4, size - 4)
            yield pygame.Color(255, 217, 2), gold_rect
        elif self.highlighted:
            blue_rect = pygame.Rect(x_pos + 2, y_pos + 2, size - 4, size - 4)
            yield pygame.Color(167,216,254), blue_rect
        elif not self.blocked:
            white_rect = pygame.Rect(x_pos + 2, y_pos + 2, size - 4, size - 4)
            yield pygame.Color("white"), white_rect
    
    
    def display_current_entry(self, x_pos: int, y_pos: int, size: int, font):
        if self.current_entry != " ":
            text = font.render(self.current_entry, True, "black")
            text_rect = text.get_rect()
            text_rect.center = (x_pos + size // 2 - 1, y_pos + size // 2 + 1)
            yield text, text_rect
            
            
    def display_clue_number(self, number: int, x_pos: int, y_pos: int, font):
        text = font.render(str(number), True, "black")
        text_rect = text.get_rect()
        text_rect.topleft = (x_pos + 4, y_pos)
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
    position: tuple[int, int]
    tiles: list[Tile] = field(default_factory=list) 
    
    
    def update_tile_solutions(self) -> None:
        """Updates the solution for each tile of that clue"""
        if self.tiles == []:
            raise ValueError("No tiles connected to clue")
        for value, tile in zip(self.solution, self.tiles):
            print(self)
            print(self.position)
            print(tile.correct_entry, value)
            if tile.correct_entry == " " or tile.correct_entry == value:
                tile.assign_clue(self, self.orientation)
                tile.correct_entry = value
            else:
                raise InvalidPuzzleError("Puzzle has conflicting clues")
    
    
    def highlight_clue(self) -> None:
        if any(tile.selected for tile in self.tiles):
            print(self)
            for tile in self.tiles:
                tile.highlighted = True
        else:
            for tile in self.tiles:
                tile.highlighted = False
    
    
    def __str__(self) -> str:
        return f"{self.question} -> {self.solution}"
    

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
        return [[Tile(False) for _ in range(cols)] for _ in range(rows)]
    
    
    def assign_clues_to_tiles(self) -> None:
        """Assigns clues to tiles in the grid then updates the tiles' solutionsxs"""
        if self.clues is None:
            return
        for clue in self.clues:
            num_down, num_across = clue.position[0], clue.position[1]
            sol_size = len(clue.solution)
            if clue.orientation == "across":
                clue.tiles = [self.get_tile(num_down, num_across+i) for i in range(sol_size)]
            if clue.orientation == "down":
                clue.tiles = [self.get_tile(num_down+i, num_across) for i in range(sol_size)]
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
                x_pos = padding + tile_size * j
                y_pos = padding + tile_size * i
                tile_display = tile.display_border(x_pos, y_pos, tile_size)
                text_display = tile.display_current_entry(x_pos, y_pos, tile_size, font)
                yield tile_display, text_display
                
    
    def __str__(self) -> str:
        output = ""
        for row in self.tiles:
            for tile in row:
                output += str(tile)
            output += "\n"
        return output
