# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
import os
import subprocess
import re
import platform
import time

if platform.system() == "Windows":
    import winapps

# Check if MKVToolNix is installed on Windows
def check_mkv_tool_nix():
    """Return True if MKVToolNix is installed on Windows."""
    if platform.system() != "Windows":
        return False
    for app in winapps.search_installed("MKVToolNix"):
        if app:
            return True
    return False


# Current FOLDER
FOLDER = "."

def intel_qsv_available():
    try:
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True
        )
        return "hevc_qsv" in result.stdout
    except Exception:
        return False


# Decide encoder
if intel_qsv_available():
    print("Intel Quick Sync detected → Using hevc_qsv")
    ffmpeg_template = [
        "ffmpeg",
        "-i",
        "",
        "-map",
        "0",
        "-c:v",
        "hevc_qsv",
        "-global_quality",
        "27",
        "-preset",
        "medium",
        "-c:a",
        "copy",
        "-c:s",
        "copy",
        "",
    ]
else:
    print("Intel Quick Sync not found → Using CPU libx265")
    ffmpeg_template = [
        "ffmpeg",
        "-i",
        "",
        "-map",
        "0",
        "-c:v",
        "libx265",
        "-crf",
        "27",
        "-preset",
        "medium",
        "-c:a",
        "copy",
        "-c:s",
        "copy",
        "",
    ]

# Iterate through all MKV files in current FOLDER (sorted ascending)
for filename in sorted(os.listdir(FOLDER), key=str.lower):
    if filename.lower().endswith(".mkv"):
        input_path = os.path.join(FOLDER, filename)

        # Clean filename and generate a friendly output name.
        # Examples handled:
        #  - The.Diplomat.S02E01.When a Stranger Calls.1080p.WEB.H264-NHTFS
        # -> The Diplomat - S02E01 - When a Stranger Calls
        name_no_ext = os.path.splitext(filename)[0]

        # Normalize separators (dots/underscores -> spaces) and trim
        normalized = re.sub(r"[._]+", " ", name_no_ext).strip()

        # Remove trailing release group like "-NHTFS" or tags separated by a dash
        normalized = re.sub(r"\s*-\s*[^\s]+$", "", normalized).strip()

        # Common quality/release tokens that mark the end of the human title
        quality_tokens = {
            "1080p",
            "720p",
            "2160p",
            "480p",
            "web",
            "webrip",
            "web-dl",
            "hdrip",
            "bluray",
            "brrip",
            "h264",
            "h.264",
            "x264",
            "x265",
            "h265",
            "hevc",
            "aac",
            "dts",
            "dvdrip",
            "proper",
            "repack",
            "limited",
        }

        # Look for season/episode patterns (S02E01 or 2x01)
        se_match = re.search(r"(?i)\bS(\d{1,2})E(\d{1,2})\b", normalized)
        if not se_match:
            se_match = re.search(r"\b(\d{1,2})x(\d{2})\b", normalized)

        show = None
        episode_code = None
        episode_title = ""

        if se_match:
            # Standardize episode code to S##E##
            g1, g2 = se_match.group(1), se_match.group(2)
            episode_code = f"S{int(g1):02d}E{int(g2):02d}"

            # Show name is everything before the match
            show = normalized[: se_match.start()].strip()
            # Remove any year tokens like (1993) or standalone 1993 from the show
            show = re.sub(r"\(?\b(?:19|20)\d{2}\b\)?", "", show).strip()
            # Remove any trailing separators (e.g. a leftover hyphen from an already-clean filename)
            show = re.sub(r"[-\s]+$", "", show).strip()

            # Everything after the match up to the first quality token is the episode title
            after = normalized[se_match.end() :].strip()
            # Remove any leading separators (e.g. a leftover hyphen) so title doesn't start with '-'
            after = re.sub(r"^[-\s]+", "", after).strip()
            if after:
                after_tokens = after.split()
                good_tokens = []
                for t in after_tokens:
                    low = t.lower()
                    # stop if token looks like a resolution or quality or is a single-bracketed tag
                    if (
                        re.match(r"^\d{3,4}p$", low)
                        or low in quality_tokens
                        or re.match(r"^\[.*\]$", t)
                        or re.match(r"^\(.*\)$", t)
                    ):
                        break
                    good_tokens.append(t)
                episode_title = " ".join(good_tokens).strip()
                # Remove any year tokens like (1993) or standalone 1993 from the episode title
                episode_title = re.sub(r"\(?\b(?:19|20)\d{2}\b\)?", "", episode_title).strip()

        # Fallback: no season/episode found -> try to strip common tags and use cleaned name
        if not show:
            # Remove common year tokens, quality tokens and codec tags
            cleaned = re.sub(r"\(?\b(?:19|20)\d{2}\b\)?", "", normalized)
            cleaned = re.sub(
                r"\b(?:%s)\b" % "|".join(map(re.escape, quality_tokens)),
                "",
                cleaned,
                flags=re.IGNORECASE,
            )
            # collapse spaces
            cleaned = re.sub(r"\s+", " ", cleaned).strip()
            base_name = cleaned
        else:
            # Clean up spacing in show and episode title
            show = re.sub(r"\s+", " ", show).strip()
            episode_title = re.sub(r"\s+", " ", episode_title).strip()
            if episode_title:
                base_name = f"{show} - {episode_code} - {episode_title}"
            else:
                base_name = f"{show} - {episode_code}"

        # Final cleanup
        base_name = base_name.strip()
        output_name = os.path.join(FOLDER, base_name)

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
        subprocess.run(cmd, check=True)

        # Meta title: use the cleaned base_name without any file extension
        meta_title = os.path.splitext(base_name)[0]

        # Check OS first and MKVToolNix for Windows
        if (platform.system() == "Windows") and check_mkv_tool_nix():
            MKVPROPEDIT = r"C:\Program Files\MKVToolNix\mkvpropedit.exe"
            subprocess.run(
                [
                    MKVPROPEDIT,
                    output_name,
                    "--edit",
                    "info",
                    "--set",
                    f"title={meta_title}",
                ],
                check=True,
            )
        elif platform.system() == "Linux":
            MKVPROPEDIT = "/usr/bin/mkvpropedit"
            # Check if mkvpropedit exists in linux system
            if os.path.exists(MKVPROPEDIT):
                # Call mkvpropedit using subprocess to change metadata title
                subprocess.run(
                    [
                        MKVPROPEDIT,
                        output_name,
                        "--edit",
                        "info",
                        "--set",
                        f"title={meta_title}",
                    ],
                    check=True,
                    capture_output=True,
                )
            else:
                # Open a file with access mode "a"
                file = open(
                    os.path.expanduser("~") + "/meta_titles_not_changed.txt",
                    "a",
                    encoding="utf-8",
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
