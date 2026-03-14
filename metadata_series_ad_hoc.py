import os
from pickle import FALSE
import subprocess
import errno
import re
import platform

if (platform.system() == "Windows"):
	import winapps
	
from mutagen import MutagenError
from mutagen.mp4 import MP4
from io import StringIO

# Main
def main():

	# Ask if batch process
	batch_mode_input = input("Is this a batch process? (yes/no): ").lower()

	# Define home directory
	directory = os.path.dirname(os.path.realpath(__file__))

	if batch_mode_input in ('yes', 'y'):
		# Batch mode: process all files in directory
		year = input("Input Year: ")
		try:
			os.chdir(directory)
			RenameLoop(None, None, None, None, year, directory, True)
		except OSError as e:
			if e.errno != errno.EEXIST:
				raise
	else:
		# Single file mode: current behavior
		title = input("Insert Title: ")
		year = input("Input Year: ")
		# Get season and episode no from title
		series_match = re.search(r"[^ -]*", title);
		series = series_match.group(0)
		search_str = re.search(r"(?:s|S|season|Season^)\d{2}(?:e|E|episode|Episode^)\d{2}", title)
		if search_str:
			episode_match = re.search(r"(.+?:e|E|episode|Episode^)\d{2}", search_str.group(0))
			season_match = re.search(r"(.+?:s|S|season|Season^)\d{2}", search_str.group(0))
			if season_match:
				season = season_match.group(0)[len(season_match.group(0)) - 2 :]
				episode_no = episode_match.group(0)[len(episode_match.group(0)) - 2 :]
				try:
					# Get into directory
					os.chdir(directory)
					# Iterate on current directory
					RenameLoop(series, title, season, episode_no, year, directory, False)

				# Handle Exceptions - Create file with not found episodes
				except OSError as e:
					if e.errno != errno.EEXIST:
						raise
					else:
						# Open a file with access mode "a"
						file = open(os.path.expanduser("~") + "/not_found.txt", "a")
						# Append title at the end of file
						file.write(title)
						# New line
						file.write("\n")
						# Close the file
						file.close()

def CheckMKVToolNix():
	for app in winapps.search_installed('MKVToolNix'):
		if app:
			return True
		else:
			return False

# Rename files (handles both single-file and batch modes)
def RenameLoop(series, new_title, season, episode_no, year, directory, is_batch_mode):
	# Batch mode: series, new_title, season, episode_no are all None
	# is_batch_mode = (series is None and new_title is None and season is None and episode_no is None)

	# Loop through files
	for root, dirs, files in os.walk(directory):
		for file in files:
			if is_batch_mode:
				# Batch mode: process all .mkv and .mp4 files
				if not (file.lower().endswith(".mkv") or file.lower().endswith(".mp4")):
					continue

				# Extract and clean filename for metadata
				name_no_ext = os.path.splitext(file)[0]
				meta_title = name_no_ext
				file_path = os.path.join(root, file)
				extension = os.path.splitext(file)[1].lower()
			else:
				# Single file mode: match specific series, season, episode
				if series not in file:
					continue
				if season not in file:
					continue

				# Adapt to API's response for episode titles from 1-9 and add 0 in front
				if len(episode_no) == 1:
					new_episode_no = "0" + str(episode_no)
				else:
					new_episode_no = episode_no
				# Change season string for single digit No input
				if len(season) == 1:
					season = "0" + str(season)
				# Search parameters in filename eg S01E01
				search_str = re.search(r"(?:\bseason\b|\bSeason\b|s|S)" + season + r"(?:\s|\-|\.)?(?:\bepisode\b|\bEpisode\b|e|E)" + re.escape(new_episode_no), file)
				if not search_str:
					continue

				# Get file's extension
				file_length = len(file)
				extension = file[file_length - 4 :]

				# Prepare rename string
				rename_str = new_title + extension

				# Get file's name
				original_filename = os.path.join(root, file)
				# Get replacement filename
				file_path = os.path.join(root, rename_str)

				# Rename file
				os.rename(original_filename, file_path)

				# Metadata title
				meta_title = new_title

			# Apply metadata based on file type
			if extension.lower() == ".mp4":
				try:
					# New mp4 instance
					video = MP4(file_path)
					# Add title to instance
					video["\xa9nam"] = meta_title
					# Add comment to instance
					video["\xa9cmt"] = meta_title
					# Add year to instance
					video["\xa9day"] = year
					# Save instance metadata to file
					video.save()
					if is_batch_mode:
						print(f"Updated metadata for: {file}")
					else:
						print("Found episode No " + new_title + extension)
				except MutagenError as m_error:
					print("Metadata title for " + meta_title + " failed with error: " + str(m_error))
			elif extension.lower() == ".mkv":
				try:
					# Check OS first and MKVToolNix for Windows
					if (platform.system() == "Windows") and CheckMKVToolNix():
						mkvpropedit = r"C:\Program Files\MKVToolNix\mkvpropedit.exe"
						subprocess.run([mkvpropedit, file_path, '--edit', 'info', '--set', f'title={meta_title}'], check=True)
					elif platform.system() == "Linux":
						mkvpropedit = "/usr/bin/mkvpropedit"
						# Check if mkvpropedit exists in linux system
						if os.path.exists(mkvpropedit):
							# Call mkvpropedit using subprocess to change metadata title
							subprocess.run([mkvpropedit, file_path, '--edit', 'info', '--set', f'title={meta_title}'], capture_output=True, check=True)
						else:
							# Open a file with access mode "a"
							file_handle = open(os.path.expanduser("~") + "/meta_titles_not_changed.txt", "a")
							# Append title at the end of file
							file_handle.write(meta_title)
							# New line
							file_handle.write("\n")
							# Close the file
							file_handle.close()
							# Print message
							print("mkvpropedit does not exist in current system. Metadata title for " + file_path + " will not be updated")
					if is_batch_mode:
						print(f"Updated metadata for: {file}")
					else:
						print("Found episode No " + new_title + extension)
				except Exception as e:
					print("Metadata title for " + meta_title + " failed with error: " + str(e))
if __name__ == "__main__":
	while True:
		main()
		again = input('Restart? ')
		if again.lower() not in ('yes', 'y'):
			break