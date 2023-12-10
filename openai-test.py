from openai import OpenAI
import config

client = OpenAI()

completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    temperature=0.6,
    messages=[
        {"role": "system", "content": "You are an expert crossword solver. When given a crossword clue and the length of the clue's answer, you briefly answer the clue in all caps. Your response must be the length of the answer."},
        {"role": "user", "content": "Clue: 'Car mentioned in 'Hotel California,' informally', Answer Length: 8 Letters"},
    ]
)

print(completion.choices[0].message.content)