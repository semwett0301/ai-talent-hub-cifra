from source_service.application.web_crawl.html_meta import (
    extract_html_metadata,
    extract_publication_date_signal,
)


def test_jsonld_article_date_is_high_confidence():
    html = """
    <html lang="ru"><head>
      <script type="application/ld+json">
      {"@context":"https://schema.org","@type":"NewsArticle","headline":"Test","datePublished":"2026-09-03T10:00:00+03:00"}
      </script>
    </head><body></body></html>
    """
    meta = extract_html_metadata(html)
    signal = extract_publication_date_signal(html)
    assert meta["title"] == "Test"
    assert signal.source == "json_ld"
    assert signal.value == "2026-09-03T10:00:00+03:00"
    assert signal.confidence > 0.95


def test_random_body_date_is_not_treated_as_publication_date():
    html = """<html><body><h1>Новость</h1><p>Компания сообщила, что 1 сентября 2026 года состоялась встреча.</p></body></html>"""
    signal = extract_publication_date_signal(html)
    assert signal.value is None
    assert signal.confidence == 0.0


def test_time_datetime_is_accepted():
    html = """<html><body><article><h1>Title</h1><time datetime="2026-09-03T12:30:00+03:00">3 сентября 2026</time></article></body></html>"""
    signal = extract_publication_date_signal(html)
    assert signal.source == "time_element"
    assert signal.value.startswith("2026-09-03")


def test_visible_date_detector_accepts_article_header_without_site_selector():
    html = """<html><body><article><div class="article-header"><span class="article-header__date">3 сентября 2026 в 12:30</span><h1>Title</h1></div></article></body></html>"""
    signal = extract_publication_date_signal(html)
    assert signal.source == "visible_dom"
    assert signal.value == "3 сентября 2026 в 12:30"


def test_visible_date_detector_ignores_related_article_dates():
    html = """<html><body><article><h1>Title</h1><div class="entry-meta published-date">3 сентября 2026</div><p>Body</p></article><aside class="related"><span class="date">4 сентября 2026</span></aside></body></html>"""
    signal = extract_publication_date_signal(html)
    assert signal.source == "visible_dom"
    assert signal.value == "3 сентября 2026"


def test_visible_date_detector_prefers_date_in_the_h1_header_block():
    html = """<html><body><article><div class="article-header"><span class="date">3 сентября 2026 в 12:30</span><h1>Title</h1></div><div class="materials__date">09.04.2026</div></article></body></html>"""
    signal = extract_publication_date_signal(html)
    assert signal.source == "visible_dom"
    assert signal.value == "3 сентября 2026 в 12:30"
