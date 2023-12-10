import config # api key

from crossword_parser import get_all_QA_pairs
from tiktoken import encoding_for_model
import os
import json

GPT_MODEL = "gpt-3.5-turbo"

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
        if len(results) > 2000:
            print(f"{len(string)} string split into {len(results)} strings.")
        return results

# collect data
QA_PAIR_FOLDER = "nyt_crosswords-master"
QA_list = get_all_QA_pairs(QA_PAIR_FOLDER)
QA_text = ""
for clue in QA_list:
    QA_text += f"{clue.question} ({len(clue.solution)} letters): {clue.solution}\n"
print(f"{len(QA_list)} QA pairs collected")
    
# split sections into chunks
MAX_TOKENS = 1600
QA_strings = split_string(QA_text, max_tokens=MAX_TOKENS)
print(f"{len(QA_list)} QA pairs split into {len(QA_strings)} strings.")

# embedding chunks in batches through the parallel processor
EMBEDDING_MODEL = "text-embedding-ada-002"
BATCH_SIZE = 10
QA_batches = []
for batch_start in range(0, len(QA_strings), BATCH_SIZE):
    batch_end = batch_start + BATCH_SIZE
    batch = QA_strings[batch_start:batch_end]
    QA_batches.append(batch)
    print(f"Batch {batch_start} to {batch_end-1}")
    
# save strings to jsonl file for parallel processing
# see: https://github.com/openai/openai-cookbook/blob/main/examples/api_request_parallel_processor.py
filename = "data/nyt_qa_requests_to_parallel_process.jsonl"
jobs = [{"model": EMBEDDING_MODEL, "input": QA_batch} for QA_batch in QA_batches]
with open(filename, "w") as f:
    for job in jobs:
        json_string = json.dumps(job)
        f.write(json_string + "\n")
print(f"QA pairs saved to {filename}.")

# run parallel processing
os.system("sh parallel_process.sh")

# completion = client.chat.completions.create(
#     model="gpt-3.5-turbo",
#     temperature=0.6,
#     messages=[
#         {"role": "system", "content": "You are an expert crossword solver. When given a crossword clue and the length of the clue's answer, you briefly answer the clue in all caps. Your response must be the length of the answer."},
#         {"role": "user", "content": "Clue: 'Car mentioned in 'Hotel California,' informally', Answer Length: 8 Letters"},
#     ]
# )