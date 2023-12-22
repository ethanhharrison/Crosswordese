from enum import unique
import numpy as np
import pandas as pd
import plotly.express as px
import pickle
import random
from sklearn.model_selection import train_test_split
import torch

from embeddings_util import get_embedding, cosine_similarity

# input parameters
embedding_cache_path = "data/clueqa_embedding_cache.pkl"  # embeddings will be saved/loaded here
default_embedding_engine = "text-embedding-ada-002"  # text-embedding-ada-002 is recommended
local_dataset_path = "data/unique_qa_pairs.csv" 
num_pairs_to_embed = 1000  # 1000 is arbitrary
random_seed = 1987

def process_input_data(df: pd.DataFrame) -> pd.DataFrame:
    # you can customize this to preprocess your own dataset
    # output should be a dataframe with 3 columns: text_1, text_2, and
    # label (1 for similar, -1 for dissimilar)
    df["label"] = 1
    df = df.rename(columns={"Answer": "text_1", "Clue": "text_2"})
    df = df.sample(n=num_pairs_to_embed, random_state=random_seed)
    return df

def dataframe_of_negatives(df_of_positives: pd.DataFrame) -> pd.DataFrame:
    """Return the dataframe of negative pairs made by combining elements of positive pairs"""
    df_texts = df_of_positives[["text_1", "text_2"]]
    
    # perform a cross join between answers and clue-answer pairs
    df_texts["key"] = 1
    df_answers = df_texts.drop("text_2", axis=1)
    all_pairs = pd.merge(df_answers, df_texts, on="key").drop("key", axis=1)  # type: ignore
    
    # retrieve all negative pairs by filtering rows that have the same text_1
    df_of_negatives = all_pairs[all_pairs["text_1_x"] != all_pairs["text_1_y"]].drop_duplicates()
    df_of_negatives = df_of_negatives[["text_1_x", "text_2"]]
    df_of_negatives = df_of_negatives.rename(columns={"text_1_x": "text_1"})
    
    # add label and return
    df_of_negatives["label"] = -1
    return df_of_negatives

# calculate accuracy (and its standard error) of predicting label=1 if similarity>x
# x is optimized by sweeping from -1 to 1 in steps of 0.01
def accuracy_and_se(cosine_similarity, labeled_similarity) -> tuple[float, float]:
    accuracies = []
    for threshold_thousandths in range(-1000, 1000, 1):
        threshold = threshold_thousandths / 1000
        total = 0
        correct = 0
        for cs, ls in zip(cosine_similarity, labeled_similarity):
            total += 1
            if cs > threshold:
                prediction = 1
            else:
                prediction = -1
            if prediction == ls:
                correct += 1
        accuracy = correct / total
        accuracies.append(accuracy)
    a = max(accuracies)
    n = len(cosine_similarity)
    standard_error = (a * (1 - a) / n) ** 0.5  # standard error of binomial
    return a, standard_error


def main():
    # process data
    df = pd.read_csv("data/unique_qa_pairs.csv")
    
    df = process_input_data(df)
    
    # split data into training and testing
    test_fraction = 0.5
    train_df, test_df = train_test_split(
        df, test_size=test_fraction, stratify=df["label"], random_state=random_seed
    )
    train_df.loc[:, "dataset"] = "train"
    test_df.loc[:, "dataset"] = "test"

    # generate synthetic negatives
    negatives_per_positive = 1 # will work for larger values, but training will be slowe
    # training set
    train_df_negatives = dataframe_of_negatives(train_df)
    train_df_negatives["dataset"] = "train"
    # testing set
    test_df_negatives = dataframe_of_negatives(test_df)
    test_df_negatives["dataset"] = "test"
    # sample negatives and combine with positives
    train_df = pd.concat([
        train_df, 
        train_df_negatives.sample(
            n=len(train_df) * negatives_per_positive, random_state=random_seed
        )
    ])
    test_df = pd.concat([
        test_df, 
        test_df_negatives.sample(
            n=len(test_df) * negatives_per_positive, random_state=random_seed
        )
    ])
    df = pd.concat([train_df, test_df])
    
    # establishing a cache of embeddings to avoid recomputing
    try:
        with open(embedding_cache_path, "rb") as f:
            embedding_cache = pickle.load(f)
    except FileNotFoundError:
        embedding_cache = {}
    
    def get_embedding_with_cache(
        text: str,
        embedding_cache: dict = embedding_cache,
        engine: str = default_embedding_engine,
        embedding_cache_path: str = embedding_cache_path
    ) -> list:
        if (text, engine) not in embedding_cache.keys():
            print(f"{text} not found in cache, creating embedding")
            # if not in cache, call API to get embedding
            embedding_cache[(text, engine)] = get_embedding(text, engine)
            # save embeddings cache to disk after each update
            with open(embedding_cache_path, "wb") as embedding_cache_file:
                pickle.dump(embedding_cache, embedding_cache_file)
        return embedding_cache[(text, engine)]
    
    # create column of embeddings
    for column in ["text_1", "text_2"]:
        df[f"{column}_embedding"] = df[column].apply(get_embedding_with_cache)
    # create column of cosine similarity
    df["cosine_similarity"] = df.apply(
        lambda row: cosine_similarity(row["text_1_embedding"], row["text_2_embedding"]),
        axis = 1
    )
    
    # check that training and test sets are balanced
    px.histogram(
        df,
        x="cosine_similarity",
        color="label",
        barmode="overlay",
        width=500,
        facet_row="dataset",
    ).show()

    for dataset in ["train", "test"]:
        data = df[df["dataset"] == dataset]
        a, se = accuracy_and_se(data["cosine_similarity"], data["label"])
        print(f"{dataset} accuracy: {a:0.1%} ± {1.96 * se:0.1%}")

if __name__ == "__main__":
    main()