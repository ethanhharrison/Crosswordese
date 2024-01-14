import pandas as pd
import pickle
import openai

from embedding_customizer import embed_all_answers

ANSWER_EMBEDDING_CACHE_FILE = "data/caches/answer_embedding_cache.pkl"


def main():
    df = pd.read_csv("data/dataframes/unique_qa_pairs.csv")
    # with open(ANSWER_EMBEDDING_CACHE_FILE, "rb") as f:
    #     unique_answer_embeddings = pickle.load(f)

    # answer_question_pairs = df.itertuples(index=False, name=None)  # [(a, q), ...]
    # answer_question_embedding_pairs = []  # [(ae, qe), ...]

    # answers = df["Answer"].to_list()
    questions = list(df["Clue"].unique())

    questions = list(map(str, questions))

    questions.sort()

    embed_all_answers(questions, {}, type="question")


if __name__ == "__main__":
    main()
