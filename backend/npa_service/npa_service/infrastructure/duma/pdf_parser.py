"""Extract readable text from an official PDF bill document."""

import subprocess
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from pypdf import PdfReader

from npa_service.application.errors import NpaDocumentError


class PdfParser:
    def parse(self, content: bytes) -> str:
        try:
            reader = PdfReader(BytesIO(content))
            text = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
        except Exception as error:
            raise NpaDocumentError("bill text is not a readable PDF document") from error
        return text or self.__ocr(content)

    def __ocr(self, content: bytes) -> str:
        """Recognize scanned official documents, bounded to the first 20 pages."""
        try:
            with TemporaryDirectory(prefix="cifra-npa-") as directory:
                root = Path(directory)
                pdf_path = root / "document.pdf"
                pdf_path.write_bytes(content)
                output_prefix = root / "page"
                subprocess.run(
                    [
                        "pdftoppm",
                        "-r",
                        "200",
                        "-f",
                        "1",
                        "-l",
                        "20",
                        "-png",
                        str(pdf_path),
                        str(output_prefix),
                    ],
                    check=True,
                    capture_output=True,
                    timeout=90,
                )
                pages = sorted(root.glob("page-*.png"))
                text = "\n".join(
                    subprocess.run(
                        ["tesseract", str(page), "stdout", "-l", "rus+eng"],
                        check=True,
                        capture_output=True,
                        text=True,
                        timeout=30,
                    ).stdout.strip()
                    for page in pages
                ).strip()
        except (OSError, subprocess.SubprocessError) as error:
            raise NpaDocumentError("bill PDF could not be recognized") from error
        if not text:
            raise NpaDocumentError("bill PDF document contains no readable text")
        return text
