import time
import re
from library import WordSuggester

def library_from_path(path: str, word_length: int, max_complexity=1000000):
    word_re = r"^[a-zA-Z]+$"
    with open(path) as fp:
        all_words = (line.strip() for line in fp)
        valid_words = [line.lower() for line in all_words if len(line) == word_length and re.match(word_re, line)]
    print(f"Using dictionary of {len(valid_words)} words")
    return WordSuggester(valid_words, max_complexity)


def get_suggestions(library: WordSuggester, suggestion_count: int, valid_only=False):
    print("Getting suggestions...")

    start = time.time()
    suggestions = library.suggest_words(suggestion_count, valid_only=valid_only)
    end = time.time()
    duration = end - start
    print(f"Calculating suggested words took {duration:.2f} seconds")
    return suggestions


def get_user_word(word_length: int):
    while True:
        print("What word did you use?")
        word = input().strip()
        if len(word) == word_length:
            return word
        else:
            print("That word doesn't have the right number of letters")


def get_user_feedback(word_length: int):
    while True:
        print("What was the game's response? [Y = Yellow, G = Green, N = None]")
        feedback = input().strip()
        if re.match(f"[YGN]{{{word_length}}}", feedback):
            return feedback
        else:
            print("That doesn't look right... please use one of YGN for each letter")


