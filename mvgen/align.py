"""Step 2: align known lyrics to ASR characters (global Needleman–Wunsch).

Unmatched characters are linearly interpolated, so recognition errors on a
few characters do not break the line timing.
"""
import json
import numpy as np


def is_cjk(c):
    return "一" <= c <= "鿿"


def load_lyrics(path):
    with open(path, encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip() and not l.startswith("#")]


def align(lyrics_path, asr_json, out_json, gap=-0.6, mismatch=-0.5):
    lines = load_lyrics(lyrics_path)
    lc = [(c, i) for i, l in enumerate(lines) for c in l]
    asr = [(t, c) for t, c in json.load(open(asr_json)) if is_cjk(c)]
    n, m = len(lc), len(asr)
    D = np.zeros((n + 1, m + 1))
    B = np.zeros((n + 1, m + 1), dtype=np.int8)
    D[:, 0] = np.arange(n + 1) * gap
    D[0, :] = np.arange(m + 1) * gap
    for i in range(1, n + 1):
        ci = lc[i - 1][0]
        for j in range(1, m + 1):
            diag = D[i - 1, j - 1] + (1.0 if ci == asr[j - 1][1] else mismatch)
            up, left = D[i - 1, j] + gap, D[i, j - 1] + gap
            if diag >= up and diag >= left:
                D[i, j], B[i, j] = diag, 0
            elif up >= left:
                D[i, j], B[i, j] = up, 1
            else:
                D[i, j], B[i, j] = left, 2
    i, j, tm = n, m, [None] * n
    while i > 0 and j > 0:
        k = B[i, j]
        if k == 0:
            if lc[i - 1][0] == asr[j - 1][1]:
                tm[i - 1] = asr[j - 1][0]
            i, j = i - 1, j - 1
        elif k == 1:
            i -= 1
        else:
            j -= 1
    idx = [k for k in range(n) if tm[k] is not None]
    if not idx:
        raise SystemExit("No lyric characters matched the audio — check language / lyrics file.")
    t = np.interp(np.arange(n), idx, [tm[k] for k in idx])
    for k in range(1, n):
        t[k] = max(t[k], t[k - 1])
    result = []
    for li, text in enumerate(lines):
        ks = [k for k in range(n) if lc[k][1] == li]
        result.append({"text": text, "start": float(t[ks[0]]), "last": float(t[ks[-1]]),
                       "chars": [float(t[k]) for k in ks],
                       "matched": sum(tm[k] is not None for k in ks)})
    with open(out_json, "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    return result
