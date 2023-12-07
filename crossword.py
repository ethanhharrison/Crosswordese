from __future__ import annotations
from asyncore import close_all
from dataclasses import dataclass, field
from typing import Optional
import string


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
    down_clue: Optional[Clue] = None
    across_clue: Optional[Clue] = None
    
        
    def assign_clue(self, clue: Clue, orientation: str) -> None:
        """Attach tile to an associated clue"""
        if orientation == "down":
            self.down_clue = clue
        elif orientation == "across":
            self.across_clue = clue
            
    
    def display_clues(self):
        """Display the clues for the player"""
        if self.down_clue:
            print("Down:", self.down_clue)
        if self.across_clue:
            print("Across:", self.across_clue)
    
    
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
            if tile.correct_entry == " " or tile.correct_entry == value:
                tile.assign_clue(self, self.orientation)
                tile.correct_entry = value
            else:
                raise InvalidPuzzleError("Puzzle has conflicting clues")
    
    
    def __str__(self) -> str:
        return f"{self.question} -> {self.solution}"
    

class GameBoard:
    """Class for creating the game board"""
    def __init__(self, cols: int, rows: int, clues: list[Clue]) -> None:
        self.cols = cols
        self.rows = rows
        self.clues = clues
        self.tiles = self.make_tile_grid(cols, rows)
        self.selected_tile = self.get_tile(0, 0)
    
    
    def make_tile_grid(self, cols: int, rows: int) -> list[list[Tile]]:
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
            elif clue.orientation == "down":
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
        self.selected_tile = new_tile
            
                 
    def update_tile_entry(self, value: str) -> None:
        """Adds or removes value to the selected tile"""
        if value == "delete":
            self.selected_tile.remove()
        else:
            self.selected_tile.fill(value)
            
    
    def __str__(self) -> str:
        output = ""
        for row in self.tiles:
            for tile in row:
                output += str(tile)
            output += "\n"
        return output
