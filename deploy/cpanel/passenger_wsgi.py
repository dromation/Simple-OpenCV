"""cPanel startup file; application root must be outside public_html."""
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))


def load_application():
    try:
        settings = json.loads((ROOT / 'hosting.json').read_text(encoding='utf-8'))
        if settings.get('opencv24_worker'):
            worker = Path(settings['opencv24_worker'])
            os.environ['SIMPLEMOTOCAM_OPENCV24_WORKER'] = str(worker if worker.is_absolute() else ROOT / worker)
        from simplemotocam.studio_web import WebApplication
        return WebApplication(settings, ROOT / 'private' / 'sessions')
    except (OSError, ValueError, ImportError):
        import traceback
        traceback.print_exc()  # Details go only to the private Passenger log.
        def unavailable(environ, start_response):
            message = b'SimpleMotocam setup incomplete. Follow INSTALL-CPANEL.md in the application folder; check hosting.json and Python dependencies. Restart the Python app after setup.'
            start_response('503 Service Unavailable', [('Content-Type', 'text/plain; charset=utf-8'), ('Content-Length', str(len(message))), ('Cache-Control', 'no-store')])
            return [message]
        return unavailable


application = load_application()
