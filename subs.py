import os
import subprocess
import errno
import re
import platform
import enzyme
if (platform.system() == "Windows"):
	import winapps
from mutagen import MutagenError
from mutagen.mp4 import MP4
from io import StringIO
import glob
import shutil

# Main
def main():
	
	# Define home directory
	directory = os.path.dirname(os.path.realpath(__file__))
	# Get into directory
	os.chdir(directory)
	# Iterate on current directory
	RenameLoop(directory)

# Rename files
def RenameLoop(directory):
	# Loop through files
	for root, dirs, files in os.walk(directory):
		# Exclude searching on hidden files and folders
		files = [f for f in files if not f[0] == '.']
		dirs[:] = [d for d in dirs if not d[0] == '.']
		# Loop
		for file in files:
			if (".mp4" in file or ".mkv" in file):
				# Get video name
				meta_title = file[:-4]
				# Get file's length
				file_length = len(file)
				# Get file's extension
				extension = file[file_length - 4:]
				# Get file's name
				original_filename = os.path.join(root, file)
				# Get file directory
				fpath = os.path.dirname(os.path.realpath(original_filename))
				# Set Subs folder path
				subspath = os.path.join(fpath, "Subs")
				try:
					if (os.path.isdir(subspath)):
						os.chdir(subspath)
						subfiles = []
						# Get srt files in array
						for file in glob.glob("*.srt"):
							subfiles.append(file)
						index = 0
						# Loop for multiple English srt files (if any)
						while index < len(subfiles):
							if ("_English" in str(subfiles[index])):
								if (index == 0):
									orig_subpath = os.path.realpath(subfiles[index])
									new_meta_title = meta_title + ".srt"
									new_subpath = os.path.realpath(new_meta_title)
									os.rename(orig_subpath, new_subpath)
									index += 1
								else:
									orig_subpath = os.path.realpath(subfiles[index])
									new_meta_title = meta_title + "_" + str(index + 1) + ".srt"
									new_subpath = os.path.realpath(new_meta_title)
									os.rename(orig_subpath, new_subpath)
									index += 1
						# Move srt files to main directory
						subs_to_move = os.listdir(subspath)
						for f in subs_to_move:
							shutil.move(os.path.join(subspath, f), os.path.join(fpath, f))
						os.chdir(fpath)
						# Remove Subs folder
						shutil.rmtree(subspath)
						# Remove any txt files
						for txtfile in glob.glob("*.txt"):
							os.remove(txtfile)
						# Remove any exe files
						for exefile in glob.glob("*.exe"):
							os.remove(exefile)
				except OSError as e:
					if e.errno != errno.EEXIST:
						raise
						
if __name__ == "__main__":
	main()