from collections import namedtuple
from typing import TypeVar
import statistics
import random
import math

LetterCount = namedtuple("LetterCount", ["char", "count", "exact"])
T = TypeVar('T')

def key_count(char: str, count: int):
    yield LetterCount(char, count, True)
    for i in range(count):
        yield LetterCount(char, i + 1, False)

def normalize_counts(counts: "dict[any, int]", basis: int):
    return {key: 1.0 * count / basis for key, count in counts.items()}

def sample_items(source: "list[T]", max_samples=500) -> "list[T]":
    '''
    Return a subset of items with up to max_samples items

    If source has fewer than max_samples items, the whole collection is returned
    '''
    if len(source) > max_samples:
        return random.sample(source, max_samples)
    return source

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
    max_goal_samples: int = None
    max_guess_samples: int = None

    def __init__(self, word_list, complexity_level=5):
        self.valid_words = list(word_list)
        self.all_words = list(self.valid_words)
        self.set_max_complexity(complexity_level)

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
        if not valid_only:
            # Only suggest valid answers once we're down to 3 or fewer possible solutions.
            # At 3 options we are guaranteed success in 2 guesses - forcing a valid
            # guess means we also have a chance it is correct and we can win in 1
            valid_only = (len(self.valid_words) <= 3)

        sampled_goals = sample_items(self.valid_words, self.max_goal_samples)
        scorer = SignificanceScorer(sampled_goals)

        if valid_only:
            guesses = self.valid_words
        else:
            guesses = self.all_words

        sampled_guesses = sample_items(guesses, self.max_guess_samples)
        return ((word, scorer.score(word)) for word in sampled_guesses)

    def suggest_words(self, count, valid_only=None):
        scored_words = self._suggest_significant_words(
            valid_only=valid_only
        )
        return sorted(scored_words, key=lambda pair: pair[1], reverse=True)[:count]

    def suggest_word(self, valid_only=None):
        scored_words = self._suggest_significant_words(valid_only=valid_only)
        return max(scored_words, key=lambda pair: pair[1])

    def random_word(self):
        return random.choice(self.all_words)

    def reset(self):
        self.valid_words = list(self.all_words)

    def set_max_complexity(self, max_complexity):
        max_comparisons = 1000 * math.pow(10, max_complexity)
        goal_guess_sample_ratio = 10
        sample_base = math.sqrt(max_comparisons / goal_guess_sample_ratio)
        self.max_goal_samples = int(sample_base)
        self.max_guess_samples = int(sample_base * goal_guess_sample_ratio)



class SignificanceScorer(object):
    '''
    Calculates the impact a word is expected to have finding an unknown goal.

    Simulates what feedback that word could receive for every possible goal and how many
    possible goals that feedback would could eliminate, and scores the word on the median outcome.

    Words that can be expected to receive feedback that will eliminate more goals from
    consideration in most cases will be scored higher than words that may perform exceptionally
    well but in fewer cases.
    '''
    possible_words: "set[str]" = None

    def __init__(self, possible_words: "set[str]"):
        self.possible_words = possible_words

    @classmethod
    def _count_filtered_words(cls, word: str, possible_goals: "set[str]", feedback: str):
        '''
        Returns the number of goals that are still valid after applying feedback
        '''
        return sum(1 for _ in apply_feedback(possible_goals, word, feedback))

    @classmethod
    def _score_significance(cls, word, possible_goals):
        '''
        Returns a sequence of counts of how many possible goals would remain in
        consideration after applying the feedback expected if this word were used as a guess
        against each goal
        '''
        # Many word/goal combinations will produce the same feedback, which will always produce the
        # same filtering outcome. Rather than re-calculate the effect of the same feedback each
        # time we encounter it, we should store the result in memory and reuse it.
        feedback_cache = {}
        for goal in possible_goals:
            feedback = simulate_feedback(goal, word)
            if feedback not in feedback_cache:
                count = cls._count_filtered_words(word, possible_goals, feedback)
                feedback_cache[feedback] = count
            yield feedback_cache[feedback]

    def score(self, word):
        '''
        Returns a score representing how many potential goals guessing with this word is expected to
        eliminate, in the median case.
        '''
        starting_count = len(self.possible_words)
        simulated_counts = self._score_significance(word, self.possible_words)
        median_count = statistics.median(simulated_counts)

        median_reduction = starting_count - median_count
        return 1.0 * median_reduction / starting_count
