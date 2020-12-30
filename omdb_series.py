import os
import subprocess
import errno
import json
import urllib.request
import urllib.error
import urllib.parse
import urllib.request
import urllib.parse
import urllib.error
import re
import platform
if (platform.system() == "Windows"):
	import winapps
from mutagen import MutagenError
from mutagen.mp4 import MP4

# Main
def main():
	
	# Input series title
	title_series = input("Insert Series Title: ")
	# Input season number
	season = input("Insert Season No: ")
	# Make Api Call
	data = ApiCall(title_series, season)
	# Handle Response, if any
	if data["Response"] == "True":
	    Response(title_series, season, data)
	elif data["Response"] == "False":
		print(data["Error"])
	else:
		return
	
# Api Reponse
def Response(title_series, season, data):
	# Define home directory
	dirPath = os.path.dirname(os.path.realpath(__file__))
	# Escape characters on title
	query = urllib.parse.quote(title_series)

	if season != "":
	# Get number of episodes
		episodes = data["Episodes"]
		# Loop through episodes
		for e in episodes:
			# Episode title
			episode_title = e["Title"]
			# Episode number
			episode_no = e["Episode"]
			# Episode year
			episode_year = str(e["Released"])[0:4]

			try:
				# Get into directory
				os.chdir(dirPath)
				# Iterate on current directory
				RenameLoop(season, title_series, episode_title, episode_no, episode_year, query, dirPath)
		
			# Handle Exceptions - Create file with not found episodes
			except OSError as e:
				if e.errno != errno.EEXIST:
					raise
				else:
					# Open a file with access mode "a"
					file = open(os.path.expanduser("~") + "/not_found.txt", "a")
					# Append title at the end of file
					file.write(episode_title)
					# New line
					file.write("\n")
					# Close the file
					file.close()
	else:
		#Get poster
		poster = data["Poster"]
		try:
			# Get into directory
			os.chdir(dirPath)
			# Save image
			urllib.request.urlretrieve(poster, title_series + ".jpg")
			# Print successful massage
			print("Poster image saved!")
		except OSError as e:
			if e.errno != errno.EEXIST:
				raise

# Api Call
def ApiCall(title_series, season):

	url = ""
	data = ""

	# Define apikey
	apikey = ""
	# Escape characters on title
	query = urllib.parse.quote(title_series)
	# Insert season in query if exists
	if season != "":
		url = "https://www.omdbapi.com/?t=" + query + "&" + "Season=" + season + "&" + "apikey=" + apikey
	else :
		url = "https://www.omdbapi.com/?t=" + query + "&" + apikey
	# JSON to string
	data = json.load(urllib.request.urlopen(url))
	# Return data
	return data

# Check if MKVToolNix is installed on Windows
def CheckMKVToolNix():
	for app in winapps.search_installed('MKVToolNix'):
		if app:
			return True
		else:
			return False

# Rename files
def RenameLoop(season, title_series, episode_title, episode_no, episode_year, query, directory):
	# Loop through files
	for root, dirs, files in os.walk(directory):
		for file in files:
			if query in file:
				if season in file:
					# Adapt to API"s response for episode titles from 1-9 and add 0 in front
					if len(episode_no) == 1:
						new_episode_no = "0" + str(episode_no)
					else:
						new_episode_no = episode_no
					# Change season string for single digit No inpu
					if len(season) == 1:
						new_season = "0" + str(season)
					# Search parameters in filename eg S01E01
					search_str = re.search(r"(?:s|S|season|Season^)" + new_season + "(?:e|E|episode|Episode^)" + re.escape(new_episode_no), file)
					if(search_str):
						# Get file"s length
						file_length = len(file)
						# Get file"s extension
						extension = file[file_length - 4 :]
						# Check for invalid characters in response"s episode title and remove them
						invalid_match_character = re.compile(r'[<>/{}[\]~`?|:\*"]').search(episode_title)
						if invalid_match_character:
							# Continue to next episode title if found
							episode_title = episode_title.replace(str(invalid_match_character[0]), "")
						# Prepare rename string
						rename_str = title_series + " - " + "S0" + season + "E" + new_episode_no + " - " + episode_title + extension
						# Get file"s name
						original_filename = os.path.join(root, file)
						# Get replacemet filename
						new_filename = os.path.join(root, rename_str)
						# Rename file
						os.rename(original_filename, new_filename)
						# Metadata title
						meta_title = title_series + " - " + "S0" + season + "E" + new_episode_no + " - " + episode_title
						# Add metadata title and year for mp4 files
						if extension == ".mp4":
							try:
								# New mp4 instance
								video = MP4(new_filename)
								# Add title to instance
								video["\xa9nam"] = meta_title
								# Add year to instance
								video["\xa9day"] = episode_year
								# Save instance metadata to file
								video.save()
							except MutagenError as m_error:
								print("Metadata title for " + new_filename + " failed with error: " + m_error)
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
										file.write(episode_title)
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
						print("Found episode No " + new_episode_no + ": " + episode_title + extension)

if __name__ == "__main__":
  main()