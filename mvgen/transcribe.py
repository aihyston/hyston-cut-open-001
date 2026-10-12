"""Step 1: character-level Chinese ASR with timestamps (sherpa-onnx Paraformer).

Uses short overlapping windows (6 s, hop 3 s, keep the central 3 s) because
long windows compress timestamps on fast-sung passages.
"""
import json
import subprocess
import soundfile as sf


def to_wav16(audio_path, wav_path):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", audio_path,
                    "-ac", "1", "-ar", "16000", wav_path], check=True)


def transcribe(wav_path, model_dir, out_json, win=6.0, hop=3.0, threads=2):
    import sherpa_onnx
    rec = sherpa_onnx.OfflineRecognizer.from_paraformer(
        paraformer=f"{model_dir}/model.int8.onnx",
        tokens=f"{model_dir}/tokens.txt",
        num_threads=threads)
    audio, sr = sf.read(wav_path, dtype="float32")
    total = len(audio) / sr
    margin = (win - hop) / 2
    out, st = [], -margin
    while st < total:
        s0 = max(st, 0.0)
        stream = rec.create_stream()
        stream.accept_waveform(sr, audio[int(s0 * sr):int((st + win) * sr)])
        rec.decode_stream(stream)
        for tok, t in zip(stream.result.tokens, stream.result.timestamps):
            T = s0 + t
            if st + margin <= T < st + margin + hop:
                out.append((round(T, 2), tok))
        st += hop
    with open(out_json, "w") as f:
        json.dump(out, f, ensure_ascii=False)
    return out
