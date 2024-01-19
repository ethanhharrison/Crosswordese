import pandas as pd
import pickle
import openai
import os

from embedding_customizer import embed_all_answers

ANSWER_EMBEDDING_CACHE_FILE = "data/caches/answer_embedding_cache.pkl"
QUESTION_EMBEDDING_CACHE_FILE = "data/caches/question_embedding_cache.pkl"
EMBEDDING_MODEL = "text-embedding-ada-002"


def retrieve_clue_embeddings(df: pd.DataFrame):
    questions = list(df["Clue"].unique())

    questions = list(map(str, questions))

    questions.sort()

    embed_all_answers(questions, {}, type="question")


def merge_embeddings(folder_name: str, cache_path: str, type: str) -> None:
    merged_cache = {}
    for f in os.listdir(folder_name):
        if type in f:
            file_name = os.path.join(folder_name, f)
            with open(file_name, "rb") as file:
                cache = pickle.load(file)
                merged_cache.update(cache)
    with open(cache_path, "wb") as file:
        pickle.dump(merged_cache, file)


def retrieve_embedding_from_cache(string, cache, type):
    if (string, EMBEDDING_MODEL) in cache:
        return cache[(string, EMBEDDING_MODEL)]
    else:
        print(f"{string} not found in {type} cache.")


def main():
    print("Loading data...")
    df = pd.read_csv("data/dataframes/unique_qa_pairs.csv")
    with open(ANSWER_EMBEDDING_CACHE_FILE, "rb") as f:
        unique_answer_embeddings = pickle.load(f)
    with open(QUESTION_EMBEDDING_CACHE_FILE, "rb") as f:
        unique_question_embeddings = pickle.load(f)

    print("Combining rows...")
    answers = df["Answer"].to_list()
    answer_embeddings = list(
        map(
            lambda a: retrieve_embedding_from_cache(
                str(a), unique_answer_embeddings, "answer"
            ),
            answers,
        )
    )
    questions = df["Clue"].to_list()
    question_embeddings = list(
        map(
            lambda q: retrieve_embedding_from_cache(
                str(q), unique_question_embeddings, "question"
            ),
            questions,
        )
    )

    embedded_df = pd.DataFrame(
        {
            "answer": answers,
            "embedded_answer": answer_embeddings,
            "question": questions,
            "embedded_question": question_embeddings,
        }
    )
    print("Saving as CSV...")
    print(embedded_df.head())
    embedded_df.to_csv("data/dataframes/embedded_qa_pairs.csv", index=False)

    # folder_name = "data/alphabetized_embeddings"
    # cache_path = "data/caches/answer_embedding_cache_test.pkl"
    # type = "answer"
    # merge_embeddings(folder_name, cache_path, type)


if __name__ == "__main__":
    main()
