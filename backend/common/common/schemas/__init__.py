"""Domain schemas — DB-backed data shapes (SQLAlchemy ORM).

Plain in-memory shapes (no DB involvement) live in `../entities/` instead.
"""

from common.schemas.news import News
from common.schemas.news_cluster_ranking import NewsClusterRanking
from common.schemas.npa import Npa
from common.schemas.npa_version import NpaVersion
from common.schemas.rss_link import RssLink
from common.schemas.source import Source

__all__ = ["News", "NewsClusterRanking", "Npa", "NpaVersion", "RssLink", "Source"]
