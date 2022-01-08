from collections import defaultdict, Counter, namedtuple
from itertools import islice, groupby
from os import name

LetterCount = namedtuple("LetterCount", ["char", "count", "exact"])

def key_count(char: str, count: int):
    yield LetterCount(char, count, True)
    for i in range(count):
        yield LetterCount(char, i + 1, False)

def normalize_counts(counts: "dict[any, int]", basis: int):
    return {key: 1.0 * count / basis for key, count in counts.items()}

def score_word(scores, word):
    return sum(scores[char] for char in set(word))

class WordleLibrary(object):

    words: "set[str]" = set()

    def add_word(self, word: str):
        self.words.add(word.lower())

    def add_feedback(self, word: str, feedback: str):
        print(f"Applying feedback with word {word} and feedback {feedback}")
        # Assume that letters only get used once
        for pos, (char, letter_feedback) in enumerate(zip(word, feedback)):
            word_count = len(self.words)
            if letter_feedback == "N":
                print(f"Excluding all words with {char}")
                self.words = [word for word in self.words if char not in word]
            if letter_feedback == "Y":
                print(f"Filtering for words with {char} but not at position {pos}")
                self.words = [word for word in self.words if char in word and word[pos] != char]
            if letter_feedback == "G":
                print(f"Filtering for words with {char} at position {pos}")
                self.words = [word for word in self.words if char in word and word[pos] == char]
            remaining_count = len(self.words)
            removed_count = word_count - remaining_count
            print(f"Removed {removed_count} words from consideration, {remaining_count} remaining")
        self.words = list(self.words)

    def _suggest_words(self):
        letter_counts = defaultdict(int)
        for word in self.words:
            for char in set(word):
                letter_counts[char] += 1

        return sorted(self.words, key=lambda word: score_word(letter_counts, word), reverse=True)

    def suggest_words(self, count):
        return islice(self._suggest_words(), count)
