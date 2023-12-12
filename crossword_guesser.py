from sched import scheduler
import config   # api key

from create_embeddings import num_tokens
from crossword import Crossword, Clue
from copy import copy
from scipy import spatial
import pandas as pd
import dask.dataframe as dd
import dask
import openai
import json
import ast

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
    
def retrieve_embeddings(file_path: str = EMBEDDING_PATH) -> pd.DataFrame:
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
    df: pd.DataFrame,
    relatedness_fn=lambda x, y: 1 - spatial.distance.cosine(x, y),
    top_n: int = 100,
) -> tuple[list[str], list[float]]:
    """Returns a list of strings and relatedness, sorted from most related to least"""
    print("Searching for most related clues")
    query_embedding_response = openai.embeddings.create(
        model=EMBEDDING_MODEL,
        input=query
    )
    query_embedding = query_embedding_response.data[0].embedding    
    strings_and_relatedness = [
        (row["text"], relatedness_fn(query_embedding, row["embedding"]))
        for i, row in df.iterrows()
    ]
    strings_and_relatedness.sort(key=lambda x: x[1], reverse=True)
    strings, relatedness = zip(*strings_and_relatedness)
    return strings[:top_n], relatedness[:top_n]
        
def query_message(
    query: str,
    df: pd.DataFrame,
    model: str,
    token_budget: int
) -> str:
    """Return a message for GPT, with relevant source texts pulled from a dataframe."""
    print("Querying message")
    strings, relatedness = strings_ranked_by_relatedness(query, df, top_n=10)
    introduction = "Use the below clues and their respective answers to help you solve the subsequent clue."
    question = f"\n\n{query}"
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
    df: pd.DataFrame,
    model: str = GPT_MODEL,
    token_budget: int = 4096 - 500,
    print_message: bool = False
) -> str:
    """Answers a query using GPT and a dataframe of relevant texts and embeddings."""
    print("Asking question")
    # message = query_message(query, df, model=model, token_budget=token_budget)
    # if print_message:
    #     print(message)
    messages = [
        {"role": "system", 
         "content": """You are an expert crossword solver. When given a crossword clue and the length 
                       of the clue's answer, you briefly give your FIVE best guesses for the clue. Your 
                       guesses MUST be the length of the answer and should be in all caps."""},
        {"role": "user", "content": query}
    ]
    response = openai.chat.completions.create(
        model=model,
        messages=messages,                                                                                  # type: ignore
        temperature=0.4
    )
    response_message = response.choices[0].message.content
    return response_message                                                                                 # type: ignore
     
def try_literal_eval(row):
    try:
        return ast.literal_eval(row)
    except BaseException:
        pass
        
def main() -> None:
    ddf = dd.read_csv(SAVE_PATH, blocksize="25MB",                                                          # type: ignore
                                 dtype={"text": str},
                                 engine="python",
                                 on_bad_lines="warn")
    ddf["embedding"] = ddf["embedding"].apply(try_literal_eval, meta=('embedding', 'object'))
    ddf = ddf.dropna()
    # example question
    question = """Metric weight units (6 Letters)"""
    repsonse = ask(question, ddf)
    print(repsonse)
    
if __name__ == "__main__":
    main()