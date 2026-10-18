from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_home_returns_200():
    response = client.get("/")
    assert response.status_code == 200


def test_home_contains_name():
    response = client.get("/")
    assert "Sheikh Haseeb" in response.text


def test_home_contains_sections():
    response = client.get("/")
    html = response.text
    assert 'id="about"' in html
    assert 'id="skills"' in html
    assert 'id="projects"' in html
    assert 'id="experience"' in html
    assert 'id="contact"' in html


def test_home_contains_cogveel():
    response = client.get("/")
    assert "Cogveel" in response.text


def test_proprietary_badges():
    response = client.get("/")
    assert "Proprietary" in response.text
    assert "Open Source" in response.text


def test_footer_contains_last_updated():
    response = client.get("/")
    assert "Last updated:" in response.text


def test_templates_contain_no_hardcoded_company_names():
    from pathlib import Path

    templates_dir = Path(__file__).resolve().parent.parent / "app" / "templates"
    for template_file in templates_dir.rglob("*.html"):
        content = template_file.read_text(encoding="utf-8")
        assert (
            "Cogveel" not in content
        ), f"Found hardcoded 'Cogveel' in template {template_file.name}"
        assert (
            "Finna" not in content
        ), f"Found hardcoded 'Finna' in template {template_file.name}"


def test_api_config_endpoint():
    response = client.get("/api/config")
    assert response.status_code == 200
    data = response.json()
    assert "assistant_name" in data
    assert "suggestion_chips" in data
    assert isinstance(data["suggestion_chips"], list)
    assert len(data["suggestion_chips"]) > 0
    assert "current_status" in data
    assert "last_updated" in data


def test_resume_download_success():
    response = client.get("/resume")
    assert response.status_code == 200
    assert "application/pdf" in response.headers.get("content-type", "")
    assert "attachment" in response.headers.get("content-disposition", "")
    assert "Sheikh_Haseeb_Resume.pdf" in response.headers.get("content-disposition", "")


def test_resume_view_success():
    response = client.get("/resume/view")
    assert response.status_code == 200
    assert "application/pdf" in response.headers.get("content-type", "")


def test_resume_404_handling(monkeypatch):
    import app.routes.pages as pages_module
    from pathlib import Path

    non_existent = Path("/tmp/non_existent_resume_file_xyz.pdf")
    monkeypatch.setattr(pages_module, "RESUME_PATH", non_existent)

    download_res = client.get("/resume")
    assert download_res.status_code == 404
    assert "Resume is currently unavailable" in download_res.json()["detail"]

    view_res = client.get("/resume/view")
    assert view_res.status_code == 404
    assert "Resume is currently unavailable" in view_res.json()["detail"]


def test_home_page_contains_resume_buttons():
    response = client.get("/")
    assert response.status_code == 200
    assert 'href="/resume"' in response.text
    assert "Download Resume" in response.text


def test_seo_meta_tags_and_structured_data():
    response = client.get("/")
    assert response.status_code == 200
    html = response.text
    # Meta tags driven by portfolio.json
    assert '<link rel="canonical" href="https://sheikh-haseeb.onrender.com" />' in html
    assert '<meta property="og:title" content="Sheikh Haseeb — AI/ML Engineer | Portfolio &amp; Haze AI" />' in html
    assert '<meta name="twitter:card" content="summary_large_image" />' in html
    assert 'og-image.png' in html
    assert '/static/logo.svg' in html
    assert '/static/favicon.ico' in html
    # JSON-LD Schema.org Person
    assert '"@type": "Person"' in html
    assert '"Sheikh Haseeb"' in html
    assert '"https://schema.org"' in html


def test_robots_txt():
    response = client.get("/robots.txt")
    assert response.status_code == 200
    assert "text/plain" in response.headers.get("content-type", "")
    assert "User-agent: *" in response.text
    assert "Disallow: /api/" in response.text
    assert "Sitemap: https://sheikh-haseeb.onrender.com/sitemap.xml" in response.text


def test_sitemap_xml():
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    assert "xml" in response.headers.get("content-type", "")
    assert "<urlset" in response.text
    assert "<loc>https://sheikh-haseeb.onrender.com/</loc>" in response.text
    assert "<loc>https://sheikh-haseeb.onrender.com/resume/view</loc>" in response.text


def test_static_og_and_favicon():
    og_res = client.get("/static/images/og-image.png")
    assert og_res.status_code == 200
    assert "image/png" in og_res.headers.get("content-type", "")

    fav_res = client.get("/static/favicon.ico")
    assert fav_res.status_code == 200


def test_custom_404_page():
    # Non-existent web page returns HTML 404 page
    res = client.get("/non-existent-page-url")
    assert res.status_code == 404
    assert "Page Not Found" in res.text
    assert "Back to Home" in res.text
    assert "text/html" in res.headers.get("content-type", "")

    # Non-existent API route returns JSON 404
    api_res = client.get("/api/non-existent")
    assert api_res.status_code == 404
    assert api_res.headers.get("content-type", "").startswith("application/json")



