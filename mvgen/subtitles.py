"""Step 3: karaoke-style ASS subtitles (per-character \\kf sweep)."""
import json


def _ts(t):
    t = max(t, 0)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Lyric,{font} Medium,74,&H00FFFFFF,&H70E8E8F0,&H60080810,&H00000000,0,0,0,0,100,100,6,0,1,4,0,2,120,120,190,1
Style: Title,{font} Light,104,&H00FFFFFF,&H00FFFFFF,&H80101018,&H00000000,0,0,0,0,100,100,22,0,1,3,0,5,60,60,60,1
Style: Sub,{font} Light,30,&H30FFFFFF,&H30FFFFFF,&H80101018,&H00000000,0,0,0,0,100,100,26,0,1,2,0,5,60,60,60,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def make_ass(lines_json, out_ass, duration, title="", artist="", font="Noto Serif CJK SC"):
    L = json.load(open(lines_json))
    ev = []
    spaced = " ".join(artist.upper()) if artist else ""
    first = L[0]["start"] if L else duration
    if title and first > 4:
        end = first - 1.0
        ev.append(f"Dialogue: 0,{_ts(1.2)},{_ts(end)},Title,,0,0,0,,{{\\fad(1800,1500)\\blur5\\pos(960,500)}}{title}")
        if spaced:
            ev.append(f"Dialogue: 0,{_ts(2.6)},{_ts(end)},Sub,,0,0,0,,{{\\fad(1800,1500)\\blur3\\pos(960,620)}}{spaced}")
    for i, l in enumerate(L):
        st = l["start"] - 0.35
        nxt = L[i + 1]["start"] - 0.15 if i + 1 < len(L) else duration
        end = min(nxt, l["last"] + 2.6) if i + 1 < len(L) else min(l["last"] + 3.0, duration)
        parts = ["{\\k35}"]
        ch = l["chars"]
        for j, c in enumerate(l["text"]):
            nt = ch[j + 1] if j + 1 < len(ch) else min(ch[j] + 0.5, end)
            parts.append(f"{{\\kf{max(int(round((nt - ch[j]) * 100)), 8)}}}{c}")
        ev.append(f"Dialogue: 1,{_ts(st)},{_ts(end)},Lyric,,0,0,0,,{{\\fad(300,450)\\blur2.5}}" + "".join(parts))
    last = L[-1]["last"] + 2.5 if L else 0
    if title and duration - last > 4:
        ev.append(f"Dialogue: 0,{_ts(last)},{_ts(duration)},Title,,0,0,0,,{{\\fad(2000,1200)\\blur5\\pos(960,500)}}{title}")
        if spaced:
            ev.append(f"Dialogue: 0,{_ts(last + 0.8)},{_ts(duration)},Sub,,0,0,0,,{{\\fad(2000,1200)\\blur3\\pos(960,620)}}{spaced}")
    with open(out_ass, "w", encoding="utf-8") as f:
        f.write(HEADER.format(font=font) + "\n".join(ev) + "\n")
