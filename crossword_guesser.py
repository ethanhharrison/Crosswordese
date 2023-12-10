from crossword import Crossword, Clue
from copy import copy
import json
import pandas as pd

class BadModelError(BaseException):
    pass

class Solver:
    """Class to represent the puzzle solver"""
    def __init__(self, 
        puzzle: Crossword, 
        has_solved: bool=False, 
        guesses: list[str]=[]
    ) -> None:
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
    
def retrieve_embeddings(file_path: str) -> pd.DataFrame:
    strings = []
    responses = []
    with open(file_path) as file:
        for line in file:
            string, response = json.loads(line)
            strings.extend(string["input"])
            embeddings = [e["embedding"] for e in response["data"]]
            responses.extend(embeddings)
    df = pd.DataFrame({"text": strings, "embedding": responses})
    return df

df = retrieve_embeddings("data/nyt_qa_requests_to_parallel_process_results.jsonl")

SAVE_PATH = "data/qa_pairs.csv"
df.to_csv(SAVE_PATH, index=False)

# To get the client to run, add an OPENAI_API_KEY variable to your environment.
# I am doing so with a config.py file which sets os.environ["OPENAI_API_KEY"] to my key