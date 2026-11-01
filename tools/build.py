"""Build index.html (GitHub Pages) from src/aflyt.html (the artifact body)."""
import pathlib
root = pathlib.Path(__file__).resolve().parent.parent
src = (root / "src" / "story.html").read_text(encoding="utf-8")
head = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#0b0f14">
<style>html{box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}</style>
"""
(root / "index.html").write_text(head + src + "\n</html>\n", encoding="utf-8")
print("built index.html", len(head + src), "bytes")
