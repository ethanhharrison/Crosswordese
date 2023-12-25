import operator
from crossword_parser import parse_crossword_json
from crossword import Crossword, Clue

import pandas as pd
import pickle
from tqdm import tqdm

from embeddings_util import get_embedding, cosine_similarity
from embedding_customizer import embedding_multiplied_by_matrix

best_run_cache = "data/caches/best_run.pkl"
embedding_cache_file = (
    "data/caches/answer_embedding_cache.pkl"  # embeddings will be saved/loaded here
)
default_embedding_engine = (
    "text-embedding-ada-002"  # text-embedding-ada-002 is recommended
)


class BadModelError(BaseException):
    pass


class Solver:
    """Class to represent the puzzle solver"""

    def __init__(
        self,
        puzzle: Crossword,
        answer_embeddings: dict,
        matrix_filename: str = best_run_cache,
        guesses: dict[str, str] = {},
    ) -> None:
        with open(matrix_filename, "rb") as f:
            best_run = pickle.load(f)
        self.matrix = best_run["matrix"]

        answer_list = []
        custom_answer_embeddings = []
        # print("Customizing answer embeddings...")
        for key, value in tqdm(answer_embeddings.items()):
            answer_list.append(key[0])
            custom_answer_embeddings.append(
                embedding_multiplied_by_matrix(value, self.matrix)
            )
        print("Converting embeddings to dataframe...")
        self.df: pd.DataFrame = pd.DataFrame(
            {
                "text_1": answer_list,
                "text_1_embedding": answer_embeddings.values(),
                "text_1_embedding_custom": custom_answer_embeddings,
            }
        )
        self.puzzle = puzzle
        self.guesses = guesses

    # given a crossword, solve for each tile in the puzzle
    def solve(self) -> float:
        for clue in self.puzzle.clues:
            sol: str = self.find_closest_embeddings(clue.question, len(clue.tiles))
            self.guesses[clue.question] = sol
            print(f"{clue.question}: {sol}")
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
        engine: str = default_embedding_engine,
    ) -> str:
        question_embedding = get_embedding(question, engine)
        question_embedding = embedding_multiplied_by_matrix(
            question_embedding, self.matrix
        )
        similarities = {}
        for _, row in self.df.iterrows():
            if len(row["text_1"]) == length and row["text_1"] not in similarities:
                similarity = cosine_similarity(
                    row["text_1_embedding_custom"], question_embedding
                )
                similarities[row["text_1"]] = similarity
        similarities = sorted(
            similarities.items(), key=operator.itemgetter(1), reverse=True
        )
        for possible_answer in similarities[:k_closest]:
            text = possible_answer[0]
            if text.lower() not in question.lower():
                return text
        return similarities[0][0]


def main() -> None:
    try:
        with open(embedding_cache_file, "rb") as f:
            answer_embedding_cache = pickle.load(f)
    except FileNotFoundError:
        answer_embedding_cache = {}

    rows, cols, clues = parse_crossword_json("nyt_crosswords-master/2001/09/11.json")
    crossword = Crossword(rows, cols, clues)
    solver = Solver(crossword, answer_embedding_cache)
    print("Finished initializing solver!")

    accuracy = solver.solve()
    print("Accuracy:", accuracy)

if __name__ == "__main__":
    main()
