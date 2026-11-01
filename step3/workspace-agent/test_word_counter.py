import unittest

from word_counter import count_words, word_frequencies, tokenize


class TestWordCounter(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(count_words(""), 0)
        self.assertEqual(count_words("   \n\t "), 0)

    def test_simple(self):
        self.assertEqual(count_words("hello world"), 2)

    def test_punctuation_and_whitespace(self):
        self.assertEqual(count_words("Hello,   world!\nHow are you?"), 5)

    def test_case_insensitive_frequencies(self):
        freq = word_frequencies("The the THE cat")
        self.assertEqual(freq["the"], 3)
        self.assertEqual(freq["cat"], 1)

    def test_apostrophes(self):
        self.assertEqual(tokenize("Don't stop"), ["don't", "stop"])

    def test_numbers(self):
        self.assertEqual(count_words("There are 3 cats"), 4)


if __name__ == "__main__":
    unittest.main()
