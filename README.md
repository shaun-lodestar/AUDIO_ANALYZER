# 🎵 CLI Audio Batch Analyzer

A lightweight, dependency-free Python CLI tool that scans a directory of audio files (WAV, MP3, FLAC, AIFF, M4A) and generates a beautifully formatted, color-coded table of their technical specifications and EBU R128 loudness metrics.

## ✨ Features
- **File Specs:** Reads Codec, Bit depth, Bitrate, and Sample Rate.
- **Loudness Metrics:** Calculates Integrated LUFS, Short-Term max LUFS, Momentary max LUFS, and True Peak (dBTP).
- **Color-Coded Output:** Automatically scales and color-codes LUFS and True Peak values (Red for loudest, Yellow for average, Green for quietest) relative to the other tracks in the folder.
- **Smart Formatting:** Auto-aligns columns and neatly truncates ultra-long filenames to keep the table clean.

## ⚙️ Installation

1. **Install Python 3.6+** 
2. **Install FFmpeg & FFprobe (Required)**
   This script relies on `ffmpeg` and `ffprobe` being installed and added to your system's PATH.
   - **Windows:** Open an Admin terminal and run: `winget install -e --id Gyan.FFmpeg` (Restart terminal after).
   - **macOS:** `brew install ffmpeg`
   - **Linux:** `sudo apt install ffmpeg`
3. **Download the script:**
   Clone this repository or download `audio_analyzer.py`.

## 🚀 Usage

Run the script from your terminal. If you don't provide a path, it will analyze the current directory.

```bash
# Analyze the current folder
python audio_analyzer.py

# Analyze a specific folder
python audio_analyzer.py /path/to/your/music/folder
```

## ⚠️ Disclaimer

This software is provided "as is", without warranty of any kind, express or implied. The developer assumes no responsibility for any errors, loss of data, or system issues that may arise from its use. This tool interfaces with the FFmpeg executable; please ensure your FFmpeg installation is from a trusted source.