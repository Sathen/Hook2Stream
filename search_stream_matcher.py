from difflib import SequenceMatcher
from typing import Optional, List

from media_models import StreamsSearchRequest, SearchStreamItem


class StreamMatchCalculator:
    def __init__(self,
                 title_weight: float = 0.4,
                 original_title_weight: float = 0.3,
                 year_weight: float = 0.2,
                 season_weight: float = 0.2,
                 episode_weight: float = 0.1):
        self.title_weight = title_weight
        self.original_title_weight = original_title_weight
        self.year_weight = year_weight
        self.season_weight = season_weight
        self.episode_weight = episode_weight

    def calculate_title_similarity(self, request_title: str, item_title: str) -> float:
        if not request_title or not item_title:
            return 0.0

        req_title = request_title.lower().strip()
        item_title_norm = item_title.lower().strip()

        similarity = SequenceMatcher(None, req_title, item_title_norm).ratio()

        if req_title == item_title_norm:
            similarity = 1.0
        elif req_title in item_title_norm or item_title_norm in req_title:
            similarity = max(similarity, 0.9)

        return similarity

    def calculate_year_score(self, request_year: Optional[int], item_year: int) -> float:
        if not request_year:
            return 0.0

        if request_year == item_year:
            return 1.0  # Perfect match
        elif abs(request_year - item_year) <= 1:
            return 0.8  # Close match (±1 year)
        elif abs(request_year - item_year) <= 2:
            return 0.5  # Acceptable match (±2 years)
        else:
            return 0.0

    def calculate_season_score(self, request_season: Optional[int], item_season: int) -> float:
        if not request_season:
            return 0.0

        return 1.0 if request_season == item_season else 0.0

    def calculate_episode_score(self, request_episode: Optional[int], item_episodes: int) -> float:
        if not request_episode:
            return 0.0

        return 1.0 if request_episode <= item_episodes else 0.0

    def calculate_match_score(self, request: StreamsSearchRequest, item: SearchStreamItem) -> float:
        score = 0.0
        max_score = 0.0

        title_similarity = self.calculate_title_similarity(request.title, item.title)
        score += title_similarity * self.title_weight
        max_score += self.title_weight

        if request.original_title:
            original_title_similarity = self.calculate_title_similarity(request.original_title, item.title)
            score += original_title_similarity * self.original_title_weight
            max_score += self.original_title_weight

            best_title_match = max(title_similarity, original_title_similarity)
            score = score - (title_similarity * self.title_weight) + (best_title_match * self.title_weight)

        if request.year:
            year_score = self.calculate_year_score(request.year, item.year)
            score += year_score * self.year_weight
            max_score += self.year_weight

        # Season matching
        if request.season_number:
            season_score = self.calculate_season_score(request.season_number, item.season)
            score += season_score * self.season_weight
            max_score += self.season_weight

        # Episode availability check
        if request.total_episodes:
            episode_score = self.calculate_episode_score(request.total_episodes, item.number_of_episodes)
            score += episode_score * self.episode_weight
            max_score += self.episode_weight

        # Normalize score to 0-1 range
        if max_score > 0:
            return score / max_score
        else:
            return title_similarity  # Fallback to title similarity only


def find_best_match(request: StreamsSearchRequest, search_results: List[SearchStreamItem],
                    calculator: StreamMatchCalculator = None, min_threshold: float = 0.3) -> Optional[SearchStreamItem]:
    if not search_results:
        return None

    if calculator is None:
        calculator = StreamMatchCalculator()

    best_item = None
    best_score = 0.0

    for item in search_results:
        score = calculator.calculate_match_score(request, item)
        if score > best_score:
            best_score = score
            best_item = item

    # Only return if score is above threshold (configurable)
    if best_score >= min_threshold:
        return best_item

    return None
