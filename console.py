import argparse
import random
import re

from library import WordleLibrary, simulate_feedback

parser = argparse.ArgumentParser(description='Tool to automate word finding for Wordle')
parser.add_argument('--corpus', type=str, default='/usr/share/dict/words',
                    help='Path to file to use as word list')
parser.add_argument('--letters', type=int, default='5',
                    help='Number of letters in guesses')
parser.add_argument('--guesses', type=int, default='6',
                    help='Number of guesses allowed')
parser.add_argument('--simulate', action='store_true',
                    help="Select a secret goal word internally and simulate Wordle's responses")


args = parser.parse_args()

def library_from_path(path):
    word_re = r"^[a-zA-Z]+$"
    with open(path) as fp:
        all_words = (line.strip() for line in fp)
        wordle_words = [line.lower() for line in all_words if len(line) == args.letters and re.match(word_re, line)]
    print(f"Using dictionary of {len(wordle_words)} words")
    return WordleLibrary(wordle_words)


library = library_from_path(args.corpus)
if args.simulate:
    secret = library.random_word()

for guess in range(1, args.guesses + 1):
    print(f"Guess {guess}!")
    print("Getting suggestions...")
    suggestions = library.suggest_words(5)
    print("The top suggested words are:")
    for suggestion, _ in suggestions:
        print(f"- {suggestion}")

    while True:
        print("What word did you use?")
        word = input().strip()
        if len(word) == args.letters:
            break
        else:
            print("That word doesn't have the right number of letters")

    if args.simulate:
        feedback = simulate_feedback(secret, word)
        print(f"Your simulated feedback is {feedback}")
    else:
        while True:
            print("What was Wordle's feedback? [Y = Yellow, G = Green, N = None]")
            feedback = input().strip()
            if re.match(f"[YGN]{{{args.letters}}}", feedback):
                break
            else:
                print("That doesn't look right... please use one of YGN for each letter")

    if feedback == 'G' * args.letters:
        print(f"You won in {guess} guesses!")
        break
    else:
        print("")


    library.add_feedback(word, feedback)
