"""Extract readable text from legacy Microsoft Word .doc documents."""

import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from npa_service.application.errors import NpaDocumentError


class DocParser:
    def parse(self, content: bytes) -> str:
        try:
            with TemporaryDirectory(prefix="cifra-npa-") as directory:
                path = Path(directory) / "document.doc"
                path.write_bytes(content)
                result = subprocess.run(
                    ["antiword", "-m", "UTF-8.txt", str(path)],
                    check=True,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=30,
                )
        except (OSError, subprocess.SubprocessError) as error:
            raise NpaDocumentError("bill text is not a readable .doc document") from error
        text = result.stdout.strip()
        if not text:
            raise NpaDocumentError("bill .doc document contains no readable text")
        return text
