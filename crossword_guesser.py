from crossword import Crossword, Clue
from copy import copy

class BadModelError(BaseException):
    pass

class Solver:
    """Class to represent the puzzle solver"""
    def __init__(self, puzzle: Crossword, has_solved: bool=False, guesses: list[str]=[]) -> None:
        self.puzzle = copy(puzzle)
        self.has_solved = has_solved
        self.guesses = guesses
        
    # given a crossword, solve for each tile in the puzzle
    def solve(self) -> None:
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
    def answer_clue(self, clue: Clue) -> str:
        return ""
        
    def accuracy(self) -> float:
        if self.has_solved:
            return self.puzzle.board.accuracy()
        else:
            return -1