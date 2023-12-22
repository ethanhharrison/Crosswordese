from enum import unique
import numpy as np
import pandas as pd
import pickle
import random
from sklearn.model_selection import train_test_split
import torch

from embeddings_util import get_embedding, cosine_similarity

# input parameters
embedding_cache_path = "data/clueqa_embedding_cache.pkl"  # embeddings will be saved/loaded here
default_embedding_engine = "text-embedding-ada-002"  # text-embedding-ada-002 is recommended
num_pairs_to_embed = 1000  # 1000 is arbitrary
local_dataset_path = "data/unique_qa_pairs.csv" 

def process_input_data(df: pd.DataFrame) -> pd.DataFrame:
    # you can customize this to preprocess your own dataset
    # output should be a dataframe with 3 columns: text_1, text_2, label (1 for similar, -1 for dissimilar)
    df["label"] = df["gold_label"]
    df = df[df["label"].isin(["entailment"])]
    df["label"] = df["label"].apply(lambda x: {"entailment": 1, "contradiction": -1}[x])
    df = df.rename(columns={"sentence1": "text_1", "sentence2": "text_2"})
    df = df[["text_1", "text_2", "label"]]
    df = df.head(num_pairs_to_embed)
    return df

def main():
    df = pd.read_csv("data/unique_qa_pairs.csv")
    
    df = process_input_data(df)

if __name__ == "__main__":
    main()