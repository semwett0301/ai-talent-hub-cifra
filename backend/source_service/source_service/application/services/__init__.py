"""Application services, grouped by domain: `source/` and `web/`.

Use cases plus the steps they are composed of — a step (`HubDiscovery`, `DateResolution`)
is not a use case, but it holds ports and thresholds, so it belongs here and not in the
domain. Import from the subpackage (`from source_service.application.services.web import
WebCrawl`); nothing is re-exported from here.
"""
