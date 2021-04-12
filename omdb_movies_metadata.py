import os
import subprocess
import errno
import re
import platform
import json
import urllib.request
import urllib.error
import urllib.parse
import urllib.request
import urllib.parse
import urllib.error

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
		RenameLoop(directory)

	# Handle Exceptions - Create file with not found movies
	except OSError as e:
		if e.errno != errno.EEXIST:
			raise
		else:
			# Open a file with access mode "a"
			file = open(os.path.expanduser("~") + "/not_found.txt", "a")
			# Append title at the end of file
			file.write()
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

# Api Call
def ApiCall(title):

	url = ""
	data = ""

	# Define apikey
	apikey = ""
	# Escape characters on title
	query = urllib.parse.quote(title)
	# Insert season in query if exists
	if title != "":
		url = "https://www.omdbapi.com/?t=" + query + "&" + "apikey=" + apikey
	# JSON to string
	data = json.load(urllib.request.urlopen(url))
	# Return data
	return data

# Rename files
def RenameLoop(directory):
	query = ""
	# Loop through files
	for root, dirs, files in os.walk(directory):
		# Exclude searching on hidden files and folders
		files = [f for f in files if not f[0] == '.']
		dirs[:] = [d for d in dirs if not d[0] == '.']
		# Loop
		for file in files:
			if (".mp4" in file or ".mkv" in file):
				# Split title if is more than one words
				title_array = file.split()
				if len(title_array) > 1:
					i = 0
					sb = StringBuilder()
					# Build query string using split words
					while i < len(title_array):
						sb.Append(title_array[i] + "+")
						i += 1
					# Assign to query minus (the last plus + year + extension)
					query = str(sb)[:-12]
				else:
					query = file[:-12]
				# Make API call
				data = ApiCall(query)
				if(data["Response"] == "True"):
					# Get file's length
					file_length = len(file)
					# Get file's extension
					extension = file[file_length - 4 :]
					# Get file's name
					original_filename = os.path.join(root, file)
					# Get replacemet filename
					new_filename = os.path.join(root, file)
					# Rename file
					os.rename(original_filename, new_filename)
					# Metadata title
					meta_title = file[:-4]
					# Add metadata title and year and remove comments for mp4 files
					if extension == ".mp4":
						try:
							# New mp4 instance
							video = MP4(new_filename)
							# Add title to instance
							video["\xa9nam"] = str(file)
							# Add year to instance
							video["\xa9day"] = str(data["Year"])
							# Empty comments if any
							video["\251cmt"] = ""
							# Save instance metadata to file
							video.save()
						except MutagenError as m_error:
							print("Metadata title for " + meta_title + " failed with error: " + m_error)
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
									file.write(meta_title)
									# New line
									file.write("\n")
									# Close the file
									file.close()
									# Print message
									print("mkvpropedit does not exist in current system. Metadata title for " + new_filename + "will not be updated")
						except OSError as e:
							if e.errno != errno.EEXIST:
								raise
					#Get poster
					poster = data["Poster"]
					if poster == "N/A":
						print("Poster not found!")
					else:
						try:
							# Get into directory
							os.chdir(root)
							# Save image
							urllib.request.urlretrieve(poster, meta_title + ".jpg")
							# Print successful massage
							print("Poster image saved!")
						except OSError as e:
							if e.errno != errno.EEXIST:
								file = open(os.path.expanduser("~") + "/posters_not_found.txt", "a")
								# Append title at the end of file
								file.write(meta_title)
								# New line
								file.write("\n")
								# Close the file
								file.close()
								# Print message
								print("Poster not found for " + new_filename)
					# Print successfull message
					print("Found movie " + meta_title + extension)

# StringBuilder Class
class StringBuilder:
	_file_str = None

	def __init__(self):
		self._file_str = StringIO()

	def Append(self, str):
		self._file_str.write(str)

	def __str__(self):
		return self._file_str.getvalue()

if __name__ == "__main__":
	main()