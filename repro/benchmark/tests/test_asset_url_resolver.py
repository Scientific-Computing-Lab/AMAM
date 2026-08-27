from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
CHROME = shutil.which("google-chrome") or shutil.which("chromium")


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


if __name__ == "__main__":
    unittest.main()
