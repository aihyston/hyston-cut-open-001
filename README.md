# HYSTON CUT / OPEN 001

**An AI-native, code-driven lyric music video workflow.**
一首歌 + 一份歌词 → 一条 1080p 逐字点亮的歌词 MV。全部由可阅读、可修改、可复现的代码完成。

这是 AI HYSTON 的第一个开源项目，源自 HYSTON 原创歌曲《雨水没有决定花期》（4:02）的歌词 MV 制作流程。

## 它做了什么

| 步骤 | 做法 | 代码 |
|---|---|---|
| 1. 音频理解 | 转 16 kHz 单声道，用 sherpa-onnx + Paraformer 中文模型做**逐字时间戳**识别（6 秒窗口、3 秒步进，避免快歌词时间被压缩） | `mvgen/transcribe.py` |
| 2. 歌词对齐 | 把已知歌词与识别结果做全局序列比对（Needleman–Wunsch），没识别到的字线性插值 | `mvgen/align.py` |
| 3. 动态字幕 | 生成 ASS 字幕，每个字按演唱时长做 `\kf` 卡拉OK扫光，片头片尾自动加标题卡 | `mvgen/subtitles.py` |
| 4. 程序化画面 | 逐帧生成雨丝、光斑、绽放的花、飘落花瓣；颜色、雨量、花开程度由关键帧驱动；亮度随音量轻微起伏 | `mvgen/render.py` |
| 5. 合成输出 | FFmpeg 放大到 1920×1080、烧录字幕、混入原音频，H.264 输出 | `run.py` |

> 说明：背景在 960×540 生成后放大到 1080p，字幕直接以 1080p 渲染，所以文字是清晰的。

## 快速开始

需要 Python 3.10+、FFmpeg（带 libass）、中文字体 Noto Serif CJK SC（Ubuntu: `apt install fonts-noto-cjk`）。

```bash
pip install -r requirements.txt
bash scripts/download_models.sh         # 下载中文识别模型（约 230 MB，不包含在仓库里）

python run.py \
  --audio your_song.mp3 \
  --lyrics your_lyrics.txt \
  --title "你的歌名" --artist "YOUR NAME" \
  --scenes examples/scenes.example.json \
  --out mv.mp4
```

- 歌词格式见 `examples/lyrics.example.txt`：一行一句，按实际演唱顺序，重复的副歌要重复写出。
- 不传 `--scenes` 会按歌曲时长自动生成一条「雨夜 → 花开 → 天亮」的默认情绪曲线。
- 2 核 CPU 上，4 分钟的歌大约 15–25 分钟出片。

## 修正个别歌词时间

自动对齐后，每句会打印 `匹配字数/总字数`。匹配少的句子可能偏差半拍：
打开 `work/lines.json` 手动改这句的 `start` 和 `chars`，然后：

```bash
python run.py --audio your_song.mp3 --lyrics your_lyrics.txt --lines work/lines.json --out mv.mp4
```

## 自定义画面

`examples/scenes.example.json` 是《雨水没有决定花期》实际使用的关键帧：
`t` 为秒，`top` / `bottom` 为天空上下两端颜色，`rain` / `bloom` / `petals` 取 0–1。
关键帧之间会平滑过渡，按你的歌曲段落改时间点即可。

## 已知局限

- 识别模型目前是**中文**；其他语言需要换模型并调整 `align.py` 的字符过滤。
- 对齐依赖识别质量：混音很满、和声多、说唱段落可能需要手动修正几句。
- 画面是程序化的抽象风格；实拍或 AI 视频素材的版本在后续计划中。

## 版权与授权边界

- **本仓库代码**：MIT License，© 2026 HYSTON PTY LTD。
- **不包含**：任何歌曲音频、歌词、成片视频。《雨水没有决定花期》的词曲与录音版权不随本项目开源。
- **第三方组件**（不随仓库分发，请自行遵守其许可）：
  - [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx)：Apache-2.0
  - Paraformer 中文模型（FunASR）：见模型压缩包内说明
  - Noto Serif CJK 字体：SIL Open Font License 1.1
  - FFmpeg / libass：LGPL/GPL（取决于你的构建）

用这个工具做 MV 时，请确保你对使用的音乐和歌词拥有相应权利。

---

*The model is replaceable. The workflow is open.* — AI HYSTON
