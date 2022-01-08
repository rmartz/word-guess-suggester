from collections import defaultdict, namedtuple
from functools import lru_cache
import statistics
import time
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

class WordleLibrary(object):
    valid_words: "list[str]" = list()
    guessable_words: "list[str]" = list()

    def add_word(self, word: str):
        self.valid_words.append(word)
        self.guessable_words.append(word)

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

    def _suggest_significant_words(self):
        sampled_goals = cap_complexity(self.valid_words, 1000)
        sampled_guesses = cap_complexity(self.guessable_words, 10000)

        scorer = SignificanceScorer(sampled_goals)
        return ((word, scorer.score(word)) for word in sampled_guesses)

    def _suggest_likely_words(self):
        def _score_word(scores, word):
            return sum(scores[char] for char in set(word))

        letter_counts = defaultdict(int)
        for word in self.valid_words:
            for char in set(word):
                letter_counts[char] += 1

        return ((word, _score_word(letter_counts, word)) for word in self.valid_words)

    def suggest_words(self, count):
        start = time.time()
        if len(self.valid_words) > count:
            scored_words = self._suggest_significant_words()
        else:
            scored_words = self._suggest_likely_words()
        result = sorted(scored_words, key=lambda pair: pair[1], reverse=True)[:count]

        end = time.time()
        print(f"Calculating suggested words took {end - start} seconds")
        return result


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
