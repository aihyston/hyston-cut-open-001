#!/usr/bin/env python3
"""HYSTON CUT / OPEN 001 — one command from song + lyrics to lyric MV.

  python run.py --audio song.mp3 --lyrics lyrics.txt --title "歌名" --artist "ARTIST" --out mv.mp4
"""
import argparse, json, os, subprocess, sys
import soundfile as sf
from mvgen import transcribe, align, subtitles, render


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--audio", required=True)
    ap.add_argument("--lyrics", required=True, help="UTF-8 text, one sung line per row")
    ap.add_argument("--out", default="mv.mp4")
    ap.add_argument("--title", default="")
    ap.add_argument("--artist", default="")
    ap.add_argument("--scenes", help="JSON keyframes (see examples/scenes.example.json)")
    ap.add_argument("--model-dir", default="models/sherpa-onnx-paraformer-zh-2023-09-14")
    ap.add_argument("--work", default="work", help="folder for intermediate files")
    ap.add_argument("--font", default="Noto Serif CJK SC")
    ap.add_argument("--crf", type=int, default=21)
    ap.add_argument("--skip-asr", action="store_true", help="reuse work/asr.json")
    ap.add_argument("--lines", help="use an existing / hand-corrected lines.json instead of aligning")
    a = ap.parse_args()

    os.makedirs(a.work, exist_ok=True)
    wav = os.path.join(a.work, "audio16k.wav")
    asr_json = os.path.join(a.work, "asr.json")
    lines_json = a.lines or os.path.join(a.work, "lines.json")
    ass = os.path.join(a.work, "lyrics.ass")

    print("[1/4] audio -> 16 kHz mono"); transcribe.to_wav16(a.audio, wav)
    dur = sf.info(wav).duration
    if not a.lines:
        if not a.skip_asr:
            print("[2/4] ASR with character timestamps"); transcribe.transcribe(wav, a.model_dir, asr_json)
        print("[2/4] aligning lyrics")
        for l in align.align(a.lyrics, asr_json, lines_json):
            print(f'  {l["start"]:7.2f}  {l["matched"]:>2}/{len(l["text"]):<2} {l["text"]}')
        print(f"  -> {lines_json}  (edit 'start'/'chars' by hand if a line is off, then rerun with --lines)")
    print("[3/4] subtitles"); subtitles.make_ass(lines_json, ass, dur, a.title, a.artist, a.font)

    keyframes = json.load(open(a.scenes))["keyframes"] if a.scenes else None
    print(f"[4/4] rendering {dur:.1f}s ({int(dur * render.FPS)} frames) + encoding")
    ass_esc = ass.replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
    ff = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{render.W}x{render.H}", "-r", str(render.FPS), "-i", "-",
        "-i", a.audio,
        "-vf", f"scale=1920:1080:flags=lanczos,ass='{ass_esc}'",
        "-c:v", "libx264", "-preset", "medium", "-crf", str(a.crf), "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", a.out],
        stdin=subprocess.PIPE)
    render.render(wav, ff.stdin, dur, keyframes)
    ff.stdin.close()
    sys.exit(ff.wait())


if __name__ == "__main__":
    main()
