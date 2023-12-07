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


def parse_clue(clue: str, answer: str, orientation: str, positions: dict) -> Clue:
    number, question = clue.split(". ", 1)
    position = positions[int(number)]
    return Clue(int(number), question, answer, orientation, position)
    

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