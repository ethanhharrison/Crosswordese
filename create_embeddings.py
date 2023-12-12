from crossword_parser import get_all_QA_pairs
from tiktoken import encoding_for_model
import os
import json
import pandas as pd

QA_PAIR_FOLDER = "nyt_crosswords-master"
GPT_MODEL = "gpt-3.5-turbo"
EMBEDDING_MODEL = "text-embedding-ada-002"
EMBEDDING_PATH = "data/nyt_qa_requests_to_parallel_process_results.jsonl"
SAVE_PATH = "data/qa_pairs.csv"
MAX_TOKENS = 1600
BATCH_SIZE = 40


# Recursively split QA dataset to smaller sections so GPT can read it
# see: https://cookbook.openai.com/examples/embedding_wikipedia_articles_for_search
def num_tokens(text: str, model: str = GPT_MODEL) -> int:
    """Return the number of tokens in a string."""
    encoding = encoding_for_model(model)
    return len(encoding.encode(text))


def truncated_string(
    string: str, model: str, max_tokens: int, print_warning: bool = True
) -> str:
    """Truncate a string to a maximum number of tokens"""
    encoding = encoding_for_model(model)
    encoded_string = encoding.encode(string)
    truncated_string = encoding.decode(encoded_string[:max_tokens])
    if print_warning and len(encoded_string) > max_tokens:
        print(
            f"Warning: Truncated string from {len(encoded_string)} tokens to {max_tokens} tokens."
        )
    return truncated_string


def split_string_by_lines(
    string: str, lines_per_split: int = 5, max_tokens: int = 1000, model=GPT_MODEL
):
    split_string = string.split("\n")
    all_splits = []
    i = 0
    split_size = lines_per_split
    while i < len(split_string) - split_size:
        combined_string = "\n".join(split_string[i : i + split_size])
        if num_tokens(combined_string) <= max_tokens:
            all_splits.append(combined_string)
            i += split_size
            split_size = lines_per_split
        elif split_size == 1:  # this should basically never happen
            truncated = truncated_string(
                combined_string, model=model, max_tokens=max_tokens
            )
            all_splits.append(truncated)
        else:
            split_size -= 1
    return all_splits


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


def main() -> None:
    # collect data
    QA_list = get_all_QA_pairs(QA_PAIR_FOLDER)
    QA_text = ""
    for clue in QA_list:
        QA_text += f"{clue.question} ({len(clue.solution)} letters): {clue.solution}\n"
    print(f"{len(QA_list)} QA pairs collected")

    # split sections into chunks
    QA_strings = split_string_by_lines(
        QA_text, lines_per_split=20, max_tokens=MAX_TOKENS
    )
    print(f"{len(QA_list)} QA pairs split into {len(QA_strings)} strings.")
    print(num_tokens(QA_strings[0]))

    # embedding chunks in batches through the parallel processor
    QA_batches = []
    for batch_start in range(0, len(QA_strings), BATCH_SIZE):
        batch_end = batch_start + BATCH_SIZE
        batch = QA_strings[batch_start:batch_end]
        QA_batches.append(batch)
        print(f"Batch {batch_start} to {batch_end-1}")

    # save strings to jsonl file for parallel processing
    # see: https://github.com/openai/openai-cookbook/blob/main/examples/api_request_parallel_processor.py
    filename = EMBEDDING_PATH
    jobs = [{"model": EMBEDDING_MODEL, "input": QA_batch} for QA_batch in QA_batches]
    with open(filename, "w") as f:
        for job in jobs:
            json_string = json.dumps(job)
            f.write(json_string + "\n")
    print(f"QA pairs saved to {filename}.")

    # run parallel processing
    os.system("sh parallel_process.sh")

    # save embeddings as csv
    df = retrieve_embeddings()
    df.to_csv(SAVE_PATH, index=False)


if __name__ == "__main__":
    main()
