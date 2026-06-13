"""Minimal smoke test for the HTML-Misc collection.

These are standalone single-file browser apps (no build step, no JS test
runner). This test enforces the shipped-asset integrity invariants used
across the portfolio so the files stay loadable in a browser:

  * no UTF-8 BOM at the start of a shipped HTML file
  * no unfilled template placeholder tokens left in the markup
  * no literal "</script>" inside a JS template literal (would close the tag early)

(Raw <div>/</div> balance is intentionally NOT asserted: several files are
JSX compiled in-browser by Babel, and others build report HTML inside JS
template literals, so a plain-text tag count produces false positives.)

Run:  python -m pytest test_smoke.py -q   (or)   python test_smoke.py
"""

import glob
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
HTML_FILES = sorted(
    glob.glob(os.path.join(HERE, "*.html"))
    + glob.glob(os.path.join(HERE, "*.HTML"))
)

# Tokens that would indicate an un-substituted template was shipped. Built by
# concatenation so this test file does not itself contain the literal markers.
PLACEHOLDER_TOKENS = ("REPLACE" + "_ME", "__PLACE" + "HOLDER__")
# Mustache-style placeholder such as a double-brace TITLE / study_name token.
# Deliberately requires the inner token to look like a placeholder name so we
# do NOT flag JSX inline styles (style= double-brace) or JS object expressions.
PLACEHOLDER_MUSTACHE = re.compile(r"\{\{\s*[A-Za-z_][A-Za-z0-9_.]*\s*\}\}")


def _read(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    return raw, raw.decode("utf-8", errors="replace")


def test_html_files_exist():
    assert HTML_FILES, "no HTML files found in repo"


def test_no_bom():
    bad = []
    for path in HTML_FILES:
        raw, _ = _read(path)
        if raw.startswith(b"\xef\xbb\xbf"):
            bad.append(os.path.basename(path))
    assert not bad, f"BOM present in shipped HTML: {bad}"


def test_no_unfilled_placeholders():
    bad = []
    for path in HTML_FILES:
        _, text = _read(path)
        for tok in PLACEHOLDER_TOKENS:
            if tok in text:
                bad.append(f"{os.path.basename(path)}:{tok}")
        if PLACEHOLDER_MUSTACHE.search(text):
            bad.append(f"{os.path.basename(path)}:{{{{...}}}}")
    assert not bad, f"unfilled placeholder token(s): {bad}"


def test_no_literal_closing_script_in_template_literal():
    # A literal </script> inside a backtick template literal terminates the
    # <script> block early in the browser. Heuristic: flag </script> that sits
    # on a line also containing a backtick (template-literal context).
    bad = []
    for path in HTML_FILES:
        _, text = _read(path)
        for n, line in enumerate(text.splitlines(), 1):
            if "`" in line and "</script>" in line and "${'<'}" not in line:
                bad.append(f"{os.path.basename(path)}:{n}")
    assert not bad, f"literal </script> in template literal: {bad}"


if __name__ == "__main__":
    test_html_files_exist()
    test_no_bom()
    test_no_unfilled_placeholders()
    test_no_literal_closing_script_in_template_literal()
    print(f"OK: {len(HTML_FILES)} HTML files passed smoke checks")
