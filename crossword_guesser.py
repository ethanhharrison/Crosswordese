import operator
from config import OPENAI_API_KEY
from crossword_parser import parse_crossword_json
from crossword import Crossword, Clue
import pandas as pd
import openai
import pickle
import ast
from embeddings_util import get_embedding, cosine_similarity
from embedding_customizer import embedding_multiplied_by_matrix

best_run_cache = "data/best_run.pkl"
qa_dataset_file = "data/qa_dataset.pkl"
answer_embedding_cache = "data/answer_embeddings.pkl"  # embeddings will be saved/loaded here
default_embedding_engine = "text-embedding-ada-002"  # text-embedding-ada-002 is recommended

class BadModelError(BaseException):
    pass


class Solver:
    """Class to represent the puzzle solver"""

    def __init__(
        self, 
        puzzle: Crossword, 
        df_filename: str = qa_dataset_file, 
        matrix_filename: str = best_run_cache, 
        guesses: dict[str, str] = {}
    ) -> None:
        self.puzzle = puzzle
        self.guesses = guesses
        with open(df_filename, "rb") as f:
            df = pickle.load(f)
            df = df[["text_1", "text_1_embedding"]]
            df["text_1_embedding"] = df["text_1_embedding"].apply(ast.literal_eval)
            
        with open(matrix_filename, "rb") as f:
            best_run = pickle.load(f)
            self.matrix = best_run["matrix"]
            df["text_1_embedding_custom"] = df["text_1_embedding"].apply(
                lambda x: embedding_multiplied_by_matrix(x, self.matrix) # type: ignore
            ) # type: ignore

        self.df: pd.DataFrame = df # type: ignore

    # given a crossword, solve for each tile in the puzzle
    def solve(self) -> float:
        for clue in self.puzzle.clues:
            sol: str = self.answer_clue(clue)
            question: str = f"{clue.question} ({len(clue.tiles)} letters):"
            self.guesses[question] = sol
            print(f"{question} {sol}")
            for tile, char in zip(clue.tiles, sol):
                tile.fill(char)
        return self.accuracy()

    # given a clue, answer it!
    def answer_clue(self, clue: Clue):
        return ""

    def accuracy(self) -> float:
        return self.puzzle.board.accuracy()

    def find_closest_embeddings(
        self, 
        question: str,
        length: int, 
        k_closest: int = 10,
        engine: str = default_embedding_engine
    ) -> list[tuple]:
        question_embedding = get_embedding(question, engine)
        question_embedding = embedding_multiplied_by_matrix(question_embedding, self.matrix)
        print(self.df["text_1_embedding_custom"][0].size)
        print(question_embedding.size)
        similarities = {}
        for _, row in self.df.iterrows():
            if len(row["text_1"]) == length and row["text_1"] not in similarities:
                similarity = cosine_similarity(row["text_1_embedding_custom"], question_embedding)
                similarities[row["text_1"]] = similarity
        similarities = sorted(similarities.items(), key=operator.itemgetter(1), reverse=True)
        return similarities[:k_closest]
    

def main() -> None:
    rows, cols, clues = parse_crossword_json("nyt_crosswords-master/2001/09/11.json")
    crossword = Crossword(rows, cols, clues)
    solver = Solver(crossword)
    print("Finished initializing solver!")
    best_answers = solver.find_closest_embeddings("Abscond with", 5)
    
    print(best_answers)
    # solver.solve()

if __name__ == "__main__":
    main()
