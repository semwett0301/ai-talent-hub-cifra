"""Dependency-free BM25 over one batch of event-cluster summaries."""

import math
import re
from collections import Counter
from collections.abc import Sequence

from news_service.domain.company_profile.model.facet import Facet

TOKEN_PATTERN = re.compile(r"[0-9A-Za-zА-Яа-яЁё][0-9A-Za-zА-Яа-яЁё_-]{1,}")
BM25_TERMS_WEIGHT = 0.35


def _tokenize(text: str) -> list[str]:
    return [match.group(0).lower() for match in TOKEN_PATTERN.finditer(text)]


class Bm25:
    def __init__(self, corpus: Sequence[str], k1: float = 1.5, length_weight: float = 0.75):
        self.__k1 = k1
        self.__length_weight = length_weight
        self.__documents = [_tokenize(text) for text in corpus]
        self.__lengths = [len(document) for document in self.__documents]
        self.__average_length = sum(self.__lengths) / len(self.__lengths) if corpus else 0.0
        self.__frequencies = [Counter(document) for document in self.__documents]
        self.__document_frequency: Counter[str] = Counter()
        for document in self.__documents:
            self.__document_frequency.update(set(document))

    def score(self, query: str) -> list[float]:
        terms = _tokenize(query)
        return [
            self.__document_score(frequency, length, terms)
            for frequency, length in zip(self.__frequencies, self.__lengths, strict=True)
        ]

    def __document_score(self, frequency: Counter[str], length: int, terms: list[str]) -> float:
        normalization = self.__normalization(length)
        return sum(self.__term_score(term, frequency.get(term, 0), normalization) for term in terms)

    def __normalization(self, length: int) -> float:
        ratio = length / self.__average_length if self.__average_length else 0.0
        return self.__k1 * (1.0 - self.__length_weight + self.__length_weight * ratio)

    def __term_score(self, term: str, frequency: int, normalization: float) -> float:
        if not frequency:
            return 0.0
        documents = len(self.__documents)
        containing = self.__document_frequency.get(term, 0)
        inverse = math.log(1.0 + (documents - containing + 0.5) / (containing + 0.5))
        return inverse * frequency * (self.__k1 + 1.0) / (frequency + normalization)


def calculate_bm25_scores(facets: tuple[Facet, ...], documents: list[str]) -> list[float]:
    if not documents:
        return []
    scorer = Bm25(documents)
    rows = [_facet_scores(scorer, facet) for facet in facets]
    return [max(row[index] for row in rows) for index in range(len(documents))]


def _facet_scores(scorer: Bm25, facet: Facet) -> list[float]:
    description_scores = scorer.score(facet.semantic_query)
    if not facet.bm25_terms:
        return description_scores
    term_scores = scorer.score(" ".join(facet.bm25_terms))
    return [
        description + BM25_TERMS_WEIGHT * terms
        for description, terms in zip(description_scores, term_scores, strict=True)
    ]
