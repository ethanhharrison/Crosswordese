import config   # api key

from create_embeddings import num_tokens
from crossword import Crossword, Clue
from copy import copy
from scipy import spatial
import openai
import json
import ast
import pandas as pd
import numpy as np

GPT_MODEL = "gpt-3.5-turbo"
EMBEDDING_MODEL = "text-embedding-ada-002"
EMBEDDING_PATH = "data/nyt_qa_requests_to_parallel_process_results.jsonl"
SAVE_PATH = "data/qa_pairs.csv"

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
        for batch_num, line in enumerate(file):
            try:
                string, response = json.loads(line)
                print(f"{batch_num}:", string["input"][0])
                embeddings = [e["embedding"] for e in response["data"]]
                assert len(string["input"]) == len(embeddings)
                strings.extend(string["input"])
                responses.extend(embeddings)
            except BaseException as be:
                print(be)
                break
    print(len(strings), len(responses))
    df = pd.DataFrame({"text": strings, "embedding": responses})
    return df
    
# search function which takes the query and the dataframe to rank the most similar embeddings
# see: https://cookbook.openai.com/examples/question_answering_using_embeddings
def strings_ranked_by_relatedness(
    query: str,
    file_path: str,
    relatedness_fn=lambda x, y: 1 - spatial.distance.cosine(x, y),
    top_n: int = 100,
) -> tuple[list[str], list[float]]:
    """Returns a list of strings and relatedness, sorted from most related to least"""
    strings_and_relatedness = []
    csv_iterator = pd.read_csv(file_path, 
                               iterator=True, 
                               chunksize=100000, 
                               converters={"embedding": ast.literal_eval},
                               dtype={"text": str})
    for i, chunk in enumerate(csv_iterator):
        print("Chunk Number:", i)
        query_embedding_response = openai.embeddings.create(
            model=EMBEDDING_MODEL,
            input=query
        )
        query_embedding = query_embedding_response.data[0].embedding    
        strings_and_relatedness += [
            (row["text"], relatedness_fn(query_embedding, row["embedding"]))
            for i, row in chunk.iterrows()
        ]
    strings_and_relatedness.sort(key=lambda x: x[1], reverse=True)
    strings, relatedness = zip(*strings_and_relatedness)
    return strings[:top_n], relatedness[:top_n]
        
def query_message(
    query: str,
    file_path: str,
    model: str,
    token_budget: int
) -> str:
    """Return a message for GPT, with relevant source texts pulled from a dataframe."""
    strings, relatedness = strings_ranked_by_relatedness(query, file_path, top_n=1)
    introduction = 'Use the below clues and their respective answers to help you solve the subsequent clue.'
    question = f"\n\nClue: {query}"
    message = introduction
    for string in strings:
        next_clue_set = f'\n\nClue Set:"""\n{string}\n"""'
        if (num_tokens(message + next_clue_set + question, model=model) > token_budget):
            print("WARNING: Length of clue sets exceeded token budget.")
            break
        else:
            message += next_clue_set
    return message + question
        
        
def ask(
    query: str,
    file_path: str,
    model: str = GPT_MODEL,
    token_budget: int = 4096 - 500,
    print_message: bool = False
) -> str:
    """Answers a query using GPT and a dataframe of relevant texts and embeddings."""
    message = query_message(query, file_path, model=model, token_budget=token_budget)
    if print_message:
        print(message)
    messages = [
        {"role": "system", "content": "You are an expert crossword solver. When given a crossword clue and the length of the clue's answer, you briefly answer the clue in all caps. Your response must be the length of the answer."},
        {"role": "user", "content": message}
    ]
    response = openai.chat.completions.create(
        model=model,
        messages=messages,  # type: ignore
        temperature=0
    )
    response_message = response.choices[0].message.content
    return response_message # type: ignore
        
def main() -> None:
    # example question
    question = "Little Rascals (6 letters)"
    strings_ranked_by_relatedness(question, SAVE_PATH) # need to improve speed since data file is like 25GB LOL
    
if __name__ == "__main__":
    main()