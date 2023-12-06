from dataclasses import dataclass


@dataclass
class Clue:
    number: int
    question: str
    solution: str
    orientation: str


@dataclass
class Tile:
    """Class for keeping track of a game tile"""
    across_clue: Clue
    down_clue: Clue
    blocked: bool
    correct_entry: str
    current_entry: str = " "
    empty: bool = True
    
    
    def is_correct(self) -> bool:
        return self.blocked or self.correct_entry == self.current_entry
    
    
    def fill(self, value) -> bool:
        if len(value) > 1:
            print("Value is too long")
            return False
        else:
            self.current_entry = value
            self.empty = True
            return True
        
    def remove(self):
        if self.empty:
            self.current_entry = " "
            self.empty = False
            
            
    def __str__(self) -> str:
        return f"[{self.current_entry}]"
    

# Create the board
@dataclass
class GameBoard:
    """Class for creating the game board"""
    tiles: list[list[Tile]]
    clues: list[Clue]
    selected_tile: Tile = None
    
    
    def size(self):
        return len(self.tiles[0])
        
    
    def is_complete(self):
        """Check if board is complete"""
        for row in self.tiles:
            if any([not tile.is_correct() for tile in row]):
                return False
        return True
    
    
    def select_tile(self, x, y) -> bool:
        if x < 0 or y < 0 or x >= self.size() or y >= self.size():
            print("Invalid tile position")
            return False
        else:
            self.selected_tile = self.tiles[x][y]
            return True
            
                 
    def fill_tile(self, value) -> bool:
        return self.selected_tile.fill(value)
    
    
    def __str__(self) -> str:
        output = ""
        for row in self.tiles:
            for tile in row:
                output += str(tile)
            output += "\n"
        return output
                

