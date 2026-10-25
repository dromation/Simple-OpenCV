"""Bundle source-referenced detection lessons and their offline prose catalogs."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/doc_translate"))
from translate import read, digest, VERSION


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args()
    guide = ROOT / "docs/opencv-2.4-manuals/learning"
    source = read(guide / "sequence-i18n/en.json")
    glossary = read(ROOT / "tools/doc_translate/protected.json")
    expected = digest([source["strings"], glossary, VERSION])
    catalogs = {}
    for item in read(ROOT / "tools/doc_translate/languages.json"):
        lang = item["id"]
        file = guide / "sequence-i18n" / f"{lang}.json"
        if args.preview and not file.exists():
            continue
        catalog = read(file)
        if set(catalog["strings"]) != set(source["strings"]):
            raise ValueError(f"Incomplete sequence catalog: {lang}")
        if lang not in ("en", "sl") and catalog.get("sourceDigest") != expected:
            raise ValueError(f"Stale sequence catalog: {lang}")
        if any(not str(v).strip() for v in catalog["strings"].values()):
            raise ValueError(f"Empty text: {lang}")
        catalogs[lang] = catalog
    data = read(ROOT / "src/simplemotocam/studio_sequences.json")
    data["catalogs"] = catalogs
    ui = json.loads(
        (ROOT / "src/simplemotocam/studio_ui/i18n.js")
        .read_text(encoding="utf-8")
        .split("window.STUDIO_I18N = ", 1)[1]
        .rstrip(";\n")
    )
    data["labels"] = {
        lang: {
            key: value
            for key, value in catalog["strings"].items()
            if key.endswith("Block") or key == "source"
        }
        for lang, catalog in ui.items()
    }
    (guide / "sequences-data.js").write_text(
        "window.SEQUENCE_DATA = " + json.dumps(data, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )
    print(
        f'Bundled {len(data["lessons"])} detection sequences in {len(catalogs)} languages.'
    )


if __name__ == "__main__":
    main()
