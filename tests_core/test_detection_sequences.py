import json
from pathlib import Path
import cv2
import numpy as np
import pytest
from simplemotocam.studio_backend import backend_catalog
from simplemotocam.studio_engine import StudioPipeline, demo_frame

ROOT = Path(__file__).resolve().parents[1]
LESSONS = json.loads(
    (ROOT / "src/simplemotocam/studio_sequences.json").read_text(encoding="utf-8")
)["lessons"]
legacy = pytest.mark.skipif(
    not backend_catalog()["opencv24"]["available"],
    reason="Native OpenCV 2.4 worker required",
)


def test_detection_catalog_sources_and_graphs():
    assert len(LESSONS) == 6
    for item in LESSONS:
        assert item["state"]["backend"] == {"id": "opencv24", "version": "2.4.13.7"}
        assert item["sources"]
        for source in item["sources"]:
            assert source.get("url", "").startswith("https://") or (
                source.get("file") and source.get("pages") and source.get("pdfPages")
            )
        if item["sample"]:
            assert (
                ROOT / "docs/opencv-2.4-manuals/learning" / item["sample"]
            ).is_file()


def test_detection_prose_covers_every_language():
    bundle = (ROOT / "docs/opencv-2.4-manuals/learning/sequences-data.js").read_text(
        encoding="utf-8"
    )
    data = json.loads(bundle.split("window.SEQUENCE_DATA = ", 1)[1].rstrip(";\n"))
    registry = json.loads(
        (ROOT / "tools/doc_translate/languages.json").read_text(encoding="utf-8")
    )
    assert set(data["catalogs"]) == {l["id"] for l in registry}
    expected = set(data["catalogs"]["en"]["strings"])
    for lang, catalog in data["catalogs"].items():
        assert set(catalog["strings"]) == expected
        assert all(
            isinstance(v, str) and v.strip() for v in catalog["strings"].values()
        )
        if lang not in ("en", "sl"):
            assert catalog["status"] == "machine-unreviewed"


@legacy
@pytest.mark.parametrize("item", LESSONS, ids=[l["id"] for l in LESSONS])
def test_detection_results_match_teaching_claims(item):
    pipeline = StudioPipeline(item["state"])
    key = item["state"]["view"]["result"]
    if item["sample"]:
        frame = cv2.imread(
            str(ROOT / "docs/opencv-2.4-manuals/learning" / item["sample"])
        )
        values, _ = pipeline.process(frame)
    else:
        first, _ = pipeline.process(demo_frame(0))
        assert not first[key].any()
        values, _ = pipeline.process(demo_frame(1))
    mask = values[key]
    assert set(np.unique(mask)) <= {0, 1}
    assert mask.sum() > 0
    if item["id"] == "red-part":
        expected = np.zeros((240, 320), np.float32)
        expected[60:175, 40:140] = 1
        np.testing.assert_array_equal(mask, expected)
    elif item["id"] == "bright-regions":
        assert cv2.connectedComponents(mask.astype(np.uint8), 8)[0] - 1 == 2
        assert mask[90, 60] == 0 and mask[206, 151] == 0 and mask[100, 230] == 1
    elif item["id"] == "lines":
        assert mask[50:65, 30:290].sum() > 300
        assert mask[195:210, 30:50].sum() == 0
    elif item["id"] == "edges":
        assert mask[100:140, 120:200].sum() < 10
        assert mask[60:70, 90:230].sum() > 100
    elif item["id"] == "uneven-light":
        expected = np.zeros((240, 320), np.float32)
        expected[50:190, 70:78] = 1
        expected[50:190, 235:243] = 1
        np.testing.assert_array_equal(mask, expected)
