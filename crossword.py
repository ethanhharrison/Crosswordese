from dataclasses import dataclass
from typing import Optional


@dataclass
class Clue:
    number: int
    question: str
    solution: str
    orientation: str
    
    
    def connect_clues(self, other_clues):
        self.connected_clues = other_clues


@dataclass
class Tile:
    """Class for keeping track of a game tile"""
    blocked: bool
    correct_entry: str
    current_entry: str = " "
    empty: bool = True
    across_clue: Optional[Clue] = None
    down_clue: Optional[Clue] = None
    
    
    def is_correct(self) -> bool:
        """Checks if the tile is correctly filled in"""
        return self.blocked or self.correct_entry == self.current_entry
    
    
    def fill(self, value: str) -> bool:
        """Fills the tile's current entry with the given value"""
        if self.blocked:
            print("Cannot fill blocked tile")
            return False
        if len(value) > 1:
            print("Value is too long")
            return False
        else:
            self.current_entry = value
            self.empty = True
            return True
        
    def remove(self) -> bool:
        """Removes the tile's current entry"""
        if self.empty:
            self.current_entry = " "
            self.empty = False
        return True
            
            
    def __str__(self) -> str:
        if self.blocked:
            return "[/]"
        else:
            return f"[{self.current_entry}]"
    

# Create the board
@dataclass
class GameBoard:
    """Class for creating the game board"""
    tiles: list[list[Tile]]
    clues: Optional[list[Clue]] = None
    
    
    def assign_clues_to_tiles(self):
        pass
    
    
    def size(self):
        """The size of one axis of the board"""
        return len(self.tiles[0])
        
    
    def is_complete(self):
        """Check if board is complete"""
        for row in self.tiles:
            if any([not tile.is_correct() for tile in row]):
                return False
        return True
    
    
    def select_tile(self, x: int, y: int) -> bool:
        """Given the x and y coordinates, selects a tile on the board"""
        if x < 0 or y < 0 or x >= self.size() or y >= self.size():
            print("Invalid tile position")
            return False
        elif self.tiles[x][y].blocked:
            print("Cannot select a blocked tile")
            return False
        else:
            self.selected_tile = self.tiles[x][y]
            return True
            
                 
    def update_tile(self, value: str) -> bool:
        """Adds or removes value to the selected tile"""
        if value == "delete":
            return self.selected_tile.remove()
        else:
            return self.selected_tile.fill(value)
    
    
    def __str__(self) -> str:
        output = ""
        for row in self.tiles:
            for tile in row:
                output += str(tile)
            output += "\n"
        return output
