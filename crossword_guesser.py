from config import OPENAI_API_KEY
from create_embeddings import EMBEDDING_MODEL, GPT_MODEL, SAVE_PATH, num_tokens
from database_utils import query_database
from crossword import Crossword, Clue
from copy import copy
from scipy import spatial
import logging
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

def apply_prompt_template(question: str) -> str:
    prompt = f"""
    You are an expert crossword solver. When given a crossword clue and the length 
    of the clue's answer, you briefly give your FIVE best guesses for the clue. 
    
    Your guesses MUST be the length of the answer and should be in all caps. Now, please
    answer this clue:
    
    Use the provided clue-answer pairs above to help answer this next clue.
    
    {question}
    """
    return prompt

def call_chatgpt_api(question: str, chunks: list[str]):
    """
    Call chatgpt api with user's question and retrieved chunks.
    """
    # Send a request to the GPT-3 API
    messages = list(
        map(lambda chunk: {
            "role": "user",
            "content": chunk
        }, chunks))
    question = apply_prompt_template(question)
    messages.append({"role": "user", "content": question})
    for d in messages:
        print(d["content"])
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages, # type: ignore
        max_tokens=1024,
        temperature=0.3,  # High temperature leads to a more creative response.
    )
    return response


def ask(user_question: str) -> str:
    """
    Handle user's questions.
    """
    # Get chunks from database.
    chunks_response = query_database(user_question)
    chunks = []
    for result in chunks_response["results"]:
        for inner_result in result["results"]:
            text = inner_result["text"].split()
            clue = ""
            for word in text:
                clue += " " + word
                if len(word) >= 3 and word.isupper():
                    chunks.append(clue)
                    clue = ""
    
    logging.info("User's questions: %s", user_question)
    logging.info("Retrieved chunks: %s", chunks)
    
    response = call_chatgpt_api(user_question, chunks)
    logging.info("Response: %s", response)
    
    return response.choices[0].message.content # type: ignore


def try_literal_eval(row):
    try:
        return ast.literal_eval(row)
    except BaseException:
        pass


def main() -> None:
    user_query = input("Enter Clue:")
    openai.api_key = OPENAI_API_KEY
    logging.basicConfig(level=logging.WARNING,
                        format="%(asctime)s %(levelname)s %(message)s")
    print(ask(user_query))


if __name__ == "__main__":
    main()
