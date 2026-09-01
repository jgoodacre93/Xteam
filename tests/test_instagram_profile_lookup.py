import re
import sys
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = ROOT / 'Ig_information_gathering' / 'Core_files'
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

MODULE_PATH = CORE_DIR / 'Ig_information_gathering.py'
spec = importlib.util.spec_from_file_location('ig_lookup', MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_build_instagram_headers_contains_browser_and_app_id():
    headers = mod.build_instagram_headers()
    assert 'User-Agent' in headers
    assert 'X-IG-App-ID' in headers
    assert headers['X-IG-App-ID'] == mod.IG_APP_ID


def test_profile_url_is_normalized_for_username():
    username = 'gramup'
    url = mod.build_profile_url(username)
    assert url.startswith('https://www.instagram.com/')
    assert username in url
    assert re.search(r'/gramup/?$', url)


def test_login_page_is_rejected_as_fake_profile_data():
    html = '<html><head><meta property="og:title" content="Instagram" /><meta name="description" content="Create an account or log in to Instagram" /></head></html>'
    url = 'https://www.instagram.com/accounts/login/?next=%2Fgramup%2F'
    assert mod.is_public_profile_response(url, html, 'gramup') is False
