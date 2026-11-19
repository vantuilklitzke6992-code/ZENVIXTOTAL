import json
import struct
from pathlib import Path

from app import app as flask_app


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_manifest_has_installation_metadata_and_icons():
    with flask_app.test_client() as client:
        response = client.get("/static/manifest.webmanifest")

    assert response.status_code == 200
    manifest = json.loads(response.get_data(as_text=True))
    assert manifest["name"] == "Zenvix Connect"
    assert manifest["short_name"] == "Zenvix"
    assert manifest["start_url"] == "/"
    assert manifest["scope"] == "/"
    assert manifest["display"] == "standalone"

    icons = {icon["src"]: icon for icon in manifest["icons"]}
    assert icons["/static/icons/icon-192.png"]["sizes"] == "192x192"
    assert icons["/static/icons/icon-512.png"]["sizes"] == "512x512"
    maskable_icon = icons["/static/icons/icon-maskable-512.png"]
    assert maskable_icon["purpose"] == "maskable"


def test_pwa_icons_are_valid_pngs_with_declared_dimensions():
    expected_sizes = {
        "icon-192.png": (192, 192),
        "icon-512.png": (512, 512),
        "icon-maskable-512.png": (512, 512),
        "apple-touch-icon.png": (180, 180),
    }

    with flask_app.test_client() as client:
        for filename, expected_size in expected_sizes.items():
            response = client.get(f"/static/icons/{filename}")
            assert response.status_code == 200
            assert response.data.startswith(b"\x89PNG\r\n\x1a\n")
            width, height = struct.unpack(">II", response.data[16:24])
            assert (width, height) == expected_size


def test_service_worker_is_served_at_root_with_wide_scope():
    with flask_app.test_client() as client:
        response = client.get("/service-worker.js")

    assert response.status_code == 200
    assert response.mimetype == "application/javascript"
    assert response.headers["Service-Worker-Allowed"] == "/"
    assert response.headers["Cache-Control"] == "no-cache"


def test_service_worker_caches_only_public_pwa_assets():
    worker = (PROJECT_ROOT / "static" / "service-worker.js").read_text(
        encoding="utf-8"
    )
    cacheable_paths = {
        "/static/manifest.webmanifest",
        "/static/icons/icon-192.png",
        "/static/icons/icon-512.png",
        "/static/icons/icon-maskable-512.png",
        "/static/icons/apple-touch-icon.png",
    }

    for path in cacheable_paths:
        assert f'"{path}"' in worker
    for private_path in ("/login", "/cadastro", "/dashboard", "/chat"):
        assert f'"{private_path}"' not in worker

    assert 'event.request.method !== "GET"' in worker
    assert "requestUrl.origin !== self.location.origin" in worker


def test_layout_links_manifest_icons_and_mobile_metadata():
    with flask_app.test_client() as client:
        response = client.get("/")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'rel="manifest"' in html
    assert "apple-touch-icon" in html
    assert 'name="apple-mobile-web-app-capable" content="yes"' in html
    assert 'name="mobile-web-app-capable" content="yes"' in html


def test_main_script_registers_service_worker_only_in_secure_contexts():
    script = (PROJECT_ROOT / "static" / "js" / "main.js").read_text(
        encoding="utf-8"
    )

    assert '"serviceWorker" in navigator && window.isSecureContext' in script
    registration_call = (
        'navigator.serviceWorker.register("/service-worker.js", '
        '{ scope: "/" })'
    )
    assert registration_call in script
