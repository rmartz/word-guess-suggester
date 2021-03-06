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
parser.add_argument('--secret', type=str, default=None,
                    help="Word to use for the goal to guess")
parser.add_argument('--complexity', type=int, default=5,
                    help="Control how many goal/guess combinations are evaluated in scoring suggestions")

args = parser.parse_args()

library = library_from_path(args.corpus, args.letters, args.complexity)

success_count = 0
guess_counts = list()
losing_words = list()

# All games start with the same state, and so the same initial guess.
# Since it is dramatically the slowest guess to compute, we can compute it once and store it.
fixed_first_suggestion = None
if args.starting_word:
    fixed_first_suggestion = args.starting_word
elif not args.secret:
    fixed_first_suggestion, _ = library.suggest_word()

for game in range(1, args.games + 1):
    library.reset()

    if args.secret:
        secret = args.secret
    else:
        secret = library.random_word()

    print("")
    print(f"Game {game}")
    for guess in range(1, args.guesses + 1):
        first_guess = (guess == 1)

        # Only use valid guesses on the last guess when an invalid guess means we guaranteed lose.
        last_guess = (guess == args.guesses)

        if first_guess and fixed_first_suggestion:
            suggestion = fixed_first_suggestion
        else:
            suggestion, _ = library.suggest_word(valid_only=last_guess)
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
    losing_word_counts = Counter(losing_words).items()
    sorted_losing_word_counts = sorted(losing_word_counts, key=lambda pair: pair[0])
    print("Words that were not guessed successfully:")
    for word, count in sorted_losing_word_counts:
        if count == 1:
            print(f"- {word}")
        else:
            print(f"- {word} ({count}x)")

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
