"""Ports — interfaces application depends on, implemented in infrastructure.

Grouped by domain like `services/`: `source/`, `scraping/`. Import from the
subpackage (`from source_service.application.ports.scraping import PageCrawler`); nothing
is re-exported from here.
"""
