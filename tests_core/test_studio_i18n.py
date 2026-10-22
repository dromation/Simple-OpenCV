"""Guard shipped UI catalogs, including persistent terminology corrections."""
import json
import re
from pathlib import Path

from simplemotocam.studio import ROOT, UI
from simplemotocam.studio_engine import KINDS


def test_all_interface_languages_have_every_key():
    bundle = (UI / 'i18n.js').read_text(encoding='utf-8')
    catalogs = json.loads(bundle.split('window.STUDIO_I18N = ', 1)[1].rstrip(';\n'))
    registry = json.loads((ROOT / 'tools/doc_translate/languages.json').read_text(encoding='utf-8'))
    assert set(catalogs) == {lang['id'] for lang in registry}
    source = catalogs['en']['strings']
    html = (UI / 'index.html').read_text(encoding='utf-8')
    app = (UI / 'app.js').read_text(encoding='utf-8')
    required = set(re.findall(r'data-i18n(?:-aria|-alt|-title|-placeholder)?="([^"]+)"', html))
    required.update(re.findall(r'\bt\("([^"]+)"\)', app))
    required.update(kind + 'Block' for kind in KINDS if kind != 'source')
    assert required <= set(source)
    for locale, item in catalogs.items():
        assert set(item['strings']) == set(source), locale
        assert all(isinstance(v, str) and v.strip() for v in item['strings'].values()), locale
        if locale not in ('sl', 'en'):
            assert item['status'] == 'machine-unreviewed'
            corrections = json.loads((ROOT / 'tools/doc_translate/studio-corrections' / f'{locale}.json').read_text(encoding='utf-8'))
            for key, entry in corrections['entries'].items():
                assert entry['source'] == source[key]
                assert item['strings'][key] == entry['translation']
