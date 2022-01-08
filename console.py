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
                    help='Engage simulation mode for testing')


args = parser.parse_args()

library = WordleLibrary()

word_re = r"^[a-zA-Z]+$"

with open(args.corpus) as fp:
    all_words = (line.strip() for line in fp)
    wordle_words = (line.lower() for line in all_words if len(line) == args.letters and re.match(word_re, line))
    for word in wordle_words:
        library.add_word(word)

print(f"Using dictionary of {len(library.valid_words)} words")

if args.simulate:
    secret = random.choice(library.valid_words)

for _ in range(args.guesses):
    print("The top suggested words are:")
    for suggestion, score in library.suggest_words(5):
        print(f"- {suggestion} ({score})")

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
        if feedback == 'G' * args.letters:
            print("You win!")
            break
    else:
        while True:
            print("What was Wordle's feedback? [Y = Yellow, G = Green, N = None]")
            feedback = input().strip()
            if re.match(f"[YGN]{{{args.letters}}}", feedback):
                break
            else:
                print("That doesn't look right... please use one of YGN for each letter")

    library.add_feedback(word, feedback)
