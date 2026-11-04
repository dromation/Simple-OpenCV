"""Read-only deployment check; never prints the password or environment."""
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root/'src'))


def main():
    settings = json.loads((root/'hosting.json').read_text(encoding='utf-8'))
    if settings.get('opencv24_worker'):
        import os
        path = Path(settings['opencv24_worker'])
        os.environ['SIMPLEMOTOCAM_OPENCV24_WORKER'] = str(path if path.is_absolute() else root/path)
    from simplemotocam.studio_web import WebApplication
    from simplemotocam.studio_backend import backend_catalog
    from simplemotocam.studio import StudioSession
    WebApplication(settings, root/'private/sessions')
    catalog = backend_catalog()
    print('Python:', sys.version.split()[0])
    for name, entry in catalog.items():
        print(name, 'available:', entry['available'], 'version:', entry.get('version'))
    import tempfile
    with tempfile.TemporaryDirectory() as folder:
        session = StudioSession(folder, backend=settings.get('backend', 'opencv24'))
        try:
            result = session.frame()
            print('Demo frame:', result['size'], 'engine:', result['backend'])
        finally:
            session.close()
    print('PASS. Restart the Python app in cPanel, then open the HTTPS domain.')


if __name__ == '__main__':
    main()
