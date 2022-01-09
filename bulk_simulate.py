import argparse
import statistics
from library import simulate_feedback
from interaction import library_from_path
from collections import Counter

parser = argparse.ArgumentParser(description='Tool to optimize word finding')
parser.add_argument('--corpus', type=str, default='/usr/share/dict/words',
                    help='Path to file to use as word list')
parser.add_argument('--letters', type=int, default='5',
                    help='Number of letters in guesses')
parser.add_argument('--guesses', type=int, default='6',
                    help='Number of guesses allowed')
parser.add_argument('--games', type=int, default=10,
                    help="Number of games to simulate")
parser.add_argument('--starting-word', type=str, default=None,
                    help="Word to use as first guess in games")

args = parser.parse_args()

library = library_from_path(args.corpus, args.letters)

success_count = 0
guess_counts = list()
losing_words = list()

# All games start with the same state, and so the same initial guess.
# Since it is dramatically the slowest guess to compute, we can compute it once and store it.
if args.starting_word:
    first_guess = args.starting_word
else:
    first_guess, _ = library.suggest_word()

for game in range(1, args.games + 1):
    library.reset()

    secret = library.random_word()

    print("")
    print(f"Game {game}")
    for guess in range(1, args.guesses + 1):
        if guess == 1:
            suggestion = first_guess
        else:
            suggestion, _ = library.suggest_word()
        if suggestion == secret:
            print(f"Success in {guess} attempts")
            success_count += 1
            guess_counts.append(guess)
            break

        feedback = simulate_feedback(secret, suggestion)
        print(f"Guess {guess} was {suggestion}, response {feedback}")
        library.add_feedback(suggestion, feedback)
    else:
        losing_words.append(secret)

print(f"{success_count} successes in {args.games} games")
success_percent = 100.0 * success_count / args.games
print(f"({success_percent:.2f}% success)")
if losing_words:
    print("Words that were not guessed successfully:")
    for word in losing_words:
        print(f"- {word}")

mean_guesses = statistics.mean(guess_counts)
print(f"Mean guesses to win: {mean_guesses}")
print(f"Min guesses: {min(guess_counts)}")
print(f"Max guesses: {max(guess_counts)}")

histogram_counts = Counter(guess_counts)
histogram_width = 40
histogram_ratio = 1.0 * histogram_width / max(histogram_counts.values())

for guess in range(1, args.guesses + 1):
    bar_width = int(histogram_counts[guess] * histogram_ratio)
    histogram_bar = "#" * bar_width
    print(f"{guess}: {histogram_bar}")
