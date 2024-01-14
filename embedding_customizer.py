import numpy as np
import pandas as pd
import plotly.express as px
import pickle
import random
import os
import operator
import itertools
from sklearn.model_selection import train_test_split
import torch

from embeddings_util import get_embedding, cosine_similarity

import signal


def suspension_handler(signum, frame):
    print(f"Ignoring signal {signum}")


# input parameters
optimal_run_cache = "data/cache/best_run.pkl"
embedding_cache_path = "data/caches/answer_embedding_cache.pkl"
default_embedding_engine = "text-embedding-ada-002"
local_dataset_path = "data/dataframes/unique_qa_pairs.csv"
run_hyperparameter_search = False
num_pairs_to_embed = 5120  # 1000 is arbitrary
random_seed = 1987


def process_input_data(df: pd.DataFrame) -> pd.DataFrame:
    # you can customize this to preprocess your own dataset
    # output should be a dataframe with 3 columns: text_1, text_2, and
    # label (1 for similar, -1 for dissimilar)
    df["label"] = 1
    df = df.rename(columns={"Answer": "text_1", "Clue": "text_2"})
    df = df.sample(n=num_pairs_to_embed, random_state=random_seed)
    return df


def perform_train_test_split(
    df: pd.DataFrame, test_fraction: float = 0.3
) -> tuple[pd.DataFrame, pd.DataFrame]:
    # split data into training and testing
    train_df, test_df = train_test_split(
        df, test_size=test_fraction, stratify=df["label"], random_state=random_seed
    )
    train_df.loc[:, "dataset"] = "train"
    test_df.loc[:, "dataset"] = "test"
    return train_df, test_df


def create_training_df(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    negatives_per_positive: int = 1,  # will work for larger values, but training will be slowe
) -> pd.DataFrame:
    # generate synthetic negatives
    # training set
    train_df_negatives = dataframe_of_negatives(train_df)
    train_df_negatives["dataset"] = "train"
    # testing set
    test_df_negatives = dataframe_of_negatives(test_df)
    test_df_negatives["dataset"] = "test"
    # sample negatives and combine with positives
    train_df = pd.concat(
        [
            train_df,
            train_df_negatives.sample(
                n=len(train_df) * negatives_per_positive, random_state=random_seed
            ),
        ]
    )
    test_df = pd.concat(
        [
            test_df,
            test_df_negatives.sample(
                n=len(test_df) * negatives_per_positive, random_state=random_seed
            ),
        ]
    )
    return pd.concat([train_df, test_df])


def dataframe_of_negatives(df_of_positives: pd.DataFrame) -> pd.DataFrame:
    """Return the dataframe of negative pairs made by combining elements of positive pairs"""
    df_texts = df_of_positives[["text_1", "text_2"]]

    # perform a cross join between answers and clue-answer pairs
    df_texts["key"] = 1
    df_answers = df_texts.drop("text_2", axis=1)
    all_pairs = pd.merge(df_answers, df_texts, on="key").drop("key", axis=1)  # type: ignore

    # retrieve all negative pairs by filtering rows that have the same text_1
    df_of_negatives = all_pairs[
        all_pairs["text_1_x"] != all_pairs["text_1_y"]
    ].drop_duplicates()
    df_of_negatives = df_of_negatives[["text_1_x", "text_2"]]
    df_of_negatives = df_of_negatives.rename(columns={"text_1_x": "text_1"})

    # add label and return
    df_of_negatives["label"] = -1
    return df_of_negatives


# calculate accuracy (and its standard error) of predicting label=1 if similarity>x
# x is optimized by sweeping from -1 to 1 in steps of 0.01
def accuracy_and_se(
    cosine_similarity, labeled_similarity
) -> tuple[float, float, float]:
    accuracies = {}
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
        accuracies[threshold] = accuracy
    threshold, a = max(accuracies.items(), key=operator.itemgetter(1))
    n = len(cosine_similarity)
    standard_error = (a * (1 - a) / n) ** 0.5  # standard error of binomial
    return threshold, a, standard_error


def embedding_multiplied_by_matrix(
    embedding: list[float], matrix: torch.Tensor
) -> np.ndarray:
    embedding_tensor = torch.tensor(embedding).float()
    modified_embedding = embedding_tensor @ matrix
    modified_embedding = modified_embedding.detach().numpy()
    return modified_embedding


# compute custom embeddings and new cosine similarities
def apply_matrix_to_embeddings_dataframe(matrix: torch.Tensor, df: pd.DataFrame):
    for column in ["text_1_embedding", "text_2_embedding"]:
        df[f"{column}_custom"] = df[column].apply(
            lambda x: embedding_multiplied_by_matrix(x, matrix)  # type: ignore
        )  # type: ignore
    df["cosine_similarity_custom"] = df.apply(
        lambda row: cosine_similarity(
            row["text_1_embedding_custom"], row["text_2_embedding_custom"]
        ),
        axis=1,
    )
    return df


def save_embedding(
    cache: dict, cache_filname: str, temp_filename: str = "data/temp_cache.pkl"
):
    signal.signal(
        signal.SIGTSTP, suspension_handler
    )  # don't allow suspension during pickling
    with open(temp_filename, "wb") as embedding_cache_file:
        pickle.dump(cache, embedding_cache_file)
        embedding_cache_file.flush()
    os.rename(temp_filename, cache_filname)
    signal.signal(signal.SIGTSTP, signal.SIG_DFL)  # reset suspension handling


def get_embedding_with_cache(
    text: str,
    embedding_cache: dict,
    engine: str = default_embedding_engine,
    embedding_cache_path: str = embedding_cache_path,
) -> list:
    if (text, engine) not in embedding_cache.keys():
        try:
            print(f"{text} not found in cache, creating embedding")
            # if not in cache, call API to get embedding
            embedding_cache[(text, engine)] = get_embedding(text, engine)
            # save embeddings cache to disk after each update
            save_embedding(embedding_cache, embedding_cache_path)
        except BaseException as be:
            print(be)
            print(f"{text} failed to embed, not including in cache")
            return []

    return embedding_cache[(text, engine)]


def embed_all_answers(
    string_list: list[str],
    old_cache: dict,
    engine: str = default_embedding_engine,
    type: str = "answer",
):
    for letter, words in itertools.groupby(string_list, key=operator.itemgetter(0)):
        alphabet_cache_name = (
            f"data/alphabetized_embeddings/{letter}_{type}_embeddings.pkl"
        )
        try:
            with open(alphabet_cache_name, "rb") as f:
                alphabet_cache = pickle.load(f)
        except:
            alphabet_cache = {}
        for string in words:
            if (string, engine) not in old_cache.keys():
                get_embedding_with_cache(
                    string,
                    alphabet_cache,
                    engine=engine,
                    embedding_cache_path=alphabet_cache_name,
                )
            elif (string, engine) not in alphabet_cache.keys():
                print(f"{string} found in old cache, adding to new cache")
                alphabet_cache[(string, engine)] = old_cache[(string, engine)]
                save_embedding(alphabet_cache, alphabet_cache_name)
            else:
                print(f"{string} already found in the alphabet cache")


def combine_embeddings(embedding_folder: str, combined_cache: dict):
    for f in os.listdir(embedding_folder):
        with open(os.path.join(embedding_folder, f), "rb") as f:
            letter_cache = pickle.load(f)
            combined_cache.update(letter_cache)
    save_embedding(combined_cache, embedding_cache_path)


def optimize_matrix(
    df: pd.DataFrame,
    modified_embedding_length: int = 1536,  # in my brief experimentation, bigger was better (2048 is length of babbage encoding)
    batch_size: int = 100,
    max_epochs: int = 100,
    learning_rate: float = 100.0,  # seemed to work best when similar to batch size - feel free to try a range of values
    dropout_fraction: float = 0.0,  # in my testing, dropout helped by a couple percentage points (definitely not necessary)
    print_progress: bool = True,
    save_results: bool = True,
) -> torch.Tensor:
    """Return matrix optimized to minimize loss on training data."""
    run_id = random.randint(0, 2**31 - 1)  # (range is arbitrary)

    # convert from dataframe to torch tensors
    # e is for embedding, s for similarity label
    def tensors_from_dataframe(
        df: pd.DataFrame,
        embedding_column_1: str,
        embedding_column_2: str,
        similarity_label_column: str,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        e1 = np.stack(np.array(df[embedding_column_1].values))  # type: ignore
        e2 = np.stack(np.array(df[embedding_column_2].values))  # type: ignore
        s = np.stack(np.array(df[similarity_label_column].astype("float").values))  # type: ignore

        e1 = torch.from_numpy(e1).float()
        e2 = torch.from_numpy(e2).float()
        s = torch.from_numpy(s).float()

        return e1, e2, s

    e1_train, e2_train, s_train = tensors_from_dataframe(
        df[df["dataset"] == "train"], "text_1_embedding", "text_2_embedding", "label"
    )
    e1_test, e2_test, s_test = tensors_from_dataframe(
        df[df["dataset"] == "test"], "text_1_embedding", "text_2_embedding", "label"
    )

    # create dataset and loader
    dataset = torch.utils.data.TensorDataset(e1_train, e2_train, s_train)
    train_loader = torch.utils.data.DataLoader(
        dataset, batch_size=batch_size, shuffle=True
    )

    # define model (similarity of projected embeddings)
    def model(embedding_1, embedding_2, matrix, dropout_fraction=dropout_fraction):
        e1 = torch.nn.functional.dropout(embedding_1, p=dropout_fraction)
        e2 = torch.nn.functional.dropout(embedding_2, p=dropout_fraction)
        modified_embedding_1 = e1 @ matrix  # @ is matrix multiplication
        modified_embedding_2 = e2 @ matrix
        similarity = torch.nn.functional.cosine_similarity(
            modified_embedding_1, modified_embedding_2
        )
        return similarity

    # define loss function to minimize
    def mse_loss(predictions, targets) -> torch.Tensor:
        difference = predictions - targets
        return torch.sum(difference * difference) / difference.numel()

    # initialize projection matrix
    embedding_length = len(df["text_1_embedding"].values[0])
    matrix = torch.randn(
        embedding_length, modified_embedding_length, requires_grad=True
    )

    epochs, types, losses, accuracies, matrices = [], [], [], [], []
    for epoch in range(1, 1 + max_epochs):
        # iterate through training dataloader
        for a, b, actual_similarity in train_loader:
            # generate prediction
            predicted_similarity = model(a, b, matrix)
            # get loss and perform backpropagation
            loss = mse_loss(predicted_similarity, actual_similarity)
            loss.backward()
            # update the weights
            with torch.no_grad():
                matrix -= matrix.grad * learning_rate  # type: ignore
                # set gradients to zero
                matrix.grad.zero_()
        # calculate test loss
        test_predictions = model(e1_test, e2_test, matrix)
        test_loss = mse_loss(test_predictions, s_test)

        # compute custom embeddings and new cosine similarities
        df = apply_matrix_to_embeddings_dataframe(matrix, df)

        # calculate test accuracy
        for dataset in ["train", "test"]:
            data = df[df["dataset"] == dataset]
            threshold, a, se = accuracy_and_se(
                data["cosine_similarity_custom"], data["label"]
            )

            # record results of each epoch
            epochs.append(epoch)
            types.append(dataset)
            losses.append(loss.item() if dataset == "train" else test_loss.item())  # type: ignore
            accuracies.append(a)
            matrices.append(matrix.detach().numpy())

            # optionally print accuracies
            if print_progress is True:
                print(
                    f"Epoch {epoch}/{max_epochs}: {dataset} accuracy: {a:0.1%} ± {1.96 * se:0.1%}"
                )

    data = pd.DataFrame(
        {"epoch": epochs, "type": types, "loss": losses, "accuracy": accuracies}
    )
    data["run_id"] = run_id
    data["modified_embedding_length"] = modified_embedding_length
    data["batch_size"] = batch_size
    data["max_epochs"] = max_epochs
    data["learning_rate"] = learning_rate
    data["dropout_fraction"] = dropout_fraction
    data[
        "matrix"
    ] = matrices  # saving every single matrix can get big; feel free to delete/change
    if save_results is True:
        data.to_csv(f"{run_id}_optimization_results.csv", index=False)
    return data  # type: ignore


def hyperparameter_search(
    df: pd.DataFrame,
    hyperparameters_to_test: list[tuple],
    max_epochs: int = 30,
    dropout_fraction: float = 0.2,
    retrieve_cache: bool = False,
    plot: bool = True,
) -> torch.Tensor:
    if retrieve_cache:
        try:
            with open(optimal_run_cache, "rb") as f:
                best_run = pickle.load(f)
                best_matrix = best_run["matrix"]
                return best_matrix
        except FileNotFoundError:
            raise FileNotFoundError("No cache file found. Set retrieve_cache to false.")
    else:
        results = []
        for batch_size, learning_rate in hyperparameters_to_test:
            result = optimize_matrix(
                df=df,
                batch_size=batch_size,
                learning_rate=learning_rate,
                max_epochs=max_epochs,
                dropout_fraction=dropout_fraction,
                save_results=False,
            )
            results.append(result)

        runs_df = pd.concat(results)
        best_run = runs_df.sort_values(by="accuracy", ascending=False).iloc[0]

        with open(optimal_run_cache, "wb") as optimal_run_file:
            pickle.dump(best_run, optimal_run_file)

        best_matrix = best_run["matrix"]

        if plot:
            # plot training loss and test loss over time
            plot_hyperparameter_training(runs_df, measure_loss=True)

            # plot accuracy over time
            plot_hyperparameter_training(runs_df, measure_loss=False)

        return best_matrix


def plot_hyperparameter_training(runs_df: pd.DataFrame, measure_loss: bool = True):
    y = "loss" if measure_loss else "accuracy"
    px.line(
        runs_df,
        line_group="run_id",
        x="epoch",
        y=y,
        color="type",
        hover_data=["batch_size", "learning_rate", "dropout_fraction"],
        facet_row="learning_rate",
        facet_col="batch_size",
        width=500,
    ).show()


def plot_cosine_similarity_histogram(df: pd.DataFrame, custom: bool = True):
    x = "cosine_similarity_custom" if custom else "cosine_similarity"
    px.histogram(
        df,
        x=x,
        color="label",
        barmode="overlay",
        width=500,
        facet_row="dataset",
    ).show()


def main():
    # process data
    df = pd.read_csv("data/unique_qa_pairs.csv")
    df = process_input_data(df)

    # split into training and testing sets
    train_df, test_df = perform_train_test_split(df, test_fraction=0.3)

    # add artiticial negative pairs to dataset
    # this is done after the train-test split so there is no contamination
    df = create_training_df(train_df, test_df, negatives_per_positive=1)

    # establishing a cache of embeddings to avoid recomputing
    try:
        with open(embedding_cache_path, "rb") as f:
            embedding_cache = pickle.load(f)
    except FileNotFoundError:
        embedding_cache = {}

    # create column of embeddings
    for column in ["text_1", "text_2"]:
        df[f"{column}_embedding"] = df[column].apply(
            lambda x: get_embedding_with_cache(x, embedding_cache)
        )
    # create column of cosine similarity
    df["cosine_similarity"] = df.apply(
        lambda row: cosine_similarity(row["text_1_embedding"], row["text_2_embedding"]),
        axis=1,
    )

    # example hyperparameter search
    # I recommend starting with max_epochs=10 while initially exploring
    if run_hyperparameter_search:
        hyperparameters = [
            (1000, 1000),
            (1250, 1250),
            (1500, 1500),
        ]  # (batch_size, learning_size)
        best_matrix = hyperparameter_search(
            df,
            hyperparameters,
            max_epochs=30,
            dropout_fraction=0.2,
            retrieve_cache=True,
            plot=False,
        )
    else:
        with open(optimal_run_cache, "rb") as f:
            best_run = pickle.load(f)
            best_matrix = best_run["matrix"]

    # apply result of best run to original data
    df = apply_matrix_to_embeddings_dataframe(best_matrix, df)

    # plot similarity distribution BEFORE customization
    plot_cosine_similarity_histogram(df, custom=False)

    test_df = df[df["dataset"] == "test"]
    threshold, a, se = accuracy_and_se(test_df["cosine_similarity"], test_df["label"])
    print(f"Test accuracy: {a:0.1%} ± {1.96 * se:0.1%}")

    # plot similarity distribution AFTER customization
    plot_cosine_similarity_histogram(df, custom=True)

    threshold, a, se = accuracy_and_se(
        test_df["cosine_similarity_custom"], test_df["label"]
    )
    print(f"Test accuracy after customization: {a:0.1%} ± {1.96 * se:0.1%}")


if __name__ == "__main__":
    main()
