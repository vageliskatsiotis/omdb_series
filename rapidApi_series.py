import os
import subprocess
import errno
import json
import urllib.request
import urllib.error
import urllib.parse
import requests
import re
import platform
if (platform.system() == "Windows"):
	import winapps
from mutagen import MutagenError
from mutagen.mp4 import MP4
from io import StringIO

# Main
def main():
	# Input season number
	season = input("Insert Season No: ")
	# Make Api Call
	data = GetData(title_series)
	if data:
	    Response(title_series, season, data)
	else:
		print("No data found for this Series!")

# Get Data
def GetData(title_series):
	url = "https://online-movie-database.p.rapidapi.com/title/find"
	querystring = {"q":title_series}
	headers = {
		"X-RapidAPI-Key": "",
		"X-RapidAPI-Host": ""
	}
	response = requests.request("GET", url, headers=headers, params=querystring)
	data = json.loads(response.content)
	result = data['results'][0]
	if result['title'] == title_series:
		id_length = len(result['id'])
		imdbId = result['id'][7:id_length - 1]
	poster = result['image']['url']
	url = "https://online-movie-database.p.rapidapi.com/title/get-seasons"
	querystring = {"tconst":imdbId}
	response = requests.request("GET", url, headers=headers, params=querystring)
	data = json.loads(response.content)
	return data, poster

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
		url = "https://www.omdbapi.com/?t=" + query + "&" + "apikey=" + apikey
	# JSON to string
	data = json.load(urllib.request.urlopen(url))
	# Return data
	return data

# Api Response
def Response(title_series, season, data):
	# Define home directory
	dirPath = os.path.dirname(os.path.realpath(__file__))
	# Escape characters on title
	query = urllib.parse.quote(title_series)
	
	if season != "":
		data = data[0]
		# Get number of episodes
		episodes = data[int(season)-1]["episodes"]
		# Loop through episodes
		for e in episodes:
			# Episode title
			episode_title = e["title"]
			# Episode number
			episode_no = e["episode"]
			# Episode year
			episode_year = str(e["year"])

			try:
				# Get into directory
				os.chdir(dirPath)
				# Iterate on current directory
				RenameLoop(season, title_series, episode_title,
				           episode_no, episode_year, query, dirPath)

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
		poster = data[1]
		if poster == "":
			print("Poster not found!")
		else:
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
			search_title_separator = re.search(r"(.*\.)+.*", file[0:(len(file) - 4)])
			title_separator = " "
			if search_title_separator:
				title_separator = "."
			# Split title in words if query is more than one
			title_array = title_series.split()
			if len(title_array) > 1:
				i = 0
				sb = StringBuilder()
				# Build string using split words
				while i < len(title_array):
					sb.Append(title_array[i] + title_separator)
					i += 1
				# Assign to query minus the last dot
				query = str(sb)[:-1]
			else:
				query = title_series
			if (query.lower() in file.lower()):
				if ("S" + str(season)) in file:
					# Adapt to API's response for episode titles from 1-9 and add 0 in front
					if len(str(episode_no)) == 1:
						new_episode_no = "0" + str(episode_no)
					else:
						new_episode_no = str(episode_no)
					# Change season string for single digit input
					if len(str(season)) == 1:
						season = "0" + str(season)
					# Search parameters in filename eg S01E01
					search_str = re.search(r"(?:\bseason\b|\bSeason\b|s|S)" + season + r"(?:\s|\-|\.)?(?:\bepisode\b|\bEpisode\b|e|E)" + re.escape(new_episode_no), file)
					if(search_str):
						# Get file's length
						file_length = len(file)
						# Get file's extension
						extension = file[file_length - 4 :]
						# Check for invalid characters in response's episode title and remove them
						invalid_match_character = re.compile(r'[<>/{}[\]~`?|:\*"]').search(episode_title)
						if invalid_match_character:
							# Remove invalid Characters
							if invalid_match_character[0] == ":":
								episode_title = re.sub(r'[:]', " -", episode_title)
							episode_title = re.sub(r'[<>/{}[\]~`?|:\*"]', "", episode_title)
						# Prepare rename string
						rename_str = title_series + " - " + "S" + season + "E" + new_episode_no + " - " + episode_title + extension
						# Get file's name
						original_filename = os.path.join(root, file)
						# Get replacement filename
						new_filename = os.path.join(root, rename_str)
						# Rename file
						os.rename(original_filename, new_filename)
						# Metadata title
						meta_title = title_series + " - " + "S" + season + "E" + new_episode_no + " - " + episode_title
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

# StringBuilder Class
class StringBuilder:
	_file_str = None

	def __init__(self):
		self._file_str = StringIO()

	def Append(self, str):
		self._file_str.write(str)

	def __str__(self):
		return self._file_str.getvalue()

# Input series title
title_series = input("Insert Series Title: ")

if __name__ == "__main__":
	while True:
		main()
		again = input('Restart? ')
		if again.lower() not in ('yes', 'y'):
			break
