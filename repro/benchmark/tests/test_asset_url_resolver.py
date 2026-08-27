from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
CHROME = shutil.which("google-chrome") or shutil.which("chromium")


class ScriptSourceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.sources: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if tag != "script":
            return
        source = dict(attrs).get("src")
        if source:
            self.sources.append(source)


@unittest.skipUnless(CHROME, "A Chromium-compatible browser is required")
class AssetUrlResolverTests(unittest.TestCase):
    def run_resolver(self) -> list[str]:
        asset_script = (REPO_ROOT / "assets/js/asset-url.js").as_uri()
        html = f"""<!doctype html>
<html>
  <body>
    <pre id="result"></pre>
    <script src="{asset_script}"></script>
    <script>
      const resolver = window.AmamAssetUrl && window.AmamAssetUrl.toAssetUrl;
      const output = resolver ? [
        resolver(
          "data/local/4130-steel/images/4130 x 10 (1).jpg",
          "/w/AMAM-D580/index.html"
        ),
        resolver(
          "data/local/4130-steel/images/4130 x 10 (1).jpg",
          "/index.html"
        ),
        resolver(
          "https://example.org/reference image.jpg",
          "/w/AMAM-D580/index.html"
        )
      ] : ["resolver-missing", "resolver-missing", "resolver-missing"];
      document.getElementById("result").textContent = JSON.stringify(output);
    </script>
  </body>
</html>
"""

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            runner = tmp_path / "asset-url-runner.html"
            runner.write_text(html, encoding="utf-8")
            completed = subprocess.run(
                [
                    str(CHROME),
                    "--headless",
                    "--no-sandbox",
                    "--disable-gpu",
                    "--disable-dev-shm-usage",
                    "--allow-file-access-from-files",
                    f"--user-data-dir={tmp_path / 'chrome-profile'}",
                    "--dump-dom",
                    runner.as_uri(),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

        match = re.search(r'<pre id="result">(.*?)</pre>', completed.stdout)
        self.assertIsNotNone(match, completed.stdout)
        return json.loads(match.group(1))

    def test_anonymous_webview_uses_working_api_file_route(self) -> None:
        resolved = self.run_resolver()
        self.assertEqual(
            resolved[0],
            "/api/repo/AMAM-D580/file/data/local/4130-steel/images/"
            "4130%20x%2010%20%281%29.jpg",
        )

    def test_local_and_external_urls_keep_their_expected_scope(self) -> None:
        resolved = self.run_resolver()
        self.assertEqual(
            resolved[1],
            "data/local/4130-steel/images/4130%20x%2010%20(1).jpg",
        )
        self.assertEqual(resolved[2], "https://example.org/reference image.jpg")


class WebsiteScriptReferenceTests(unittest.TestCase):
    def test_pages_reference_scripts_that_exist(self) -> None:
        """app.js is renamed when it changes, to get past the host's edge cache.

        The pages are the only place those filenames appear, so a rename that
        misses one would ship a page whose script 404s.
        """
        for page in ("index.html", "report.html"):
            parser = ScriptSourceParser()
            parser.feed((REPO_ROOT / page).read_text(encoding="utf-8"))
            local = [src for src in parser.sources if not src.startswith("http")]
            self.assertTrue(local, f"{page} references no local scripts")
            for source in local:
                with self.subTest(page=page, source=source):
                    self.assertTrue(
                        (REPO_ROOT / source).is_file(),
                        f"{page} references missing script {source}",
                    )


if __name__ == "__main__":
    unittest.main()
