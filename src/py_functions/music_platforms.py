import PIL  # Used by music_tag
from re import findall, sub
from typing import Optional
from bs4 import BeautifulSoup
from music_tag import load_file as tag_load_file
from requests import get
from unicodedata import normalize
from youtubesearchpython import SearchVideos
from yt_dlp import YoutubeDL


def sanitize_title(title: str) -> str:
    """
    Sanitize title
    :param title:  Title
    :return:  Sanitized title
    """

    normalized_title = (
        normalize('NFKD', title).encode('ASCII', 'ignore').decode('utf-8')
    )
    sanitized_title = sub(r'[^a-zA-Z0-9\-_()[\]{}# ]', '', normalized_title).strip()
    return sanitized_title


def music_platform_categorizer(pyclass, query_list: list, TColor) -> list:
    platform_regexes = {
        'youtube_playlist': r'^https:\/\/(?:www\.)?(?:youtu\.be\/(?:playlist\?list=|[^\/]+\?list=)|youtube\.com\/.*\blist=[^&\s]+|music\.youtube\.com\/.*\blist=[^&\s]+).*$',
        'youtube_track': r'^https://(?:www\.)?(?:youtu\.be/|youtube\.com/watch\?v=|music\.youtube\.com/watch\?v=)([^/?&\s]+)$',
        'resso_playlist': r'^(https?://)?(www\.)?resso\.com/playlist/[\w%-]+$',
        'resso_track': r'^https:\/\/www\.resso\.com\/track\/(?!.*playlist\/)\d+(?:\.\d+)?$',
        'deezer_playlist': r'^https:\/\/www\.deezer\.com\/(?:\w{2}\/)?playlist\/\d+$',
        'deezer_track': r'https:\/\/www\.deezer\.com\/(?:[a-zA-Z]{2}\/)?track\/\d+',
        'spotify_playlist': r'^(https:\/\/open\.spotify\.com\/playlist\/[A-Za-z0-9]+)$',
        'spotify_track': r'^https:\/\/open\.spotify\.com\/track\/[a-zA-Z0-9]+$',
        'queries': r'^(?!.*(?:https?://|www\.)[\w\-\.]+\.[a-zA-Z]{2,3}(/\S*)?$).*',
    }

    for query in query_list:
        now_processing_number = query_list.index(query) + 1
        print(
            f'  {TColor.LYELLOW}Progress: {TColor.WHITE}{now_processing_number}/{TColor.WHITE}{len(query_list)}',
            end='\r',
        )

        matches = dict()
        for source, regex in platform_regexes.items():
            match = findall(regex, query)
            matches[source] = bool(match)

        for source, match in matches.items():
            if match:
                if source == 'youtube_playlist':
                    pyclass.youtube_playlist.append(query)
                elif source == 'youtube_track':
                    pyclass.youtube_track.append(query)
                elif source == 'resso_playlist':
                    pyclass.resso_playlist.append(query)
                elif source == 'resso_track':
                    pyclass.resso_track.append(query)
                elif source == 'deezer_playlist':
                    pyclass.deezer_playlist.append(query)
                elif source == 'deezer_track':
                    pyclass.deezer_track.append(query)
                elif source == 'spotify_playlist':
                    pyclass.spotify_playlist.append(query)
                elif source == 'spotify_track':
                    pyclass.spotify_track.append(query)
                elif source == 'queries':
                    pyclass.youtube_track.append(
                        get_youtube_url_from_query(query=query)
                    )
                break
    print(
        f'  {TColor.LYELLOW}Successfully categorized: {TColor.WHITE}{len(query_list)} {TColor.YELLOW}queries'
    )
    return pyclass


def get_youtube_url_from_query(query: str) -> Optional[str]:
    """
    Get youtube url from query
    :param query:  Query
    :return:  Youtube url or None if not found
    """

    try:
        scrapping_results = SearchVideos(
            query, offset=1, mode='dict', max_results=1
        ).result()
        return scrapping_results['search_result'][0]['link']
    except Exception:
        return None


def get_musics_from_youtube_playlist(url: str) -> list:
    """
    Get musics from youtube playlist
    :param url:  Youtube playlist url
    :return:  List of musics
    """

    ydl_opts = {
        'ignoreerrors': True,
        'quiet': True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        playlist_info = ydl.extract_info(url, download=False)
        if 'entries' in playlist_info:
            videos = playlist_info['entries']
            video_list = list()
            for video in videos:
                video_list.append(video['webpage_url'])
            return video_list


def get_music_name_from_resso_playlist(url: str) -> list:
    """
    Get music name from resso playlist
    :param url:  Resso playlist url
    :return:  List of music names
    """

    soup = BeautifulSoup(get(url).content, 'html.parser')
    song_list = [
        song.find('a', {'class': 'song-wrapper'})
        for song in soup.find_all('li', {'class': 'song-item'})
    ]
    song_list = [song['title'] for song in song_list if song is not None]
    return song_list


def get_music_name_from_resso_track(url: str) -> str:
    """
    Get name from resso track
    :param url:  Resso track url
    :return:  Music name
    """

    soup = BeautifulSoup(get(url).content, 'html.parser')
    title = soup.find('div', {'class': 'immersive-info-detail'}).find('h1').text.strip()
    author = soup.find('div', {'class': 'subtitle'}).find('a').text.strip()
    return title + ' - ' + author


def get_music_name_from_deezer_playlist(url: str) -> list:
    soup = BeautifulSoup(get(url).content, 'html.parser')
    title_list = [
        song.find('span', {'itemprop': 'name'})
        for song in soup.find_all('div', {'class': 'wrapper ellipsis'})
    ]
    title_list = [song.text.strip() for song in title_list if song is not None]
    author_list = [
        author.find('a', {'itemprop': 'byArtist'})
        for author in soup.find_all('td', {'class': 'artist'})
    ]
    author_list = [author.text.strip() for author in author_list if author is not None]
    formatted_song_list = [
        song + ' - ' + author for song, author in zip(title_list, author_list)
    ]
    return formatted_song_list


def get_music_name_from_deezer_track(url: str) -> str:
    soup = BeautifulSoup(get(url).content, 'html.parser')
    title = soup.find('h1').text.strip()
    author = soup.find('meta', {'itemprop': 'description'})['content']
    return title + ' - ' + author


def get_music_name_from_spotify_playlist(url: str) -> list:
    soup = BeautifulSoup(get(url).content, 'html.parser')
    url_list = [
        meta['content'] for meta in soup.find_all('meta', {'name': 'music:song'})
    ]
    formatted_song_list = [
        song + ' - ' + author.split('·')[0].strip()
        for url in url_list
        for song, author in [
            (
                BeautifulSoup(get(url).content, 'html.parser')
                .find('meta', {'property': 'og:title'})['content']
                .strip(),
                BeautifulSoup(get(url).content, 'html.parser').find(
                    'meta', {'property': 'og:description'}
                )['content'],
            )
        ]
    ]
    return formatted_song_list


def get_music_name_from_spotify_track(url: str) -> str:
    soup = BeautifulSoup(get(url).content, 'html.parser')
    title = soup.find('meta', {'property': 'og:title'})['content'].strip()
    author = (
        soup.find('meta', {'property': 'og:description'})['content']
        .split('·')[0]
        .strip()
    )
    return title + ' - ' + author


def get_youtube_song_metadata(url: str) -> dict:
    """
    Get youtube song metadata
    :param url:  Youtube url
    :return:  Song metadata dict
    """

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }
    info = YoutubeDL(ydl_opts).extract_info(url, download=False)
    return info


def download_song_from_youtube(info: dict, output_dir) -> str:
    """
    Download song from youtube
    :param info:  Song metadata
    :param output_dir:  Output directory
    :return:  Music path
    """

    url = info['webpage_url']
    music_path_wo_ext = f'{output_dir}/{sanitize_title(info["title"])}'

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{music_path_wo_ext}',
        'quiet': True,
        'no_warnings': True,
        'nooverwrites': True,
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'opus',
                'preferredquality': '128',
            }
        ],
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return f'{music_path_wo_ext}.opus'


def add_song_metadata(info: dict, music_path: str) -> None:
    """
    Add song metadata
    :param info:  Song metadata
    :param music_path:  Music path
    :return:  None
    """

    # Get song metadata
    title = sanitize_title(info['title'])
    author = info['uploader']
    publish_year = info['upload_date'][:4]

    # Get artwork data from youtube
    artwork_url = f'https://img.youtube.com/vi/{info["id"]}/maxresdefault.jpg'
    artwork_data = get(artwork_url).content

    f = tag_load_file(music_path)
    f['artwork'] = bytes(artwork_data)
    f['tracktitle'] = title
    f['artist'] = author
    f['year'] = publish_year
    f['albumartist'] = author
    f.save()
