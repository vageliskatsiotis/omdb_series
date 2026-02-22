
import os
import subprocess
import errno
import re
import platform
import json
import urllib.request
import urllib.error
import urllib.parse

if (platform.system() == "Windows"):
	import winapps

from mutagen import MutagenError
from mutagen.mp4 import MP4
from io import StringIO

# Main

def main():
	# Define home directory
	directory = os.path.dirname(os.path.realpath(__file__))
	try:
		# Get into directory
		os.chdir(directory)
		# Iterate on current directory
		CheckPosters(directory)

	# Handle Exceptions - Create file with not found movies
	except OSError as e:
		if e.errno != errno.EEXIST:
			raise

# Check for Posters

def CheckPosters(directory):
	# Loop through files
	for root, dirs, files in os.walk(directory):
		# Exclude searching on hidden files and folders
		files = [f for f in files if not f[0] == '.']
		dirs[:] = [d for d in dirs if not d[0] == '.']
		# Loop
		for file in files:
			#get year for filename
			year = file[-9:-5]
			# Get file's length
			file_length = len(file)
			# Get file's extension
			extension = file[file_length - 4:]
			# Metadata title
			meta_title = file[:-4]
			if (".mp4" in file or ".mkv" in file or ".avi" in file):
				try:
				# Get into directory
					os.chdir(root)
					# Check if image already exists in dir
					checkPoster = CheckPoster(root, meta_title)
					if not checkPoster:
						file = open(os.path.expanduser("~") + "/posters_not_found.txt", "a")
						# Append title at the end of file
						file.write(meta_title)
						# New line
						file.write("\n")
						# Close the file
						file.close()
						# Print message
						print("Poster not found for " + meta_title)
				except OSError as e:
					if e.errno != errno.EEXIST:
						raise
			

# Check if poster is already in directory is installed on Windows

def CheckPoster(dir, filename):
	if (os.path.exists(os.path.join(dir, filename + ".jpg"))):
		return True

if __name__ == "__main__":
	main()
