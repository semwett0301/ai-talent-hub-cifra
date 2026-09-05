"""Ports — interfaces application depends on, implemented in infrastructure.

Grouped by domain: `source/`, `scraping/` (every port that reaches the open web —
the RSS reader included, so it is wider than `services/web`). Import from the
subpackage (`from source_service.application.ports.scraping import PageCrawler`); nothing
is re-exported from here.
"""
