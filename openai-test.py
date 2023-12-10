from lzma import MODE_NORMAL
from openai import OpenAI
from crossword_parser import get_all_QA_pairs
from tiktoken import encoding_for_model
import config

GPT_MODEL = "gpt-3.5-turbo"
QA_PAIR_FOLDER = "nyt_crosswords-master"

# To get the client to run, add an OPENAI_API_KEY variable to your environment.
# I am doing so with a config.py file which sets os.environ["OPENAI_API_KEY"]
# to my key
client = OpenAI()

# Recursively split QA dataset to smaller sections so GPT can read it
# see: https://cookbook.openai.com/examples/embedding_wikipedia_articles_for_search
def num_tokens(text: str, model: str = GPT_MODEL) -> int:
    """Return the number of tokens in a string."""
    encoding = encoding_for_model(model)
    return len(encoding.encode(text))

def halved_by_delimiter(string: str, delimiter: str = "\n") -> list[str]:
    """Split a string in two, on a delimiter"""
    chunks = string.split(delimiter)
    if len(chunks) == 1:
        return [string, ""]
    elif len(chunks) == 2:
        return chunks
    else:
        split_idx = len(chunks) // 2
        left = delimiter.join(chunks[:split_idx])
        right = delimiter.join(chunks[split_idx:])
        return [left, right]
    
def truncated_string(
    string: str,
    model: str,
    max_tokens: int,
    print_warning: bool = True
) -> str:
    """Truncate a string to a maximum number of tokens"""
    encoding = encoding_for_model(model)
    encoded_string = encoding.encode(string)
    truncated_string = encoding.decode(encoded_string[:max_tokens])
    if print_warning and len(encoded_string) > max_tokens:
        print(f"Warning: Truncated string from {len(encoded_string)} tokens to {max_tokens} tokens.")
    return truncated_string

def split_string(
    string: str,
    max_tokens: int = 1000,
    model: str = GPT_MODEL,
    max_recursion: int = 15
) -> list[str]:
    num_tokens_in_string = num_tokens(string)
    # if length is fine, return string
    if num_tokens_in_string <= max_tokens:
        return [string]
    # if recursion hasn't found a split after X iterations, just truncate
    elif max_recursion == 0:
        return [truncated_string(string, model=model, max_tokens=max_tokens)]
    # otherwise, split in half and perform recursion
    else:
        left, right = halved_by_delimiter(string, delimiter="\n")
        results = []
        for half in [left, right]:
            half_strings = split_string(
                half,
                max_tokens=max_tokens,
                model=model,
                max_recursion=max_recursion-1
            )
            results.extend(half_strings)
        print(f"{len(string)} string split into {len(results)} strings.")
        return results

# collect data
print("collecting data...")
QA_list = get_all_QA_pairs(QA_PAIR_FOLDER)
QA_text = ""
for clue in QA_list:
    QA_text += f"{clue.question} ({len(clue.solution)} letters): {clue.solution}\n"
print(f"{len(QA_list)} QA pairs collected")
    
# split sections into chunks
print("splitting data...")
MAX_TOKENS = 1600
QA_strings = split_string(QA_text, max_tokens=MAX_TOKENS)
print(f"{len(QA_list)} QA pairs split into {len(QA_strings)} strings.")

# completion = client.chat.completions.create(
#     model="gpt-3.5-turbo",
#     temperature=0.6,
#     messages=[
#         {"role": "system", "content": "You are an expert crossword solver. When given a crossword clue and the length of the clue's answer, you briefly answer the clue in all caps. Your response must be the length of the answer."},
#         {"role": "user", "content": "Clue: 'Car mentioned in 'Hotel California,' informally', Answer Length: 8 Letters"},
#     ]
# )