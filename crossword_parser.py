import json
from crossword import Clue


def read_json_file(file_path: str) -> dict:
    with open(file_path) as file:
        data = json.load(file)
    return data
    
    
def get_clue_positons(crossword_data: dict) -> dict[int, tuple[int, int]]:
    size = crossword_data["size"]
    gridnums = crossword_data["gridnums"]
    clue_positions = {}
    for i in range(size["cols"]):
        for j in range(size["rows"]):
            clue_number = gridnums[i*size["cols"]+j]
            if clue_number > 0:
                clue_positions[clue_number] = (i, j)
    return clue_positions


def get_clues(crossword_data: dict, clue_positions: dict) -> list[Clue]:
    clues = crossword_data["clues"]
    answers = crossword_data["answers"]
    down_clues, across_clues = clues["down"], clues["across"]
    down_answers, across_answers = answers["down"], answers["across"]
    parsed_clues = []
    for clue, answer in zip(down_clues, down_answers):   
        number, question = clue.split(". ", 1)
        position = clue_positions[int(number)]
        parsed_clues.append(Clue(int(number), question, answer, "down", position))
    for clue, answer in zip(across_clues, across_answers):
        number, question = clue.split(". ", 1)
        position = clue_positions[int(number)]
        parsed_clues.append(Clue(int(number), question, answer, "across", position))
    return parsed_clues
    
    
def parse_crossword_json(file_path: str) -> tuple[int, int, list[Clue]]:
    data = read_json_file(file_path)
    rows, cols = data["size"]["rows"], data["size"]["cols"]
    clue_positions = get_clue_positons(data)
    clues = get_clues(data, clue_positions)
    return rows, cols, clues