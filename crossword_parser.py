from crossword import Clue
import json
import os

def read_json_file(file_path: str) -> dict:
    with open(file_path) as file:
        data = json.load(file)
    return data


def get_clue_positons(crossword_data: dict) -> dict[int, tuple[int, int]]:
    size = crossword_data["size"]
    gridnums = crossword_data["gridnums"]
    clue_positions = {}
    for i in range(size["rows"]):
        for j in range(size["cols"]):
            clue_number = gridnums[i * size["cols"] + j]
            if clue_number > 0:
                clue_positions[clue_number] = (i, j)
    return clue_positions


def parse_clue(
    clue: str, 
    answer: str, 
    orientation: str, 
    positions: dict
) -> Clue:
    number, question = clue.split(". ", 1)
    num_down, num_across = positions[int(number)]
    return Clue(int(number), question, answer, orientation, num_down, num_across)


def get_clues(crossword_data: dict, positions: dict) -> list[Clue]:
    clues = crossword_data["clues"]
    answers = crossword_data["answers"]
    parsed_clues = []
    for clue, answer in zip(clues["down"], answers["down"]):
        parsed_clue = parse_clue(clue, answer, "down", positions)
        parsed_clues.append(parsed_clue)
    for clue, answer in zip(clues["across"], answers["across"]):
        parsed_clue = parse_clue(clue, answer, "across", positions)
        parsed_clues.append(parsed_clue)
    return parsed_clues


def parse_crossword_json(file_path: str) -> tuple[int, int, list[Clue]]:
    data = read_json_file(file_path)
    rows, cols = data["size"]["rows"], data["size"]["cols"]
    clue_positions = get_clue_positons(data)
    clues = get_clues(data, clue_positions)
    return rows, cols, clues


def get_all_QA_pairs(path: str) -> list[Clue]:
    """Return all of the json files within a folder"""
    if os.path.isfile(path):
        try:
            _, _, clues = parse_crossword_json(path)
            return clues
        except json.decoder.JSONDecodeError: # catch any poorly-formatted files
            return []
    else:
        all_files = []
        for f in os.listdir(path):
            all_files += get_all_QA_pairs(os.path.join(path, f))
        return all_files
    
def get_QA_pairs_as_txt(path: str) -> None:
    new_folder = "data/qa_text"
    if not os.path.exists(new_folder):
        os.makedirs(new_folder)
    if os.path.isfile(path):
        try: 
            _, _, clues = parse_crossword_json(path)
            file_name = "_".join(path.split("/")[1:-1]) + ".txt"
            file_name = os.path.join(new_folder, file_name)
            print(file_name)
            with open(file_name, "a") as file:
                for clue in clues:
                    file.write(f"{clue.question} ({len(clue.solution)} letters): {clue.solution}\n")
        except json.decoder.JSONDecodeError:
            pass
    else:
        for f in os.listdir(path):
            get_QA_pairs_as_txt(os.path.join(path, f))