import os
import subprocess
import errno
import re
import platform
import time

if (platform.system() == "Windows"):
	import winapps
	
from mutagen import MutagenError
from mutagen.mp4 import MP4
from io import StringIO

# Check if MKVToolNix is installed on Windows
def CheckMKVToolNix():
	for app in winapps.search_installed('MKVToolNix'):
		if app:
			return True
		else:
			return False

# Current folder
folder = "."

# FFmpeg command template (medium preset)
ffmpeg_template = [
    "ffmpeg",
    "-i",
    "",  # input file placeholder
    "-map",
    "0",
    "-c:v",
    "libx265",
    "-crf",
    "27",
    "-preset",
    "medium",  # medium preset for faster encoding
    "-c:a",
    "copy",
    "-c:s",
    "copy",
    "",  # output file placeholder
]

# Iterate through all MKV files in current folder (sorted ascending)
for filename in sorted(os.listdir(folder), key=str.lower):
    if filename.lower().endswith(".mkv"):
        input_path = os.path.join(folder, filename)

        # Clean filename: remove year, resolution, x265, Silence
        base_name = re.sub(
            r"\s*\(\d{4}\)|\s*\(.*?p.*?x265.*?\)|\s*Silence",
            "",
            filename,
            flags=re.IGNORECASE,
        )
        base_name = re.sub(r"\s+-\s+$", "", base_name)  # remove trailing dash
        base_name = base_name.strip()
        output_name = os.path.join(folder, base_name)

        # Ensure .mkv extension
        if not output_name.lower().endswith(".mkv"):
            output_name += ".mkv"

        # Skip if output file already exists
        if os.path.exists(output_name):
            print(f"Skipping (already exists): {output_name}")
            continue

        # Print start message
        print(f"=== STARTING conversion for: {filename} ===")

        # Build ffmpeg command
        cmd = ffmpeg_template.copy()
        cmd[2] = input_path
        cmd[-1] = output_name

        # Run conversion
        start_time = time.time()
        subprocess.run(cmd)

        # Get file's length
        file_length = len(base_name)
        # Get file's title without extension
        meta_title = base_name[:file_length - 4]

        # Check OS first and MKVToolNix for Windows
        if (platform.system() == "Windows") and CheckMKVToolNix():
            mkvpropedit = r"C:\Program Files\MKVToolNix\mkvpropedit.exe"
            subprocess.run(
                [
                    mkvpropedit,
                    output_name,
                    "--edit",
                    "info",
                    "--set",
                    f"title={meta_title}",
                ]
            )
        elif platform.system() == "Linux":
            mkvpropedit = "/usr/bin/mkvpropedit"
            # Check if mkvpropedit exists in linux system
            if os.path.exists(mkvpropedit):
                # Call mkvpropedit using subprocess to change metadata title
                subprocess.run(
                    [
                        mkvpropedit,
                        output_name,
                        "--edit",
                        "info",
                        "--set",
                        f"title={meta_title}",
                    ],
                    capture_output=True,
                )
            else:
                # Open a file with access mode "a"
                file = open(
                    os.path.expanduser("~") + "/meta_titles_not_changed.txt", "a"
                )
                # Append title at the end of file
                file.write(meta_title)
                # New line
                file.write("\n")
                # Close the file
                file.close()
                # Print message
                print(
                    "mkvpropedit does not exist in current system. Metadata title for "
                    + output_name
                    + "will not be updated"
                )
        # Calculate elapsed time for the conversion
        elapsed = time.time() - start_time
        hrs = int(elapsed // 3600)
        mins = int((elapsed % 3600) // 60)
        secs = elapsed % 60
        if hrs:
            elapsed_str = f"{hrs}h {mins}m {secs:.2f}s"
        elif mins:
            elapsed_str = f"{mins}m {secs:.2f}s"
        else:
            elapsed_str = f"{secs:.2f}s"
        # Print end message
        print(f"=== FINISHED conversion for: {filename} in {elapsed_str} ===\n")
