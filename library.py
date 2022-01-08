from collections import defaultdict, namedtuple
import statistics

LetterCount = namedtuple("LetterCount", ["char", "count", "exact"])

def key_count(char: str, count: int):
    yield LetterCount(char, count, True)
    for i in range(count):
        yield LetterCount(char, i + 1, False)

def normalize_counts(counts: "dict[any, int]", basis: int):
    return {key: 1.0 * count / basis for key, count in counts.items()}

def score_word(scores, word):
    return sum(scores[char] for char in set(word))

def simulate_feedback(goal, guess):
    def _simulate_feedback():
        for goal_char, guess_char in zip(goal, guess):
            if goal_char == guess_char:
                yield 'G'
            elif guess_char in goal:
                yield 'Y'
            else:
                yield 'N'
    return ''.join(_simulate_feedback())

def apply_feedback(word_list, guess, feedback):
    # Assume that letters only get used once
    for pos, (char, letter_feedback) in enumerate(zip(guess, feedback)):
        if letter_feedback == "N":
            word_list = [word for word in word_list if char not in word]
        elif letter_feedback == "Y":
            word_list = [word for word in word_list if char in word and word[pos] != char]
        elif letter_feedback == "G":
            word_list = [word for word in word_list if char in word and word[pos] == char]
    return word_list

class WordleLibrary(object):
    valid_words: "list[str]" = list()
    guessable_words: "list[str]" = list()

    def add_word(self, word: str):
        self.valid_words.append(word)
        self.guessable_words.append(word)

    def add_feedback(self, word: str, feedback: str):
        print(f"Applying feedback with word {word} and feedback {feedback}")
        word_count = len(self.valid_words)
        self.valid_words = list(apply_feedback(self.valid_words, word, feedback))
        remaining_count = len(self.valid_words)
        removed_count = word_count - remaining_count
        print(f"Removed {removed_count} words from consideration, {remaining_count} remaining")
        if remaining_count == 0:
            raise Exception("No valid guesses remain")

    def _suggest_significant_words(self):
        scorer = SignificanceScorer(self.valid_words)
        return ((word, scorer.score(word)) for word in self.valid_words)

    def _suggest_likely_words(self):
        letter_counts = defaultdict(int)
        for word in self.valid_words:
            for char in set(word):
                letter_counts[char] += 1

        return ((word, score_word(letter_counts, word)) for word in self.valid_words)

    def suggest_words(self, count):
        scored_words = self._suggest_significant_words()
        return sorted(scored_words, key=lambda pair: pair[1], reverse=True)[:count]


class SignificanceScorer(object):
    possible_words: "list[str]" = None

    def __init__(self, possible_words):
        self.possible_words = possible_words

    @classmethod
    def _score_significance(cls, word, possible_goals):
        for goal in possible_goals:
            feedback = simulate_feedback(goal, word)
            yield sum(1 for _ in apply_feedback(possible_goals, word, feedback))

    def score(self, word):
        starting_count = len(self.possible_words)
        simulated_counts = self._score_significance(word, self.possible_words)
        median_count = statistics.mean(simulated_counts)

        median_reduction = starting_count - median_count
        return 1.0 * median_reduction / starting_count
