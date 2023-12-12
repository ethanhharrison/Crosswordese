import config  # api key

from create_embeddings import EMBEDDING_MODEL, GPT_MODEL, SAVE_PATH, num_tokens
from crossword import Crossword, Clue
from copy import copy
from scipy import spatial
import pandas as pd
import dask.dataframe as dd
import openai
import ast


class BadModelError(BaseException):
    pass


class Solver:
    """Class to represent the puzzle solver"""

    def __init__(
        self, puzzle: Crossword, has_solved: bool = False, guesses: list[str] = []
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


# search function which takes the query and the dataframe to rank the most similar embeddings
# see: https://cookbook.openai.com/examples/question_answering_using_embeddings
def strings_ranked_by_relatedness(
    query: str,
    df: pd.DataFrame,
    relatedness_fn=lambda x, y: 1 - spatial.distance.cosine(x, y),
    top_n: int = 100,
) -> tuple[list[str], list[float]]:
    """Returns a list of strings and relatedness, sorted from most related to least"""
    print("Searching for most related clues")
    query_embedding_response = openai.embeddings.create(
        model=EMBEDDING_MODEL, input=query
    )
    query_embedding = query_embedding_response.data[0].embedding
    strings_and_relatedness = []
    for i, row in df.iterrows():
        relatedness = relatedness_fn(query_embedding, row["embedding"])
        print(f"Row {i} relatedness: {relatedness}")
        strings_and_relatedness.append((row["text"], relatedness))
    strings_and_relatedness.sort(key=lambda x: x[1], reverse=True)
    strings, relatedness = zip(*strings_and_relatedness)
    return strings[:top_n], relatedness[:top_n]


def query_message(query: str, df: pd.DataFrame, model: str, token_budget: int) -> str:
    """Return a message for GPT, with relevant source texts pulled from a dataframe."""
    strings, relatedness = strings_ranked_by_relatedness(query, df, top_n=10)
    print("Querying message")
    introduction = "Use the below clues and their respective answers to help you solve the subsequent clue."
    question = f"\n\n{query}"
    message = introduction
    for string in strings:
        next_clue_set = f'\n\nClue Set:"""\n{string}\n"""'
        if num_tokens(message + next_clue_set + question, model=model) > token_budget:
            print("WARNING: Length of clue sets exceeded token budget.")
            break
        else:
            message += next_clue_set
    return message + question


def ask(
    query: str,
    df: pd.DataFrame,
    model: str = GPT_MODEL,
    token_budget: int = 4096 - 500,
    print_message: bool = False,
) -> str:
    """Answers a query using GPT and a dataframe of relevant texts and embeddings."""
    message = query_message(query, df, model=model, token_budget=token_budget)
    if print_message:
        print(message)
    messages = [
        {
            "role": "system",
            "content": """You are an expert crossword solver. When given a crossword clue and the length 
                       of the clue's answer, you briefly give your FIVE best guesses for the clue. Your 
                       guesses MUST be the length of the answer and should be in all caps.""",
        },
        {"role": "user", "content": message},
    ]
    print("Asking question")
    response = openai.chat.completions.create(
        model=model, messages=messages, temperature=0.4  # type: ignore
    )
    response_message = response.choices[0].message.content
    return response_message  # type: ignore


def try_literal_eval(row):
    try:
        return ast.literal_eval(row)
    except BaseException:
        pass


def main() -> None:
    ddf = dd.read_csv(  # type: ignore
        SAVE_PATH,
        dtype={"text": str},
        engine="python",
        on_bad_lines="warn",
    )
    ddf["embedding"] = ddf["embedding"].apply(
        try_literal_eval, meta=("embedding", "object")
    )
    ddf = ddf.dropna()
    # example question
    question = """Paper size longer than letter (5 Letters)"""
    repsonse = ask(question, ddf, print_message=True)
    print(repsonse)


if __name__ == "__main__":
    main()
