import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from thefuzz import fuzz
import pandas as pd
import cgi
import cgitb
cgitb.enable()

def solve_clue(clue):
  nytcrossword_raw = pd.read_csv("nytcrosswords.csv", encoding="latin-1")
  # Remove null values in data frame
  nytcrossword = nytcrossword_raw.dropna()
  # Add new column giving info on the length of the answer
  nytcrossword["Word_Length"] = nytcrossword.apply(lambda x: len(x["Word"]), axis=1)
  # Add new column with info on what day of the week the clue was given
  nytcrossword["Date"] = pd.to_datetime(nytcrossword["Date"])
  nytcrossword["Day_of_Week"] = nytcrossword["Date"].dt.day_name()

  nytcrossword["Percent_Matching"] = nytcrossword.apply(lambda x: fuzz.ratio(x["Clue"], clue), axis=1)
  closest_match = max(nytcrossword["WORD"], key=lambda x: x["Percent_Matching"])
  return closest_match

def main():
  form = cgi.FieldStorage()
  if (form.has_key("param")):
    solve_clue(form["param"].value)
  else:
    raise ValueError("Did not provide clue!")

main()  