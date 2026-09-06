# duma

- `url.py` — strict HTTPS host/path allow-list, preventing arbitrary URL fetching.
- `page_parser.py` — bill identity, furthest populated stage, latest source timestamp,
  publication date, and latest actual Word bill-text link from server-rendered HTML.
- `docx_parser.py` — OOXML paragraph/table extraction.
- `client.py` — bounded async downloads composing both parsers behind `NpaSource`.
