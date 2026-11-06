"""Phase 6 smoke: dashboard and its static files are served offline from the container."""
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.parametrize('path,kind', [
    ('/dashboard', 'text/html'),
    ('/static/main.js', 'javascript'),
    ('/static/office3d.js', 'javascript'),
    ('/static/office-layout.js', 'javascript'),
    ('/static/office-props.js', 'javascript'),
    ('/static/panels.js', 'javascript'),
    ('/static/styles.css', 'text/css'),
    ('/static/vendor/three.module.min.js', 'javascript'),
    ('/static/vendor/OrbitControls.js', 'javascript'),
    ('/static/vendor/CSS2DRenderer.js', 'javascript'),
], ids=lambda v: v if isinstance(v, str) and v.startswith('/') else None)
async def test_dashboard_assets_served(path, kind):
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as c:
        r = await c.get(path)
    assert r.status_code == 200 and kind in r.headers['content-type']


async def test_dashboard_uses_local_three_and_no_external_urls():
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as c:
        html = (await c.get('/dashboard')).text
    assert '/static/vendor/three.module.min.js' in html and 'id="office"' in html
    assert 'http://' not in html and 'https://' not in html


async def test_static_files_are_revalidated_so_updates_are_not_stale():
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as c:
        for path in ('/static/styles.css', '/static/panels.js', '/dashboard'):
            assert (await c.get(path)).headers['cache-control'] == 'no-cache'
