from collections import namedtuple
import statistics
import random

LetterCount = namedtuple("LetterCount", ["char", "count", "exact"])

def key_count(char: str, count: int):
    yield LetterCount(char, count, True)
    for i in range(count):
        yield LetterCount(char, i + 1, False)

def normalize_counts(counts: "dict[any, int]", basis: int):
    return {key: 1.0 * count / basis for key, count in counts.items()}

def cap_complexity(words, complexity=500):
    if len(words) > complexity:
        return random.sample(words, complexity)
    return words

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
    def _apply_filter_step(word_list, pos, char, letter_feedback):
        if letter_feedback == "N":
            return (word for word in word_list if char not in word)
        elif letter_feedback == "Y":
            return (word for word in word_list if char in word and word[pos] != char)
        elif letter_feedback == "G":
            return (word for word in word_list if word[pos] == char)

    # Assume that letters only get used once
    it = iter(word_list)
    for pos, (char, letter_feedback) in enumerate(zip(guess, feedback)):
        it = _apply_filter_step(it, pos, char, letter_feedback)
    return it

class WordSuggester(object):
    valid_words: "list[str]" = list()
    all_words: "list[str]" = list()

    def __init__(self, word_list):
        self.valid_words = list(word_list)
        self.all_words = list(self.valid_words)

    def add_feedback(self, word: str, feedback: str):
        print(f"Applying feedback with word {word} and feedback {feedback}")
        word_count = len(self.valid_words)
        filtered_words = list(apply_feedback(self.valid_words, word, feedback))
        remaining_count = len(filtered_words)
        removed_count = word_count - remaining_count
        print(f"Removed {removed_count} words from consideration, {remaining_count} remaining")

        self.valid_words = filtered_words

        if remaining_count == 0:
            raise Exception("No valid guesses remain")

    def _suggest_significant_words(self, valid_only=True):
        sampled_goals = cap_complexity(self.valid_words, 1000)
        scorer = SignificanceScorer(sampled_goals)

        if valid_only:
            guesses = self.valid_words
        else:
            guesses = self.all_words

        sampled_guesses = cap_complexity(guesses, 10000)
        return ((word, scorer.score(word)) for word in sampled_guesses)

    def suggest_words(self, count):
        scored_words = self._suggest_significant_words(
            valid_only=(count >= len(self.valid_words)
        ))
        return sorted(scored_words, key=lambda pair: pair[1], reverse=True)[:count]

    def random_word(self):
        return random.choice(self.all_words)


# SignificanceScorer calculates the impact a word is expected to have finding an unknown goal.
# For every possible goal it simulates what feedback that word could receive and how many
# possibilities that feedback would help eliminate, and scores the word on the median outcome.
class SignificanceScorer(object):
    possible_words: "set[str]" = None

    def __init__(self, possible_words):
        self.possible_words = possible_words

    @classmethod
    def count_filtered_words(cls, word: str, possible_goals: "set[str]", feedback: str):
        return sum(1 for _ in apply_feedback(possible_goals, word, feedback))

    @classmethod
    def _score_significance(cls, word, possible_goals):
        # Many word/goal combinations will produce the same feedback, which will always produce the
        # same filtering outcome. Rather than re-calculate the effect of the same feedback each
        # time we encounter it, we should store the result in memory and reuse it.
        feedback_cache = {}
        for goal in possible_goals:
            feedback = simulate_feedback(goal, word)
            if feedback not in feedback_cache:
                count = cls.count_filtered_words(word, possible_goals, feedback)
                feedback_cache[feedback] = count
            yield feedback_cache[feedback]

    def score(self, word):
        starting_count = len(self.possible_words)
        simulated_counts = self._score_significance(word, self.possible_words)
        median_count = statistics.median(simulated_counts)

        median_reduction = starting_count - median_count
        return 1.0 * median_reduction / starting_count
