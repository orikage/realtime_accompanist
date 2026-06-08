from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_pages_site_is_self_contained_static_demo():
    index = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
    app = (ROOT / "site" / "app.js").read_text(encoding="utf-8")
    styles = (ROOT / "site" / "styles.css").read_text(encoding="utf-8")

    assert "./app.js" in index
    assert "./styles.css" in index
    assert "/api/" not in app
    assert "Demo C" in index
    assert "estimateKeys" in app
    assert "Generated Accompaniment Events" in index
    assert "@media (max-width: 860px)" in styles

