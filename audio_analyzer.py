#!/usr/bin/env python3
import os
import subprocess
import json
import sys
import shutil
from pathlib import Path

# Enable ANSI escape sequences on Windows
os.system("")

def check_dependencies():
    has_ffmpeg = shutil.which("ffmpeg") is not None
    has_ffprobe = shutil.which("ffprobe") is not None
    
    if not has_ffmpeg or not has_ffprobe:
        print("\n\033[1;31m=== ERROR: FFmpeg or FFprobe Not Found ===\033[0m")
        print("This tool requires FFmpeg and FFprobe to read audio data and calculate loudness.")
        print("Your system cannot find them. They are either not installed or not added to your PATH.\n")
        
        print("\033[1;33mHow to Fix & Install (Windows):\033[0m")
        print("  1. Open Command Prompt or PowerShell as Administrator.")
        print("  2. Run the following command:")
        print("     \033[1mwinget install -e --id Gyan.FFmpeg\033[0m")
        print("  3. COMPLETELY CLOSE and RESTART this terminal window so the new PATH takes effect.")
        print("     (If using VS Code, close the entire application and reopen it).\n")
        
        print("\033[1;33mIf you already installed them manually:\033[0m")
        print("  Ensure the folder containing the .exe files (e.g., C:\\ffmpeg\\bin or your Winget")
        print("  package folder) is explicitly added to your Windows 'Path' Environment Variable.\n")
        sys.exit(1)

def run_ffprobe(file_path):
    cmd = [
        'ffprobe', '-v', 'error', 
        '-show_entries', 'stream=codec_name,sample_fmt,sample_rate,bit_rate:format=bit_rate',
        '-of', 'json', str(file_path.absolute())
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return json.loads(result.stdout)
    except Exception:
        return None

def run_ebur128(file_path):
    cmd = [
        'ffmpeg', '-nostats', '-i', str(file_path.absolute()),
        '-filter_complex', 'ebur128=peak=true',
        '-f', 'null', '-'
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        output = result.stderr
        
        integrated, true_peak = "N/A", "N/A"
        max_m, max_s = -999.0, -999.0
        
        lines = output.split('\n')
        in_summary = False
        
        for i, line in enumerate(lines):
            if "M:" in line and "S:" in line and "I:" in line:
                try:
                    parts = line.split()
                    for idx, p in enumerate(parts):
                        if p.startswith("M:"):
                            val_str = p.split(":")[1] if len(p.split(":")[1]) > 0 else parts[idx+1]
                            max_m = max(max_m, float(val_str))
                        elif p.startswith("S:"):
                            val_str = p.split(":")[1] if len(p.split(":")[1]) > 0 else parts[idx+1]
                            max_s = max(max_s, float(val_str))
                except (ValueError, IndexError):
                    pass
            
            if "Summary:" in line:
                in_summary = True
            elif in_summary:
                if "Integrated loudness:" in line:
                    integrated = lines[i+1].split("I:")[1].replace("LUFS", "").strip()
                elif "True peak:" in line:
                    true_peak = lines[i+1].split("Peak:")[1].replace("dBFS", "").strip()
                    
        return {
            'integrated': integrated,
            'true_peak': true_peak,
            'short_term_max': str(max_s) if max_s != -999.0 else "N/A",
            'momentary_max': str(max_m) if max_m != -999.0 else "N/A"
        }
    except Exception:
        return None

def analyze_directory(directory):
    target_dir = Path(directory).resolve()
    if not target_dir.is_dir():
        print(f"Error: The directory '{directory}' does not exist.")
        return

    extensions = {'.wav', '.mp3', '.flac', '.aiff', '.aif', '.m4a'}
    files = [f for f in target_dir.iterdir() if f.is_file() and f.suffix.lower() in extensions]
        
    if not files:
        print(f"No audio files found in '{directory}'")
        return

    print(f"Found {len(files)} audio file(s). Analyzing (this may take a moment)...\n")
    
    results = []
    
    for file_path in files:
        file_data = {
            "Filename": file_path.name[:37] + "..." if len(file_path.name) > 40 else file_path.name,
            "Codec": "N/A", "Depth/Fmt": "N/A", "Bitrate": "N/A", "SampleRate": "N/A",
            "Int(LUFS)": "N/A", "ST(LUFS)": "N/A", "Mom(LUFS)": "N/A", "TruePeak": "N/A"
        }
        
        probe = run_ffprobe(file_path)
        if probe:
            br = "unknown"
            if 'streams' in probe and len(probe['streams']) > 0:
                stream = probe['streams'][0]
                file_data["Codec"] = stream.get('codec_name', 'unknown').upper()
                file_data["Depth/Fmt"] = stream.get('sample_fmt', 'unknown')
                
                sr = stream.get('sample_rate', 'unknown')
                file_data["SampleRate"] = f"{int(sr)/1000:g} kHz" if sr != 'unknown' else "unknown"
                br = stream.get('bit_rate', 'unknown')
            
            if br == 'unknown' and 'format' in probe:
                br = probe['format'].get('bit_rate', 'unknown')
                
            file_data["Bitrate"] = f"{int(br)//1000} kbps" if br != 'unknown' else "unknown"

        loudness = run_ebur128(file_path)
        if loudness:
            file_data["Int(LUFS)"] = loudness['integrated']
            file_data["ST(LUFS)"] = loudness['short_term_max']
            file_data["Mom(LUFS)"] = loudness['momentary_max']
            file_data["TruePeak"] = loudness['true_peak']
            
        results.append(file_data)
        
    headers = ["Filename", "Codec", "Depth/Fmt", "Bitrate", "SampleRate", "Int(LUFS)", "ST(LUFS)", "Mom(LUFS)", "TruePeak"]
    color_keys = ["Int(LUFS)", "ST(LUFS)", "Mom(LUFS)", "TruePeak"]
    
    col_widths = {h: len(h) for h in headers}
    for row in results:
        for h in headers:
            col_widths[h] = max(col_widths[h], len(str(row[h])))
            
    val_ranges = {}
    for k in color_keys:
        vals = []
        for r in results:
            try: vals.append(float(r[k]))
            except ValueError: pass
        if vals:
            val_ranges[k] = (min(vals), max(vals))
        else:
            val_ranges[k] = (0, 0)
            
    def apply_color(text, val, min_v, max_v):
        RESET = "\033[0m"
        BOLD_RED = "\033[1;31m"
        BOLD_YELLOW = "\033[1;33m"
        BOLD_GREEN = "\033[1;32m"
        
        if max_v - min_v < 0.1:
            return f"{BOLD_GREEN}{text}{RESET}"
            
        norm = (val - min_v) / (max_v - min_v)
        
        if norm > 0.66:
            return f"{BOLD_RED}{text}{RESET}"
        elif norm > 0.33:
            return f"{BOLD_YELLOW}{text}{RESET}"
        else:
            return f"{BOLD_GREEN}{text}{RESET}"

    header_str = " | ".join([f"{h:<{col_widths[h]}}" for h in headers])
    separator = "-+-".join(["-" * col_widths[h] for h in headers])
    
    print(header_str)
    print(separator)
    
    for row in results:
        row_strs = []
        for h in headers:
            raw_str = str(row[h])
            padded_str = raw_str.ljust(col_widths[h])
            
            if h in color_keys and raw_str != "N/A":
                try:
                    val = float(raw_str)
                    min_v, max_v = val_ranges[h]
                    colorized = apply_color(padded_str, val, min_v, max_v)
                    row_strs.append(colorized)
                except ValueError:
                    row_strs.append(padded_str)
            else:
                row_strs.append(padded_str)
                
        print(" | ".join(row_strs))
        
    print("\nAnalysis complete!")

if __name__ == '__main__':
    # 1. First thing we do is verify the dependencies exist
    check_dependencies()
    
    # 2. If we pass the check, run the analysis
    directory = sys.argv[1] if len(sys.argv) > 1 else '.'
    analyze_directory(directory)