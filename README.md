# omdb_series

Autorename videos, metadata titles and subs on your local series video library using OMDB API written in Python3

# Directions

omdb_series.py file must be run from root directory of series.
Input of series title and season number is required. Series title is Case Sensitive e.g "Lost" will return results but "lost" will not.
In case no Season No is declared, only the poster for the series is downloaded in root folder.

*** OMDB ApiKey is required to run ***

# Dependencies

mutagen and winapps(Windows only) must be installed in system. Using pip is the easiest way.

curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py

pip install mutagen
pip install winapps

#

Any suggestions. PR and Forks are welcomed.

Have fun.
