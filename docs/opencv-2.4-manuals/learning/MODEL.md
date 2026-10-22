# A: model SimpleMotocam / SimpleMotocam model

## Slovenščina

Za normalizirane vrednosti RGB v [0,1] definiramo:

    h = min(R, G, B, 1-R, 1-G, 1-B)
    A = max(0, min(1, h/m)),  0 < m <= 0.5
    Q = min(A_trenutni, A_prejsnji) * velikost_spremembe_RGB

Model meri odmik od meja razpona v najbolj omejenem kanalu. Ne meri šuma,
ostrine, prepoznanega predmeta ali verjetnosti pravilnosti. A je ločen od
prosojnosti. Prag m je nastavljiv in model je mogoče zamenjati.

Izvor v projektu: `src/simplemotocam/channels.py`, funkcija `exposure_confidence`.
Uteževanje obeh slik: `src/simplemotocam/algebra.py`, `confident_motion`.

## English

For normalised RGB values in [0,1], define:

    h = min(R, G, B, 1-R, 1-G, 1-B)
    A = max(0, min(1, h/m)),  0 < m <= 0.5
    Q = min(A_current, A_previous) * RGB_change_magnitude

This model measures distance from range limits in the most constrained channel.
It does not measure noise, sharpness, object identity or probability of correctness.
A is separate from opacity. The margin m is configurable and the model replaceable.

Project source: `src/simplemotocam/channels.py`, function `exposure_confidence`.
Pairwise confidence weighting: `src/simplemotocam/algebra.py`, `confident_motion`.
