from config import OPENAI_API_KEY
from crossword_parser import parse_crossword_json
from database_utils import query_database
from crossword import Crossword, Clue
import logging
import openai


class BadModelError(BaseException):
    pass


class Solver:
    """Class to represent the puzzle solver"""

    def __init__(
        self, puzzle: Crossword, guesses: dict[str, str] = {}
    ) -> None:
        self.puzzle = puzzle
        self.guesses = guesses

    # given a crossword, solve for each tile in the puzzle
    def solve(self) -> None:
        solutions: dict[Clue, str] = {}
        for clue in self.puzzle.clues:
            sol: str = self.answer_clue(clue)
            solutions[clue] = sol
        for clue, sol in solutions.items():
            for tile, char in zip(clue.tiles, sol):
                tile.fill(char)
        self.has_solved = True

    # given a clue, answer it!
    def answer_clue(self, clue: Clue) -> str:
        question = f"{clue.question} ({len(clue.tiles)} letters):"
        guesses = ask(question).splitlines()
        truncated_guesses = []
        for guess in guesses:
            guess = guess[3:]
            if len(guess) == len(clue.tiles):
                self.guesses[question] = guess
                return self.guesses[question]
            if len(guess) > len(clue.tiles):
                truncated_guesses.append(guess[:len(clue.tiles)])
        if not truncated_guesses:
            raise BadModelError("No valid guesses provided!")
        self.guesses[question] = truncated_guesses[0]
        return self.guesses[question]

    def accuracy(self) -> float:
        if self.has_solved:
            return self.puzzle.board.accuracy()
        else:
            return -1

# Prompt engineering WOOOOOOO
# This can certainly be improved: https://betterprogramming.pub/enhancing-chatgpt-with-infinite-external-memory-using-vector-database-and-chatgpt-retrieval-plugin-b6f4ea16ab8
# A possible step foward is adding metadata to each clue that we ask chatgpt to categorize
# beforehand, then use the categorized data for the relevant clue retrieval
def apply_prompt_template(question: str) -> str:
    prompt = f"""
    You are an expert crossword solver. When provided a crossword clue and the length 
    of the clue's answer, you briefly give your five best guesses for the clue in the format:
        1. GUESSONE
        2. GUESSTWO
        3. GUESSTHREE
        4. GUESSFOUR
        5. GUESSFIVE
    When answering, all of your guesses should be in capital letters and should be the same
    number of letters that the clue says. 
    
    Use the provided clue-answer pairs above to help answer this next clue.
    
    New Clue: {question}
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
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages, # type: ignore
        max_tokens=1024,
        temperature=0.5,  # High temperature leads to a more creative response.
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

def main() -> None:
    openai.api_key = OPENAI_API_KEY
    logging.basicConfig(level=logging.WARNING,
                        format="%(asctime)s %(levelname)s %(message)s")
    rows, cols, clues = parse_crossword_json("nyt_crosswords-master/2001/09/11.json")
    crossword = Crossword(rows, cols, clues)
    solver = Solver(crossword)
    for clue in solver.puzzle.clues:
        question = f"{clue.question} ({len(clue.tiles)} letters):"
        solver.answer_clue(clue)
        print(f"{question} {solver.guesses[question]}")

if __name__ == "__main__":
    main()
