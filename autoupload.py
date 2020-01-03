# Standard library packages
import re
import os
import sys
import string
import argparse
import html
from urllib.parse import urlparse
import json
import ftplib

# Third-party packages
import requests
from bs4 import BeautifulSoup
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from torf import Torrent
from tqdm import tqdm
from langdetect import detect

# JPS-AU files
import jpspy

def asciiart ():
    print("""
     ██╗██████╗ ███████╗       █████╗ ██╗   ██╗
     ██║██╔══██╗██╔════╝      ██╔══██╗██║   ██║
     ██║██████╔╝███████╗█████╗███████║██║   ██║
██   ██║██╔═══╝ ╚════██║╚════╝██╔══██║██║   ██║
╚█████╔╝██║     ███████║      ██║  ██║╚██████╔╝
 ╚════╝ ╚═╝     ╚══════╝      ╚═╝  ╚═╝ ╚═════╝

""")

# Get arguments using argparse
def getargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-dir', '--directory', help='Initiate upload on directory', nargs='?', required=True)
    parser.add_argument("-f", "--freeleech", help="Enables freeleech", action="store_true")
    parser.add_argument('-d', '--debug', help='Enable debug mode', action='store_true')
    parser.add_argument("-dry", "--dryrun", help="Dryrun will carry out all actions other than the actual upload to JPS.", action="store_true")

    return parser.parse_args()

# Acquire the authkey used for torrent files from upload.php
def getauthkey():
    uploadpage = j.retrieveContent("https://jpopsuki.eu/upload.php")
    soup = BeautifulSoup(uploadpage.text, 'html5lib')
    rel2 = str(soup.select('#wrapper #content .thin'))
    # Regex returns multiple matches, could be optimized.
    authkey = re.findall("(?<=value=\")(.*)(?=\")", rel2)[0]

    return authkey

# Creates torrent file using torf module.
def createtorrent(authkey, directory, filename):
    t = Torrent(path=directory,
                trackers=[authkey]) # Torf requires we store authkeys in a list object. This makes it easier to add multiple announce urls.
    # Set torrent to private as standard practice for private trackers
    t.private = True
    t.generate()
    filename = f"{filename}.torrent"
    t.write(filename)
    print(f"Torrent has been created for {filename}")

    return filename

# Reads FLAC file and returns metadata.
def readflac(filename):
    read = FLAC(filename)

    # Create dict containing all meta fields we'll be using.
    tags={
        "ALBUM": read['album'],
        "ALBUMARTIST": read['albumartist'],
        "ARTIST": read['artist'],
        "DATE": read['date'][0],
        "GENRE": read['genre'],
        "TITLE": read['title'],
        "COMMENT": read['comment']}

    # Not further looked into this but some FLACs hold a grouping key of contentgroup instead of grouping.
    try:
        tags['GROUPING'] = read['grouping']
    except KeyError:
        tags['GROUPING'] = read['contentgroup']

    return tags

# Reads MP3 file and returns metadata.
def readmp3(filename):
    read = MP3(filename)

    # Create dict containing all meta fields we'll be using.
    tags={
        "ALBUM": read['TALB'].text,
        "ALBUMARTIST": read['TPE2'].text,
        "ARTIST": read['TPE1'].text,
        "DATE": str(read['TDRC']),
        "GENRE": read['TCON'].text,
        "TITLE": read['TIT2'].text,
        "COMMENT": read['COMM::eng'].text,
        "GROUPING": read['TIT1'].text}

    return tags

def readlog(log_name, log_directory):
    with open(f"{log_directory}/{log_name}.log", "r+") as f:
        log_contents = f.read()

    return log_contents

def add_to_hangul_dict(hangul , english , category):
    hangul = str(hangul)
    english = str(english)

    categories = ['version','general','artist','genres', 'label', 'distr']
    file = f"json_data/dictionary.json"
    json_file = open(file, 'r', encoding='utf-8', errors='ignore')
    dictionary = json.load(json_file)
    json_file.close()

    new = dict()
    for cats in dictionary:
        #== Create the categories in the new temp file
        new[cats] = dict()

        for key,value in dictionary[cats].items():
            #== List all the old items into the new dict
            new[cats][key] = value

    if hangul in new[category].keys():

        if new[category].get(hangul) is None:

            if english != 'None':
                new[category][hangul] = english

        else:
            #== Only update if English word has been supplied ==#
            if english != 'None':
                new[category][hangul] = english
    else:

        if english == 'None':
            new[category][hangul] = None
        else:
            new[category][hangul] = english

    json_write = open(file, 'w+', encoding='utf-8')
    json_write.write(json.dumps(new, indent=4, ensure_ascii=False))
    json_write.close()

def translate(string, category, result=None, output=None):

    file = "json_data/dictionary.json"
    with open(file, encoding='utf-8', errors='ignore') as f:
        dictionary = json.load(f, strict=False)

    category = str(category)
    string = str(string)
    search = dictionary[category]
    string = string.strip()

    if string == 'Various Artists':
        output = ['Various Artists',None]
    else:
        #== NO NEED TO SEARCH - STRING HAS HANGUL+ENGLISH or HANGUL+HANGUL ==#
        if re.search("\((?P<inside>.*)\)", string):
        #== Complete translation, add to dictionary with both values ==#

            #== Contains parentheses, need to split
            parenthesis = string.split("(")
            pre_parenthesis = parenthesis[0].strip()
            in_parenthesis = parenthesis[1].replace(")","").strip()

            #== Check the order of the parentheses ==#

            if re.search("[^\u0000-\u007F]+",pre_parenthesis) and re.search("[^\u0000-\u007F]+",in_parenthesis):
                #== Both hangul
                first = 'kr'
                second = 'kr'
            else:
                if re.search("[^\u0000-\u007F]+",pre_parenthesis):
                    first = 'kr'
                    second = 'eng'
                else:
                    first = 'eng'
                    second = 'kr'

            if first == 'kr' and second == 'eng':
                #== Hangul first ==#
                hangul = pre_parenthesis
                english = in_parenthesis
                add_to_hangul_dict(hangul,english,category)

            elif first == 'eng' and second == 'kr':
                #== English first ==#
                hangul = in_parenthesis
                english = pre_parenthesis
                add_to_hangul_dict(hangul,english,category)
            elif first == 'kr' and second == 'kr':
                #== Both Hangul ==#
                hangul = pre_parenthesis
                english = None
                add_to_hangul_dict(pre_parenthesis,None,category)
                add_to_hangul_dict(hangul,None,category)
            else:
                #== Both English
                hangul = None
                english = pre_parenthesis

            output = [hangul,english]

        #== No parentheses - HANGUL
        else:

            #== If the input string is a full Hangul word - check dictionary and then add if necessary)
            if re.search("[^\u0000-\u007F]+", string):

                if string in search.keys():
                #== yes
                    if search.get(string) is None:
                        #== If the keyword does not have a translation, add it to the dictionary ==#
                        output = [string,None]
                    else:
                        #== Translation already exists, output the result in a list ==#
                        output = [string,search.get(string)]
                else:
                    output = [string,None]
                    add_to_hangul_dict(string, None, category)

            #== Full English name -- leave it
            else:
                for key,value in search.items():
                    if key == string:
                        output = [value,string]
                        break
                    else:
                        output = [string,string]

    return output

def gatherdata(directory):
    ## List objects used to compare files.
    # The reason we do this is because we need to confirm all files contain the same meta before uploading.
    list_album_artists = []
    list_track_artists = []
    list_album = []
    list_genre = []
    translated_genre = []
    translated_album_artists = []
    releasedata = {}

    ## Set no log as default value.
    # This will be set to True is a .log file is found, in turn this will allow us to determine if WEB or CD.
    log_available = False
    flac_present = False
    mp3_present = False
    # Read directory contents, grab metadata of .FLAC files.
    for file in os.listdir(directory):
        file_location = os.path.join(directory, file)
        if file.endswith(".flac"):
            # Read FLAC file to grab meta
            tags = readflac(file_location)
            flac_present = True
        if file.endswith(".mp3"):
            # Read MP3 file to grab meta
            tags = readmp3(file_location)
            mp3_present = True
        if debug:
            print(f"Tags for {file}:\n{tags}")
        # If only one genre in list attempt to split as there's likely more.
        if len(tags['GENRE']) == 1:
            tags['GENRE'] = tags['GENRE'][0].split(";")
        for aa in tags['ALBUMARTIST']:
            list_album_artists.append(aa)
        for a in tags['ARTIST']:
            list_track_artists.append(a)
        list_album.append(tags['ALBUM'][0])
        for g in tags['GENRE']:
            list_genre.append(g)


        # Check files to make sure there's no multi-format.
        if flac_present:
            format = 'FLAC'
            bitrate = 'Lossless'
        if mp3_present:
            format = 'MP3'
            bitrate = '320'
        if flac_present and mp3_present:
            print("Mutt detected, exiting.")
            sys.exit()

        if file.endswith(".log"):
            log_available = True

        if log_available == True:
            media = 'CD'
        else:
            media = 'WEB'

    # Translate genre's using our dict as jps uses specific tagging.
    file = "json_data/dictionary.json"
    with open(file, encoding='utf-8', errors='ignore') as f:
        dictionary = json.load(f, strict=False)

    for g in set(list_genre):
        translation = translate(g, "genres")[0]
        translated_genre.append(translation)

    for a in set(list_album_artists):
        translated_artist_name = translate(string=tags['ALBUMARTIST'][0], category="artist")
        translated_album_artists.append(translated_artist_name[1])

    ## Identify unique values using sets.
    unique_album_artists = ','.join(set(translated_album_artists))
    unique_track_artists = ','.join(set(list_track_artists))
    unique_genre = ','.join(set(translated_genre))
    unique_album = set(list_album)

    ## Acquire contents of our log file to be used for album description
    # Comments store the album id which matches our log names, so we can use the comment tag to find our album descriptions.
    log_filename = tags['COMMENT'][0]
    log_directory = cfg['local_prefs']['log_directory']
    # Album description taken from log file.
    album_description = readlog(log_filename, log_directory)
    # Release description
    release_description = f"Sourced from [url=https://music.bugs.co.kr/album/{tags['COMMENT'][0]}]Bugs[/url]"

    ## Assign all our unique values into releasedata{}. We'll use this later down the line for POSTING.
    # POST values can be found by inspecting JPS HTML
    releasedata['submit'] = 'true'
    releasedata['type'] = translate(tags['GROUPING'][0], "release_types")[0]
    releasedata['title'] = tags['ALBUM'][0]
    releasedata['artist'] = unique_album_artists
    # If the value of album artist and artist is the same, we don't need to POST original artist.
    if unique_album_artists != unique_track_artists:
        releasedata['artistjp'] = unique_track_artists
    #re.sub removes any date separators, jps doesn't accept them
    releasedata['releasedate'] = re.sub(r"[^0-9]", "", tags['DATE'])
    releasedata['format'] = format
    releasedata['bitrate'] = bitrate
    releasedata['media'] = media
    releasedata['album_desc'] = album_description
    releasedata['release_desc'] = release_description
    releasedata['tags'] = unique_genre

    #Enable freeleech if arg is passed
    if freeleech:
        releasedata['freeleech'] = "true" 

    return releasedata

# Simple function to split a string up into characters
def split(word):
    return [char for char in word]

def detectlanguage(string):
    ## Language Detect
    # This is a required check as we don't want to enter non-english/romaji characters into the title field.
    characters = split(string)
    language_list = []
    for c in characters:
        try:
            language = detect(c)
            language_list.append(language)
        except:
            langauge = "error"

    if 'ko' in language_list:
        en = False
    else:
        en = True

    if debug:
        print(f"Language List: {language_list}")

    return en

def uploadtorrent(torrent, cover, releasedata):

    # POST url.
    uploadurl = "https://jpopsuki.eu/upload.php"

    ## Language Checks
    # This is a required check as we don't want to enter non-english/romaji characters into the title/artist field.
    en = detectlanguage(releasedata['title'])
    if debug:
        print(f"{releasedata['title']} language: {en}")
    if en == False:
        input_english_title = input("\n" + "_" * 62 + "\nKorean/Japanese Detected. Please enter the romaji/english title:\n")
        # Create new key called titlejp and assign the old title to it
        releasedata['titlejp'] = releasedata['title']
        # Replace title with the user input.
        releasedata['title'] = input_english_title

    en = detectlanguage(releasedata['artist'])
    if debug:
        print(f"{releasedata['artist']} language: {en}")
    if en == False:
        input_english_artist = input("\n" + "_" * 62 + "\nKorean/Japanese Detected. Please enter the romaji/english artist name:\n")
        # Create new key called titlejp and assign the old title to it
        # Replace title with the user input.
        releasedata['artist'] = input_english_artist

    # Dataset containing all of the information obtained from our FLAC files.
    data = releasedata

    if debug:
        print('_' * 100)
        print('Release Data:\n')
        print(releasedata)

    postDataFiles = {
        'file_input': open(torrent, 'rb'),
        'userfile': open(cover, 'rb')
    }

    JPSres = j.retrieveContent(uploadurl, "post", data, postDataFiles)
    ## TODO Filter through JPSres.text and create error handling based on responses
    #print(JPSres.text)
    print('Upload POSTED')

# Function for transferring the contents of the torrent as well as the torrent.
def ftp_transfer(fileSource, fileDestination, directory, folder_name, watch_folder):

    # Create session
    session = ftplib.FTP(cfg['ftp_prefs']['ftp_server'],cfg['ftp_prefs']['ftp_username'],cfg['ftp_prefs']['ftp_password'])
    # Set session encoding to utf-8 so we can properly handle hangul/other special characters
    session.encoding='utf-8'

    # Successful FTP Login Print
    print("_" * 100)
    print("FTP Login Successful")
    print(f"Server Name: {cfg['ftp_prefs']['ftp_server']}  :  Username: {cfg['ftp_prefs']['ftp_username']}\n")

    if cfg['ftp_prefs']['add_to_downloads_folder']:

        # Create folder based on the directory name of the folder within the torrent.
        try:
            session.mkd(f"{fileDestination}/{folder_name}")
            print(f'Created directory {fileDestination}/{folder_name}')
        except ftplib.error_perm:
            pass

        # Notify user we are beginning the transfer.
        print(f"Beginning transfer...")
        # Set current folder to the users preferred destination
        session.cwd(f"{fileDestination}/{folder_name}")
        # Transfer each file in the chosen directory
        for file in os.listdir(directory):
            with open(f"{directory}/{file}",'rb') as f:
                filesize = os.path.getsize(f"{directory}/{file}")
                ## Transfer file
                # tqdm used for better user feedback.
                with tqdm(unit = 'blocks', unit_scale = True, leave = False, miniters = 1, desc = f'Uploading [{file}]', total = filesize) as tqdm_instance:
                    session.storbinary('STOR ' + file, f, 2048, callback = lambda sent: tqdm_instance.update(len(sent)))
                print(f"{file} | Complete!")
                f.close()

    if cfg['ftp_prefs']['add_to_watch_folder']:
        with open(fileSource,'rb') as t:
            # Set current folder to watch directory
            session.cwd(watch_folder)
            ## Transfer file
            # We avoid tqdm here due to the filesize of torrent files.
            # Most connections will upload these within 1-3s, resulting in near useless progress bars.
            session.storbinary(f"STOR {torrentfile}", t)
            print(f"{torrentfile} | Sent to watch folder!")
            t.close()
    # Quit session when complete.
    session.quit()

def localfileorganization(torrent, directory, watch_folder, downloads_folder):

    # Move torrent directory to downloads_folder
    if cfg['local_prefs']['add_to_downloads_folder']:
        os.rename(directory, f"{downloads_folder}/{directory}")
    # Move torrent file to ftp_watch_folder
    if cfg['local_prefs']['add_to_watch_folder']:
        os.rename(torrent, f"{watch_folder}/{torrent}")

if __name__ == "__main__":

    asciiart()
    args = getargs()

    # TODO consider calling args[] directly, we will then not need this line
    dryrun = freeleech = directory = debug = None

    directory = args.directory

    if args.dryrun:
        dryrun = True

    if args.debug:
        debug = True

    if args.freeleech:
        freeleech = True

    # Load login credentials from JSON and use them to create a login session.
    with open(f'json_data/config.json') as f:
        cfg = json.load(f)
    loginData = {'username': cfg['credentials']['username'], 'password': cfg['credentials']['password']}
    loginUrl = "https://jpopsuki.eu/login.php"
    loginTestUrl = "https://jpopsuki.eu"
    successStr = "Latest 5 Torrents"

    # j is an object which can be used to make requests with respect to the loginsession
    j = jpspy.MyLoginSession(loginUrl, loginData, loginTestUrl, successStr, debug=args.debug)
    # Acquire authkey
    authkey = getauthkey()
    # Gather data of FLAC file
    releasedata = gatherdata(directory)

    # Folder_name equals the last folder in the path, this is used to rename .torrent files to something relevant.
    folder_name = os.path.basename(os.path.normpath(directory))
    # Identifying cover.jpg path
    cover_path = directory + "/" + cfg['local_prefs']['cover_name']

    # Create torrent file.
    torrentfile = createtorrent(authkey, directory, folder_name)

    # Upload torrent to JPopSuki
    if dryrun != True:
        uploadtorrent(torrentfile, cover_path, releasedata)

    # Setting variable for watch/download folders
    ftp_watch_folder = cfg['ftp_prefs']['ftp_watch_folder']
    ftp_downloads_folder = cfg['ftp_prefs']['ftp_downloads_folder']
    local_watch_folder = cfg['local_prefs']['local_watch_folder']
    local_downloads_folder = cfg['local_prefs']['local_downloads_folder']


    if cfg['ftp_prefs']['enable_ftp']:
        ftp_transfer(fileSource=torrentfile, fileDestination=ftp_downloads_folder, directory=directory, folder_name=folder_name, watch_folder=ftp_watch_folder)

    if cfg['local_prefs']['add_to_watch_folder'] or cfg['local_prefs']['add_to_downloads_folder']:
        localfileorganization(torrent=torrentfile, directory=directory, watch_folder=local_watch_folder, downloads_folder=local_downloads_folder)
