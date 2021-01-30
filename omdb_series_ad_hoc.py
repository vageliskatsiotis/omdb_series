import os
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
	
	# Input title
	title = input("Insert Title: ")
	# Input year
	year = input("Input Year: ")
	# Input season
	season = input("Insert Season: ")
	# Input episode_no
	episode_no = input("Input Episode No: ")
	# Define home directory
	directory = os.path.dirname(os.path.realpath(__file__))
	try:
		# Get into directory
		os.chdir(directory)
		# Iterate on current directory
		RenameLoop(title, season, episode_no, year, directory)

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

# Check if MKVToolNix is installed on Windows
def CheckMKVToolNix():
	for app in winapps.search_installed('MKVToolNix'):
		if app:
			return True
		else:
			return False

# Rename files
def RenameLoop(new_title, season, episode_no, year, directory):
	# Loop through files
	for root, dirs, files in os.walk(directory):
		for file in files:
			if season in file:
				# Adapt to API's response for episode titles from 1-9 and add 0 in front
				if len(episode_no) == 1:
					new_episode_no = "0" + str(episode_no)
				else:
					new_episode_no = episode_no
				# Change season string for single digit No input
				if len(season) == 1:
					season = "0" + str(season)
				# Search parameters in filename eg S01E01
				search_str = re.search(r"(?:s|S|season|Season^)" + season + r"(?:e|E|episode|Episode^)" + re.escape(new_episode_no), file)
				if(search_str):
					# Get file"s length
					file_length = len(file)
					# Get file"s extension
					extension = file[file_length - 4 :]
					# Prepare rename string
					rename_str = new_title + extension
					# Get file"s name
					original_filename = os.path.join(root, file)
					# Get replacemet filename
					new_filename = os.path.join(root, rename_str)
					# Rename file
					os.rename(original_filename, new_filename)
					# Metadata title
					meta_title = new_title
					# Add metadata title and year for mp4 files
					if extension == ".mp4":
						try:
							# New mp4 instance
							video = MP4(new_filename)
							# Add title to instance
							video["\xa9nam"] = new_title
							# Add year to instance
							video["\xa9day"] = year
							# Save instance metadata to file
							video.save()
						except MutagenError as m_error:
							print("Metadata title for " + new_title + " failed with error: " + m_error)
					# Add metadata title for mkv files
					elif extension == ".mkv":
						try:
							# Check OS first and MKVToolNix for Windows
							if ((platform.system() == "Windows") and CheckMKVToolNix()):
								mkvpropedit = r"C:\Program Files\MKVToolNix\mkvpropedit.exe"
								subprocess.run([mkvpropedit, new_filename, '--edit', 'info', '--set', f'title={meta_title}'])
							elif platform.system() == "Linux":
								mkvpropedit = "/usr/bin/mkvpropedit"
								# Check if mkvpropedit exists in linux system
								if os.path.exists(mkvpropedit):
									# Call mkvpropedit using subprocess to change metadata title
									subprocess.run([mkvpropedit, new_filename, '--edit', 'info', '--set', f'title={meta_title}'], capture_output = True)
								else:
									# Open a file with access mode "a"
									file = open(os.path.expanduser("~") + "/meta_titles_not_changed.txt", "a")
									# Append title at the end of file
									file.write(new_title)
									# New line
									file.write("\n")
									# Close the file
									file.close()
									# Print message
									print("mkvpropedit does not exist in current system. Metadata title for " + new_filename + "will not be updated")
						except OSError as e:
							if e.errno != errno.EEXIST:
								raise
					# Print successfull message
					print("Found episode No " + new_title + extension)
						
if __name__ == "__main__":
  main()