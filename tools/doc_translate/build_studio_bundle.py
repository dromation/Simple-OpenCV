"""Validate and bundle the studio interface catalogs for offline use."""
import json
from pathlib import Path

from translate import ROOT, VERSION, digest, read


def main():
    ui = ROOT / "src/simplemotocam/studio_ui"
    source = read(ui / "i18n/en.json")
    glossary = read(Path(__file__).with_name("studio-protected.json"))
    expected = digest([source["strings"], glossary, VERSION])
    catalogs = {}
    for language in read(Path(__file__).with_name("languages.json")):
        locale = language["id"]
        item = read(ui / "i18n" / f"{locale}.json")
        if set(item["strings"]) != set(source["strings"]):
            raise ValueError(f"Incomplete studio catalog: {locale}")
        if any(not isinstance(v, str) or not v.strip() for v in item["strings"].values()):
            raise ValueError(f"Empty studio translation: {locale}")
        if locale not in ("sl", "en") and item.get("sourceDigest") != expected:
            raise ValueError(f"Stale studio translation: {locale}")
        corrections = Path(__file__).with_name("studio-corrections") / f"{locale}.json"
        if corrections.exists():
            overrides = read(corrections)
            for key, correction in overrides["entries"].items():
                if correction["source"] != source["strings"].get(key):
                    raise ValueError(f"Stale studio correction: {locale}/{key}")
                if not correction["translation"].strip():
                    raise ValueError(f"Empty studio correction: {locale}/{key}")
                item["strings"][key] = correction["translation"]
            item["correctionStatus"] = overrides["status"]
        catalogs[locale] = item
    (ui / "i18n.js").write_text(
        "// Generated offline interface catalogs; machine drafts are labelled in the UI.\n"
        + "window.STUDIO_I18N = " + json.dumps(catalogs, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )
    print(f"Bundled {len(catalogs)} studio languages, {len(source['strings'])} keys each.")


if __name__ == "__main__":
    main()
