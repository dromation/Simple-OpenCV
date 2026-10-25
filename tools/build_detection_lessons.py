"""Build authored detection lessons and deterministic demonstration images.
Run with the project's Python; translation is a separate optional step.
"""

import json
from pathlib import Path
import numpy as np
import cv2
from simplemotocam.studio_catalog import recipe

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / "docs/opencv-2.4-manuals/learning"
BOOK = "Joseph Howse, OpenCV Computer Vision with Python, Packt, 2013"
TRUCCO = "Emanuele Trucco & Alessandro Verri, Introductory Techniques for 3-D Computer Vision, Prentice Hall, 1998"
WEB = "https://docs.opencv.org/2.4.13.7/doc/tutorials/"
lessons = []


def add(
    id, title, goal, order, tune, expected, caution, formula, specs, refs, sample=True
):
    entry = recipe("lesson-" + id, title[0], specs)
    entry["state"]["backend"] = {"id": "opencv24", "version": "2.4.13.7"}
    lessons.append(
        dict(
            id=id,
            title=dict(zip(("en", "sl"), title)),
            goal=dict(zip(("en", "sl"), goal)),
            order=dict(zip(("en", "sl"), order)),
            tune=dict(zip(("en", "sl"), tune)),
            expected=dict(zip(("en", "sl"), expected)),
            caution=dict(zip(("en", "sl"), caution)),
            formula=formula,
            state=entry["state"],
            sources=refs,
            sample=f"examples/{id}.png" if sample else None,
        )
    )


def book(pages, pdf):
    return {
        "title": BOOK,
        "file": "OpenCV243 Computer Vision with Python.pdf",
        "pages": pages,
        "pdfPages": pdf,
    }


def trucco(pages, pdf):
    return {
        "title": TRUCCO,
        "file": "Zaznavanje - trucco_verri.pdf",
        "pages": pages,
        "pdfPages": pdf,
    }


def web(title, path):
    return {"title": title, "url": WEB + path}


add(
    "red-part",
    ("Find a red part", "Poišči rdeč predmet"),
    (
        "Select a red object against a neutral or green background. The output is a binary mask of sufficiently large red regions.",
        "Izberi rdeč predmet na nevtralnem ali zelenem ozadju. Rezultat je binarna maska dovolj velikih rdečih območij.",
    ),
    (
        "Extract the color channels, subtract green from red, then threshold. Opening removes isolated foreground pixels before component filtering measures the remaining connected regions.",
        "Razcepi barvne kanale, odštej zeleno od rdeče in nato uporabi prag. Odpiranje odstrani osamljene piksle, preden filtriranje povezanih območij izmeri preostale skupine.",
    ),
    (
        "Start with threshold 0.20, opening size 3 and minimum area 100 pixels. Raise the threshold to reject weak redness; raise the area limit to reject small fragments.",
        "Začni s pragom 0,20, velikostjo odpiranja 3 in najmanjšo površino 100 pikslov. Višji prag zavrne šibko rdečino; večja površina zavrne majhne delce.",
    ),
    (
        "The supplied scene contains one large red rectangle, a green rectangle and small red specks. The final mask should keep only the large red rectangle.",
        "Priložen prizor vsebuje velik rdeč pravokotnik, zelen pravokotnik in drobne rdeče pike. Končna maska ohrani samo velik rdeč pravokotnik.",
    ),
    (
        "This is color segmentation, not object recognition. White balance, colored illumination and highlights change the difference. The threshold uses normalized float channels.",
        "To je segmentacija barve, ne prepoznavanje vrste predmeta. Ravnovesje beline, barvna osvetlitev in odsevi spremenijo razliko. Prag uporablja normalizirane kanale.",
    ),
    "S = R − G\nM = 1[S > τ]\nM₁ = (M ⊖ K) ⊕ K\nO(p) = 1[p ∈ C ∧ |C| ≥ A_min]",
    [
        ("algebra", {"expression": "R-G"}),
        ("threshold", {"input": "S", "threshold": 0.2}),
        ("opening", {"input": "mask", "size": 3}),
        ("components", {"input": "opening", "minArea": 100}),
    ],
    [
        book("42–43", "55–56"),
        web(
            "Eroding and Dilating", "imgproc/erosion_dilatation/erosion_dilatation.html"
        ),
    ],
)

add(
    "bright-regions",
    ("Keep large bright regions", "Ohrani velika svetla območja"),
    (
        "Separate bright parts from a dark background and reject tiny regions by their actual pixel area.",
        "Loči svetle predmete od temnega ozadja in zavrni drobna območja glede na dejansko število pikslov.",
    ),
    (
        "Convert RGB to luminance, smooth small fluctuations, threshold, then filter connected regions. Area filtering comes after segmentation because it needs a binary foreground.",
        "Pretvori RGB v svetlost, zgladi manjša nihanja, uporabi prag in filtriraj povezana območja. Površino filtriramo po segmentaciji, ker potrebujemo binarno ospredje.",
    ),
    (
        "Use Gaussian size 3 and sigma 1, threshold 0.60 and minimum area 80. Compare the threshold output with the final mask while raising the area limit.",
        "Uporabi Gaussovo velikost 3 in sigmo 1, prag 0,60 in najmanjšo površino 80. Ob zviševanju površine primerjaj rezultat praga s končno masko.",
    ),
    (
        "Two large bright parts remain. A dark hole inside a part stays a hole; it does not contribute to the foreground area. Tiny bright dots disappear.",
        "Ostaneta dva velika svetla predmeta. Temna luknja znotraj predmeta ostane luknja in ne prispeva k površini ospredja. Drobne svetle pike izginejo.",
    ),
    (
        "Eight-connectivity joins pixels touching at a corner. Touching physical objects can therefore become one region. Pixel area is not a calibrated physical area.",
        "Osemsosednost poveže tudi piksle, ki se dotikajo v oglišču. Fizična predmeta, ki se dotikata, lahko postaneta eno območje. Površina v pikslih ni umerjena fizična površina.",
    ),
    "Y = 0.299R + 0.587G + 0.114B\nJ = Gσ ⋆ Y\nM = 1[J > τ]\nO(p) = 1[p ∈ C ∧ |C| ≥ A_min]",
    [
        ("luminance", {}),
        ("gaussian", {"input": "gray", "size": 3, "sigma": 1}),
        ("threshold", {"input": "smooth", "threshold": 0.6}),
        ("components", {"input": "mask", "minArea": 80}),
    ],
    [
        book("55–57", "68–70"),
        web(
            "Finding contours: segmentation precedes shape analysis",
            "imgproc/shapedescriptors/find_contours/find_contours.html",
        ),
    ],
)

add(
    "motion",
    ("Detect changes between frames", "Zaznaj spremembe med sličicami"),
    (
        "Find regions whose color changed between consecutive frames from a fixed camera.",
        "Poišči območja, katerih barva se je spremenila med zaporednima sličicama mirujoče kamere.",
    ),
    (
        "Keep signed channel differences, combine their magnitudes, threshold, remove isolated pixels, then reject small regions. A second frame is required before a difference exists.",
        "Ohrani predznačene razlike kanalov, združi njihove velikosti, uporabi prag, odstrani osamljene piksle in zavrni majhna območja. Za razliko potrebujemo drugo sličico.",
    ),
    (
        "Start with magnitude threshold 0.12, opening size 3 and minimum area 40. Step through two frames, then compare the signed red difference with the magnitude and mask.",
        "Začni s pragom velikosti 0,12, odpiranjem velikosti 3 in najmanjšo površino 40. Izvedi dve sličici in primerjaj predznačeno rdečo razliko z velikostjo in masko.",
    ),
    (
        "The first processed frame is empty. Later frames show changed portions around the moving synthetic part, including its previous location.",
        "Prva obdelana sličica je prazna. Naslednje pokažejo spremenjene dele ob premikajočem se sintetičnem predmetu, tudi na njegovi prejšnji lokaciji.",
    ),
    (
        "This detects change, not identity or a full object silhouette. Camera motion, flicker and shadows also produce responses. Restarting the algorithm resets the previous frame.",
        "To zaznava spremembo, ne identitete ali celotne silhuete predmeta. Premik kamere, utripanje in sence prav tako povzročijo odziv. Ponovni začetek algoritma ponastavi prejšnjo sličico.",
    ),
    "ΔC = C(t) − C(t−1)\nD = √(ΔR² + ΔG² + ΔB²)\nM = 1[D > τ]",
    [
        ("difference", {}),
        ("algebra", {"expression": "sqrt(dR**2+dG**2+dB**2)"}),
        ("threshold", {"input": "S", "threshold": 0.12}),
        ("opening", {"input": "mask", "size": 3}),
        ("components", {"input": "opening", "minArea": 40}),
    ],
    [
        {
            "title": "Original SimpleMotocam exercise: signed channel differencing",
            "url": "https://github.com/mech-id-x/SI_Eksperimenti_Strojnega_Vida/blob/33ac150c0cf2205313dd91ce3eab511e12c38fe7/Test_za_podatke_While_Loop",
        },
        book("42–43 (channel arithmetic background)", "55–56"),
    ],
    sample=False,
)

add(
    "lines",
    ("Detect straight edges", "Zaznaj ravne robove"),
    (
        "Turn a grayscale edge map into a mask of long straight line segments.",
        "Pretvori sivinsko karto robov v masko dolgih ravnih daljic.",
    ),
    (
        "Compute luminance and smooth it before Canny. Hough then groups edge pixels into candidate line segments. Thresholding a color region is a different task from finding its boundary.",
        "Izračunaj svetlost in jo zgladi pred Cannyjem. Hough nato združi robne piksle v kandidatne daljice. Pragovanje barvnega območja ima drugačen namen kot iskanje njegove meje.",
    ),
    (
        "Use Gaussian size 3, Canny low 40 and high 100, Hough votes 30, minimum length 60 and maximum gap 5. Canny thresholds are in the quantized 8-bit gradient domain.",
        "Uporabi Gaussovo velikost 3, Cannyjev spodnji prag 40 in zgornji 100, Houghove glasove 30, najmanjšo dolžino 60 in največjo vrzel 5. Cannyjeva pragova sta v kvantizirani 8-bitni domeni gradienta.",
    ),
    (
        "Long straight features are retained while short isolated marks are rejected. A thick bright stripe may produce two boundary lines.",
        "Dolge ravne značilnosti ostanejo, kratke osamljene oznake pa odpadejo. Debela svetla črta lahko povzroči dve robni daljici.",
    ),
    (
        "A line mask is not a fitted physical dimension. Perspective, calibration and uncertainty must be addressed before metrology. More votes do not guarantee a more accurate line.",
        "Maska daljic ni izmerjena fizična dimenzija. Pred meroslovjem je treba obravnavati perspektivo, kalibracijo in negotovost. Več glasov ne zagotavlja natančnejše daljice.",
    ),
    "J = Gσ ⋆ Y\nE = Canny(J, low, high)\nρ = x cos θ + y sin θ",
    [
        ("luminance", {}),
        ("gaussian", {"input": "gray", "size": 3, "sigma": 1}),
        ("canny", {"input": "smooth", "low": 40, "high": 100}),
        ("hough", {"input": "canny", "votes": 30, "minLength": 60, "maxGap": 5}),
    ],
    [
        web("Hough Line Transform", "imgproc/imgtrans/hough_lines/hough_lines.html"),
        trucco("68–69 (features and edges)", "43"),
        book("55 (smoothing before edges)", "68"),
    ],
)

add(
    "edges",
    ("Find edges after suppressing noise", "Poišči robove po odstranitvi šuma"),
    (
        "Compare impulsive noise with coherent object boundaries using median filtering and a Laplacian response.",
        "Z medianinim filtrom in Laplaceovim odzivom primerjaj impulzni šum s povezanimi mejami predmeta.",
    ),
    (
        "Convert to luminance, apply a small median filter, compute the signed Laplacian, take its absolute value, then threshold. Absolute value keeps both edge polarities.",
        "Pretvori v svetlost, uporabi majhen medianin filter, izračunaj predznačeni Laplaceov odziv, vzemi absolutno vrednost in uporabi prag. Absolutna vrednost ohrani obe polariteti roba.",
    ),
    (
        "Start with median size 3 and response threshold 0.15. Inspect the signed Laplacian before the absolute-value block. Increase the median size to compare lost fine detail.",
        "Začni z mediano velikosti 3 in pragom odziva 0,15. Pred blokom absolutne vrednosti preglej predznačeni Laplaceov odziv. Povečaj velikost mediane in primerjaj izgubo drobnih podrobnosti.",
    ),
    (
        "Sparse salt-and-pepper pixels mostly disappear, while the rectangle boundary remains. This is a detection adaptation, not a copy of the book’s artistic outlining effect.",
        "Redki črni in beli šumni piksli večinoma izginejo, rob pravokotnika pa ostane. To je prilagoditev za zaznavanje, ne kopija umetniškega učinka iz knjige.",
    ),
    (
        "The Laplacian amplifies residual noise. Filtering can erase thin objects. This exercise uses float32, a size-3 median and a size-1 Laplacian stencil, unlike the book’s color effect.",
        "Laplacian ojača preostali šum. Filtriranje lahko izbriše tanke predmete. Vaja uporablja float32, mediano velikosti 3 in Laplaceovo shemo velikosti 1, drugače kot barvni učinek v knjigi.",
    ),
    "J = median₃(Y)\nL = ∂²J/∂x² + ∂²J/∂y²\nM = 1[|L| > τ]",
    [
        ("luminance", {}),
        ("median", {"input": "gray", "size": 3}),
        ("laplacian", {"input": "median"}),
        ("algebra", {"expression": "abs(laplace)", "output": "strength"}),
        ("threshold", {"input": "strength", "threshold": 0.15}),
    ],
    [book("55–57", "68–70"), trucco("52–53, 68–69 (noise and edges)", "35, 43")],
)

add(
    "uneven-light",
    ("Segment under uneven illumination", "Segmentiraj pri neenakomerni osvetlitvi"),
    (
        "Extract dark marks on a slowly varying bright background using a local threshold.",
        "Izloči temne oznake na počasi spreminjajočem se svetlem ozadju z lokalnim pragom.",
    ),
    (
        "Convert to luminance, smooth, use adaptive Gaussian thresholding, invert the result, then remove small regions. Inversion makes the dark marks the foreground.",
        "Pretvori v svetlost, zgladi, uporabi prilagodljivi Gaussov prag, obrni rezultat in odstrani majhna območja. Z obračanjem postanejo temne oznake ospredje.",
    ),
    (
        "Start with adaptive window size 15, offset 5 and minimum area 50. The window must be odd and wider than the mark. The offset is in 8-bit intensity units.",
        "Začni z oknom prilagodljivega praga 15, odmikom 5 in najmanjšo površino 50. Okno mora biti liho in širše od oznake. Odmik je v 8-bitnih enotah svetlosti.",
    ),
    (
        "The two dark bars remain across the brightness gradient. Compare with a fixed threshold to see why the locally estimated background helps.",
        "Temni letvi ostaneta kljub gradientu svetlosti. Primerjaj s fiksnim pragom, da vidiš korist lokalno ocenjenega ozadja.",
    ),
    (
        "A window that is too small can detect only outlines or miss wide marks. Strong texture and sharp shadows can resemble defects. This is an illustrative inspection task, not a trained defect classifier.",
        "Premajhno okno lahko zazna samo obrise ali izpusti široke oznake. Močna tekstura in ostre sence lahko spominjajo na napake. To je učna kontrolna naloga, ne naučen klasifikator napak.",
    ),
    "T(x,y) = GaussianMean_window(J₈) − C\nM = 1[J₈ > T]\nD = 1 − M",
    [
        ("luminance", {}),
        ("gaussian", {"input": "gray", "size": 3, "sigma": 1}),
        ("adaptive", {"input": "smooth", "size": 15, "offset": 5}),
        ("invert", {"input": "adaptive"}),
        ("components", {"input": "inverted", "minArea": 50}),
    ],
    [
        {
            "title": "OpenCV 2.4 miscellaneous image transformations: adaptiveThreshold",
            "url": "https://docs.opencv.org/2.4.13.7/modules/imgproc/doc/miscellaneous_transformations.html#adaptivethreshold",
        }
    ],
)

ui = {
    "sequences": ("Detection sequences", "Zaporedja zaznavanja"),
    "goal": ("Detection goal", "Cilj zaznave"),
    "order": ("Why this order", "Zakaj ta vrstni red"),
    "tune": ("Parameters to try", "Parametri za preizkus"),
    "expected": ("Expected result", "Pričakovani rezultat"),
    "caution": ("Limits and failure cases", "Omejitve in napake"),
    "load": (
        "Build this algorithm in the application",
        "Sestavi ta algoritem v aplikaciji",
    ),
    "download": ("Download algorithm state", "Prenesi stanje algoritma"),
    "sample": ("Download the test scene", "Prenesi preizkusni prizor"),
    "sources": ("Sources and book pages", "Viri in strani v knjigah"),
    "code": ("Runnable Python pipeline", "Izvedljivo zaporedje Python"),
    "offline": (
        "Open the classroom inside SimpleMotocam to load this sequence. The state and test image can also be downloaded.",
        "Za nalaganje zaporedja odpri učilnico znotraj SimpleMotocam. Stanje in preizkusno sliko lahko tudi preneseš.",
    ),
    "intro": (
        "Each sequence targets OpenCV 2.4.13.7. Load it to inspect intermediate channels and change the mathematics. The examples are original teaching adaptations with source references.",
        "Vsako zaporedje uporablja OpenCV 2.4.13.7. Naloži ga, preglej vmesne kanale in spreminjaj matematiko. Primeri so avtorske učne prilagoditve z navedenimi viri.",
    ),
    "bookNote": (
        "Local books are in D:\\Dromation\\Computer Vision. Page references distinguish printed pages from PDF pages; the books are not redistributed with the application.",
        "Lokalne knjige so v D:\\Dromation\\Computer Vision. Sklici ločijo tiskane strani od strani PDF; knjige se ne razširjajo z aplikacijo.",
    ),
    "codeNote": (
        "This Python orchestrator calls the genuine OpenCV 2.4 worker through SimpleMotocam. The C/C++/Java selector applies to the individual foundation lessons.",
        "Ta orkestrator Python kliče pravi pogon OpenCV 2.4 prek SimpleMotocam. Izbirnik C/C++/Java velja za posamezne osnovne učne teme.",
    ),
    "confirm": (
        "Replace the current algorithm with this OpenCV 2.4 exercise and its test scene?",
        "Zamenjam trenutni algoritem s to vajo OpenCV 2.4 in njenim preizkusnim prizorom?",
    ),
    "legacyCode": (
        "OpenCV 2.4 custom Python: use NumPy for algebra and cv24.run(kind, plane, **parameters) for native operations. Importing cv2 refers to this limited bridge, never silently to OpenCV 4.",
        "Lastna koda Python za OpenCV 2.4: za algebro uporabi NumPy, za izvorne operacije pa cv24.run(kind, plane, **parameters). Uvoz cv2 pomeni ta omejeni most, nikoli tihega preklopa na OpenCV 4.",
    ),
    "primary": ("Primary engine: OpenCV 2.4", "Glavni pogon: OpenCV 2.4"),
}


def main():
    folder = GUIDE / "sequence-i18n"
    folder.mkdir(exist_ok=True)
    for lang, index in [("en", 0), ("sl", 1)]:
        strings = {f"ui.{key}": values[index] for key, values in ui.items()}
        for item in lessons:
            for key in ("title", "goal", "order", "tune", "expected", "caution"):
                strings[item["id"] + "." + key] = item[key][lang]
        (folder / (lang + ".json")).write_text(
            json.dumps(
                {"locale": lang, "status": "authored", "strings": strings},
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    data = {"schema": 1, "lessons": lessons}
    (ROOT / "src/simplemotocam/studio_sequences.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    examples = GUIDE / "examples"
    examples.mkdir(exist_ok=True)
    rng = np.random.default_rng(24)
    for id in ("red-part", "bright-regions", "lines", "edges", "uneven-light"):
        image = np.full((240, 320, 3), 40, np.uint8)
        if id == "red-part":
            image[60:175, 40:140] = (25, 30, 225)
            image[60:175, 190:280] = (25, 225, 30)
            for y, x in [(20, 20), (35, 160), (200, 240)]:
                image[y : y + 2, x : x + 2] = (20, 20, 255)
        elif id == "bright-regions":
            image[40:150, 30:110] = 220
            image[80:190, 190:280] = 235
            image[75:110, 50:85] = 40
            image[205:208, 150:153] = 255
        elif id == "lines":
            image[55:59, 30:290] = 235
            image[155:159, 40:280] = 235
            image[30:205, 235:239] = 235
            image[200:203, 35:43] = 235
        elif id == "edges":
            image[65:175, 80:245] = 210
            ys = rng.integers(0, 240, 350)
            xs = rng.integers(0, 320, 350)
            image[ys, xs] = rng.choice([0, 255], 350)[:, None]
        else:
            image[:] = np.linspace(115, 235, 320, dtype=np.uint8)[None, :, None]
            image[50:190, 70:78] = 25
            image[50:190, 235:243] = 25
        ok, encoded = cv2.imencode(".png", image)
        assert ok
        (examples / (id + ".png")).write_bytes(encoded.tobytes())
    print("Built six original OpenCV 2.4 sequences and five synthetic test scenes.")


if __name__ == "__main__":
    main()
