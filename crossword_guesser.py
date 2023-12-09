from dataclasses import dataclass, field
from crossword import Crossword, Clue

class BadModelError(BaseException):
    pass

@dataclass
class Solver:
    """Class to represent the puzzle solver"""
    
    puzzle: Crossword
    has_solved: bool = False
    guesses: list[str] = field(default_factory=list)
        
    # given a crossword, solve for each tile in the puzzle
    def solve(self):
        solutions: dict[Clue, str] = {}
        for clue in self.puzzle.clues:
            sol: str = self.answer_clue(clue)
            solutions[clue] = sol
        for clue, sol in solutions.items():
            if len(clue.tiles) != len(sol):
                raise BadModelError("solution is wrong length!")
            for tile, char in zip(clue.tiles, sol):
                tile.fill(char)
        self.has_solved = True
    
    # given a clue, answer it!
    def answer_clue(self, clue) -> str:
        return ""
        
    # record the accuracy of the model as (total correct / total tiles)
    def accuracy(self):
        if not self.has_solved:
            return -1
        pass

    #  list all the errors in the puzzle
    def report_errors(self):
        if not self.has_solved:
            return []
        pass
    
