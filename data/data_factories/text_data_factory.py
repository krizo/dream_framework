from typing import List

from faker import Faker


class TextDataFactory:
    """Factory for generating text-related data"""

    def __init__(self, faker: Faker):
        self.faker = faker

    def word(self) -> str:
        """Generate a random word"""
        return self.faker.word()

    def words(self, count: int = 3) -> List[str]:
        """Generate a list of random words"""
        return self.faker.words(nb=count)

    def sentence(self, word_count: int = 6) -> str:
        """Generate a random sentence"""
        return self.faker.sentence(nb_words=word_count)

    def sentences(self, count: int = 3) -> List[str]:
        """Generate a list of random sentences"""
        return self.faker.sentences(nb=count)

    def paragraph(self, sentence_count: int = 3) -> str:
        """Generate a random paragraph"""
        return self.faker.paragraph(nb_sentences=sentence_count)

    def paragraphs(self, count: int = 3) -> List[str]:
        """Generate a list of random paragraphs"""
        return self.faker.paragraphs(nb=count)

    def text(self, max_chars: int = 200) -> str:
        """Generate random text with specified maximum length"""
        return self.faker.text(max_nb_chars=max_chars)