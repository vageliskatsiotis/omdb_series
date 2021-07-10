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

# Main
def main():
	
	# Define home directory
	directory = os.path.dirname(os.path.realpath(__file__))
	try:
		# Get into directory
		os.chdir(directory)
		# Iterate on current directory
		RenameLoop(directory)

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
def RenameLoop(directory):
	# Loop through files
	for root, dirs, files in os.walk(directory):
		# Exclude searching on hidden files and folders
		files = [f for f in files if not f[0] == '.']
		dirs[:] = [d for d in dirs if not d[0] == '.']
		# Loop
		for file in files:
			if (".mp4" in file or ".mkv" in file):
				# Metadata title
				meta_title = file[:-4]
				#get year for filename
				year = file[-9:-5]
				# Get file's length
				file_length = len(file)
				# Get file's extension
				extension = file[file_length - 4:]
				# Get file's name
				original_filename = os.path.join(root, file)
				# Get replacemet filename
				new_filename = os.path.join(root, file)
				# Rename file
				os.rename(original_filename, new_filename)
				if extension == ".mp4":
					try:
						video_orig = MP4(original_filename)
						orig_meta_title = video_orig["\xa9nam"]
						if str(orig_meta_title[0]) == str(meta_title):
							continue
						else:
							# New mp4 instance
							video = MP4(new_filename)
							# Add title to instance
							video["\xa9nam"] = str(meta_title)
							# Add year to instance
							video["\xa9day"] = str(year)
							# Empty comments if any
							video["\251cmt"] = ""
							# Save instance metadata to file
							video.save()
							# Print successfull message
							print("Found movie " + meta_title + extension)
					except MutagenError as m_error:
						print("Metadata title for " + meta_title + " failed with error: " + m_error)
				# Add metadata title for mkv files
				elif extension == ".mkv":
					try:
						with open(original_filename, 'rb') as f:
							video_orig = enzyme.MKV(f)
							orig_title = video_orig.info.title
						if orig_title == meta_title:
							continue
						else:
							# Check OS first and MKVToolNix for Windows
							if ((platform.system() == "Windows") and CheckMKVToolNix()):
								mkvpropedit = r"C:\Program Files\MKVToolNix\mkvpropedit.exe"
								subprocess.run([mkvpropedit, new_filename, '--edit', 'info', '--set', f'title={meta_title}'])
							elif platform.system() == "Linux":
								mkvpropedit = "/usr/bin/mkvpropedit"
								# Check if mkvpropedit exists in linux system
								if os.path.exists(mkvpropedit):
									# Call mkvpropedit using subprocess to change metadata title
									subprocess.run([mkvpropedit, new_filename, '--edit', 'info', '--set', f'title={meta_title}'], capture_output=True)
									# Print successfull message
									print("Found movie " + meta_title + extension)
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
				else:
					# Open a file with access mode "a"
					file = open(os.path.expanduser("~") + "/not_found.txt", "a")
					# Append title at the end of file
					file.write(meta_title)
					# New line
					file.write("\n")
					# Close the file
					file.close()
					#Print
					print("Filetype mp4 or mkv not found for " + new_filename)
					# Print successfull message
					print("Found movie " + meta_title + extension)
						
if __name__ == "__main__":
	while True:
		main()
		again = input('Restart? ')
		if again.lower() not in ('yes', 'y'):
			break