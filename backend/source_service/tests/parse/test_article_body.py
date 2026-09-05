from source_service.application.parse import article_body, choose_text_container, word_count

PARAGRAPH = "<p>" + "word " * 60 + "</p>"
ARTICLE = f"<article><h1>Title</h1>{PARAGRAPH}{PARAGRAPH}</article>"
HTML = f"<html><body><nav><a href='/a'>Menu</a></nav>{ARTICLE}<footer>legal</footer></body></html>"


def test_container_prefers_article_when_it_holds_the_prose():
    assert choose_text_container(HTML, min_words=80) == "article"


def test_container_falls_back_to_document_when_too_thin():
    assert choose_text_container("<html><body><article>hi</article></body></html>", 80) is None


def test_body_uses_the_selector_and_drops_navigation():
    body = article_body(HTML, markdown="fallback", selector="article", min_words=80)
    assert "Menu" not in body
    assert word_count(body) >= 120


def test_body_falls_back_to_markdown_when_selector_is_thin():
    assert article_body("<article>short</article>", "the markdown", "article", 80) == "the markdown"
