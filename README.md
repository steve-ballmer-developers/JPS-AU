## Overview
**JPS-AU** is a tool for automating the uploading process on jpopsuki.eu.  
This is intended to be used alongside BugsPy.

**Features:**
- JPS Client.
- FTP Support
- FLAC/MP3 Support.
- BugsPy .log Support.

**Installation:**
- Install requirements
```
pip install -r requirements.txt
```

## Command Usage
```
python bugs.py {command_name} {ID/URL}
```
Command  | Description  | Example
------------- | ------------- | -------------
-d, --debug | Provides additional information on upload for debugging purposes | `python autoupload.py -d`
-f, --freeleech | Enables freeleech (VIP+ Userclass Requirement) | `python autoupload.py -f -dir "Z:\Music\Korean\Ego\Ego - E [2020.01.02] [EP] [WEB-MP3]"`
-t, --tags | Add additional tags to upload, separated with comma | `python autoupload.py -t "korean, female.vocalist" -dir "Z:\Music\Korean\Ego\Ego - E [2020.01.02] [EP] [WEB-MP3]"`
-dir, --directory | Appoint directory used for torrent creation | `python autoupload.py -dir "Z:\Music\Korean\Ego\Ego - E [2020.01.02] [EP] [WEB-MP3]"`
-dry, --dryrun | Carries out all actions other than the upload itself.| `python autoupload.py -dir "Z:\Music\Korean\Ego\Ego - E [2020.01.02] [EP] [WEB-MP3]" -dry`

## Config.json  

- It's not recommended to use both local watch/download folders and ftp watch/download folders at the same time as it will result in seeding from 2 locations.

**credentials:**

Config  | Description  | Example
------------- | ------------- | -------------
Username | JPopSuki Username | Slyy
Password  | JPopSuki Password | Password

**local_prefs**  

Config  | Description  | Example
------------- | ------------- | -------------
log_directory | directory containing BugsPy log files  | `Z:/Bugs/Logs`
cover_name | name of cover with extension | `cover.jpg`
add_to_watch_folder | moves .torrent file to local watch folder | `true/false`  
add_to_downloads_folder | moves torrent data to local downloads folder | `true/false`  
local_watch_folder | directory of local watch folder | `Z:/watch/Transmission`
local_downloads_folder | directory of local downloads folder | `Z:/downloads`  


**ftp_prefs:**

Config  | Description  | Example
------------- | ------------- | -------------
enable_ftp  | enable ftp mode, if enabled suggested to disable local watch and downloads folders | `true/false`
add_to_watch_folder | transfer .torrent file to watch folder on FTP server | `true/false`
add_to_downloads_folder | transfer torrent data to downloads folder on FTP server | `true/false`
ftp_server | url of ftp server | haze.seedhost.eu
ftp_username | username of ftp account | slyy
ftp_password | password of ftp account | password
ftp_watch_folder | directory of ftp watch folder | `/downloads/watch/transmission`
ftp_downloads_folder | directory of ftp downloads folder | `/downloads`


## Disclaimer
- The usage of this script **may be** illegal in your country. It's your own responsibility to inform yourself of Copyright Law.
