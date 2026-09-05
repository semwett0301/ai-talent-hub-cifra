from source_service.domain import Site


def test_site_owns_its_host_and_subdomains_only():
    site = Site(url="https://www.Example.com/", name="Example")

    assert site.seed == "https://www.example.com/"
    assert site.label == "Example"
    assert site.owns("https://example.com/news/1")
    assert site.owns("https://media.example.com/news/1")
    assert not site.owns("https://evil.test/news/1")


def test_allowed_domains_extend_the_site():
    site = Site(url="https://example.com", allowed_domains=["partner.org"])
    assert site.owns("https://news.partner.org/x")
    assert not site.owns("https://example.net/x")
