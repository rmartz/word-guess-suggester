import argparse
from library import simulate_feedback
from interaction import library_from_path, get_suggestions, get_user_word, get_user_feedback

parser = argparse.ArgumentParser(description='Tool to optimize word finding')
parser.add_argument('--corpus', type=str, default='/usr/share/dict/words',
                    help='Path to file to use as word list')
parser.add_argument('--letters', type=int, default='5',
                    help='Number of letters in guesses')
parser.add_argument('--guesses', type=int, default='6',
                    help='Number of guesses allowed')
parser.add_argument('--simulate', action='store_true',
                    help="Select a secret goal word internally and simulate responses")
parser.add_argument('--complexity', type=int, default=5,
                    help="Control how many goal/guess combinations are evaluated in scoring suggestions")
parser.add_argument('--hard-mode', action='store_true',
                    help="Only suggest guesses that can be valid answers")

args = parser.parse_args()

library = library_from_path(args.corpus, args.letters, args.complexity)
if args.simulate:
    secret = library.random_word()

for guess in range(1, args.guesses + 1):
    print("")
    print(f"Guess {guess}!")

    suggestions = get_suggestions(library, 5, valid_only=args.hard_mode)
    print("The top suggested words are:")
    for suggestion, _ in suggestions:
        print(f"- {suggestion}")

    word = get_user_word(args.letters)

    if args.simulate:
        feedback = simulate_feedback(secret, word)
        print(f"Your simulated feedback is {feedback}")
    else:
        feedback = get_user_feedback(args.letters)

    if feedback == 'G' * args.letters:
        print(f"You won in {guess} guesses!")
        break

    library.add_feedback(word, feedback)
else:
    print("Ran out of guesses :(")
