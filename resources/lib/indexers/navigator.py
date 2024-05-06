# -*- coding: utf-8 -*-

'''
    M3 Online (Adatbázis)
    Copyright (C) 2024 heg, vargalex

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import os, sys, re, xbmc, xbmcgui, xbmcplugin, xbmcaddon, xbmcvfs, locale, base64
from bs4 import BeautifulSoup
import requests
import urllib.parse
import resolveurl as urlresolver
from resources.lib.modules.utils import py2_decode, py2_encode
import html
import json
import time

sysaddon = sys.argv[0]
syshandle = int(sys.argv[1])
addonFanart = xbmcaddon.Addon().getAddonInfo('fanart')

version = xbmcaddon.Addon().getAddonInfo('version')
kodi_version = xbmc.getInfoLabel('System.BuildVersion')
base_log_info = f'M3 Online (Adatbázis) | v{version} | Kodi: {kodi_version[:5]}'

xbmc.log(f'{base_log_info}', xbmc.LOGINFO)

base_url = 'https://nemzetiarchivum.hu'

addon = xbmcaddon.Addon('plugin.video.m3_online_database')

cookies = {
    'MtvaArchivumLastPage': 'https%3A%2F%2Fnemzetiarchivum.hu%2Fm3',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
}

if sys.version_info[0] == 3:
    from xbmcvfs import translatePath
    from urllib.parse import urlparse, quote_plus
else:
    from xbmc import translatePath
    from urlparse import urlparse
    from urllib import quote_plus

class navigator:
    def __init__(self):
        try:
            locale.setlocale(locale.LC_ALL, "hu_HU.UTF-8")
        except:
            try:
                locale.setlocale(locale.LC_ALL, "")
            except:
                pass
        self.base_path = py2_decode(translatePath(xbmcaddon.Addon().getAddonInfo('profile')))
        self.searchFileName = os.path.join(self.base_path, "search.history")

    def root(self):
        self.addDirectoryItem("M3 Online (Adatbázis)", f"get_database", '', 'DefaultFolder.png')
        self.addDirectoryItem("Keresés", f"search", '', 'DefaultFolder.png')
        self.endDirectory()

    def GetDatabase(self, program_id, data_released, data_title, data_extra, data_image_link, year, duration, short_description):

        import urllib.request
        import gzip
        import os
        import csv
        import json
        from datetime import datetime, timedelta
        
        gz_url = "https://m3.devs.space/public/m3-db.csv.gz"

        def remove_old_files(addon_data_path, new_filenames):
            for filename in os.listdir(addon_data_path):
                if filename.endswith(".json") or filename.endswith(".csv") or filename.endswith(".csv.gz"):
                    if filename not in new_filenames:
                        file_path = os.path.join(addon_data_path, filename)
                        os.remove(file_path)
        
        def get_unix_from_filename(filename):
            try:
                unix_part = filename.split("_")[0]
                unix_timestamp = int(unix_part)
                return unix_timestamp
            except (ValueError, IndexError):
                xbmc.log(f"{base_log_info} | Error converting filename to UNIX timestamp: {filename}", xbmc.LOGERROR)
                return 0
        
        def get_time_from_unix(unix_timestamp):
            return datetime.fromtimestamp(unix_timestamp)
        
        def needs_refresh(file_paths, refresh_time):
            if 'json' not in file_paths or not file_paths['json']:
                return True

            json_modification_time = os.path.getmtime(file_paths['json'])
            file_time = datetime.fromtimestamp(json_modification_time)

            if datetime.now().time() > refresh_time:
                if file_time.date() < datetime.now().date():
                    return True
        
            return False
        
        refresh_time = datetime.strptime("07:35:00", "%H:%M:%S").time()
        
        file_paths = {
            'gz': None,
            'csv': None,
            'json': None
        }
        
        addon = xbmcaddon.Addon('plugin.video.m3_online_database')
        addon_data_path = xbmcvfs.translatePath('special://userdata/addon_data/plugin.video.m3_online_database')
        
        if not os.path.exists(addon_data_path):
            os.makedirs(addon_data_path)
        
        for filename in os.listdir(addon_data_path):
            if filename.endswith(".json"):
                file_paths['json'] = os.path.join(addon_data_path, filename)
            elif filename.endswith(".csv"):
                file_paths['csv'] = os.path.join(addon_data_path, filename)
            elif filename.endswith(".csv.gz"):
                file_paths['gz'] = os.path.join(addon_data_path, filename)
        
        if needs_refresh(file_paths, refresh_time):
            unix_timestamp = int(datetime.timestamp(datetime.now()))
            file_path_gz = os.path.join(addon_data_path, f"{unix_timestamp}_m3-db-daily.csv.gz")
            file_path_csv = os.path.join(addon_data_path, f"{unix_timestamp}_m3-db-daily.csv")
            file_path_json = os.path.join(addon_data_path, f"{unix_timestamp}_m3-db-daily.json")
        
            remove_old_files(addon_data_path, [file_path_gz, file_path_csv, file_path_json])
        
            try:
                urllib.request.urlretrieve(gz_url, file_path_gz)
        
                with gzip.open(file_path_gz, 'rb') as f_in:
                    with open(file_path_csv, 'wb') as f_out:
                        f_out.write(f_in.read())
            except Exception as e:
                xbmc.log(f"{base_log_info} | Failed to download or extract CSV file: {str(e)}", xbmc.LOGERROR)
        
            data_list = []
        
            with open(file_path_csv, 'r', encoding='utf-8') as file:
                csv_reader = csv.reader(file, delimiter=';')
        
                for row in csv_reader:
                    data_dict = {
                        'program_id': row[0],
                        'title': row[1],
                        'subtitle': row[2],
                        'episode': row[3],
                        'episodes': row[4],
                        'seriesId': row[5],
                        'quality': row[6],
                        'year': row[7],
                        'duration': row[8],
                        'short_description': row[9],
                        'released': row[10]
                    }
                    data_list.append(data_dict)
        
            with open(file_path_json, 'w', encoding='utf-8') as json_file:
                json.dump(data_list, json_file, ensure_ascii=False)
        else:
            xbmc.log(f"{base_log_info} | Meglévő json betöltve.", xbmc.LOGINFO)
        
            with open(file_paths['json'], 'r', encoding='utf-8') as json_file:
                data_list = json.load(json_file)
        
        results = []
        for data in data_list:
            episode = data.get('episode')
            sec_title = data.get('title')
            series_title = data.get('seriesId')
            episodes = data.get('episodes')
            subtitle = data.get('subtitle')
            short_description = data.get('short_description')
            relesed_date = data.get('released')
            year = data.get('year')
        
            try_image = f'{base_url}/images/m3/{data["program_id"]}'
            
            quality = data.get('quality')
            if quality == 'UHD':
                quality = '4K'
        
            extra_title = ""
            if episode:
                if episode.isdigit():
                    extra_title = f"({episode}/{episodes})"
                else:
                    episode = "0"
            else:
                episode = "0"
        
            new_title_parts = [part for part in [series_title, sec_title, subtitle] if part]
            if sec_title and series_title and sec_title != series_title:
                new_title = " - ".join(new_title_parts)
            elif subtitle:
                new_title = " - ".join([series_title, subtitle])
            else:
                new_title = " - ".join([sec_title])
        
            results.append({'program_id': data['program_id'],
                            'title': new_title,
                            'extra_title': extra_title,
                            'subtitle': subtitle,
                            'episode': int(episode),
                            'episodes': episodes,
                            'seriesId': series_title,
                            'quality': quality,
                            'year': data.get('year'),
                            'duration': data['duration'],
                            'short_description': short_description,
                            'released': data.get('released'),
                            'image_link': try_image
                            })
        
        is_first_line = True
        
        for idx, data in enumerate(results, start=1):
            if is_first_line:
                is_first_line = False
                continue
            
            
            if data['extra_title'] != "(0/0)":
                
                picked_info = f'extr_picked&program_id={data["program_id"]}&data_released={data["released"]}&data_title={data["title"]}&data_extra={data["extra_title"]}&data_image_link={data["image_link"]}&year={data["year"]}&duration={data["duration"]}&short_description={data["short_description"]}'
                
                meta_info = {'title': f'{data["title"]} - {data["extra_title"]}', 'plot': f'{data["released"]}\nid: {data["program_id"]}\n{data["year"]}\n{data["short_description"]}'}
                
                self.addDirectoryItem(f'[B]{data["released"]} - {data["title"]} - {data["extra_title"]}[/B]', 
                                      f'{picked_info}', 
                                      f'{data["image_link"]}', 'DefaultMovies.png', isFolder=True, meta=meta_info)

            else:
                
                picked_info = f'extr_picked&program_id={data["program_id"]}&data_released={data["released"]}&data_title={data["title"]}&data_extra={data["extra_title"]}&data_image_link={data["image_link"]}&year={data["year"]}&duration={data["duration"]}&short_description={data["short_description"]}'
                
                meta_info = {'title': f'{data["title"]}', 'plot': f'{data["released"]}\nid: {data["program_id"]}\n{data["year"]}\n{data["short_description"]}'}
                
                self.addDirectoryItem(f'[B]{data["released"]} - {data["title"]}[/B]', 
                                      f'{picked_info}', 
                                      f'{data["image_link"]}', 'DefaultMovies.png', isFolder=True, meta=meta_info)
        
        self.endDirectory('series')

    def SearchDatabase(self, program_id, data_released, data_title, data_extra, data_image_link, year, duration, short_description, search_this):

        import urllib.request
        import gzip
        import os
        import csv
        import json
        from datetime import datetime, timedelta
        
        gz_url = "https://m3.devs.space/public/m3-db.csv.gz"
        
        def remove_old_files(addon_data_path, new_filenames):
            for filename in os.listdir(addon_data_path):
                if filename.endswith(".json") or filename.endswith(".csv") or filename.endswith(".csv.gz"):
                    if filename not in new_filenames:
                        file_path = os.path.join(addon_data_path, filename)
                        os.remove(file_path)
        
        def get_unix_from_filename(filename):
            try:
                unix_part = filename.split("_")[0]
                unix_timestamp = int(unix_part)
                return unix_timestamp
            except (ValueError, IndexError):
                xbmc.log(f"{base_log_info} | Error converting filename to UNIX timestamp: {filename}", xbmc.LOGERROR)
                return 0
        
        def get_time_from_unix(unix_timestamp):
            return datetime.fromtimestamp(unix_timestamp)
        
        def needs_refresh(file_paths, refresh_time):
            if 'json' not in file_paths or not file_paths['json']:
                return True

            json_modification_time = os.path.getmtime(file_paths['json'])
            file_time = datetime.fromtimestamp(json_modification_time)

            if datetime.now().time() > refresh_time:
                if file_time.date() < datetime.now().date():
                    return True
        
            return False
        
        refresh_time = datetime.strptime("07:35:00", "%H:%M:%S").time()
        
        file_paths = {
            'gz': None,
            'csv': None,
            'json': None
        }
        
        addon = xbmcaddon.Addon('plugin.video.m3_online_database')
        addon_data_path = xbmcvfs.translatePath('special://userdata/addon_data/plugin.video.m3_online_database')
        
        if not os.path.exists(addon_data_path):
            os.makedirs(addon_data_path)
        
        for filename in os.listdir(addon_data_path):
            if filename.endswith(".json"):
                file_paths['json'] = os.path.join(addon_data_path, filename)
            elif filename.endswith(".csv"):
                file_paths['csv'] = os.path.join(addon_data_path, filename)
            elif filename.endswith(".csv.gz"):
                file_paths['gz'] = os.path.join(addon_data_path, filename)
        
        if needs_refresh(file_paths, refresh_time):
            unix_timestamp = int(datetime.timestamp(datetime.now()))
            file_path_gz = os.path.join(addon_data_path, f"{unix_timestamp}_m3-db-daily.csv.gz")
            file_path_csv = os.path.join(addon_data_path, f"{unix_timestamp}_m3-db-daily.csv")
            file_path_json = os.path.join(addon_data_path, f"{unix_timestamp}_m3-db-daily.json")
        
            remove_old_files(addon_data_path, [file_path_gz, file_path_csv, file_path_json])
        
            try:
                urllib.request.urlretrieve(gz_url, file_path_gz)
        
                with gzip.open(file_path_gz, 'rb') as f_in:
                    with open(file_path_csv, 'wb') as f_out:
                        f_out.write(f_in.read())
            except Exception as e:
                xbmc.log(f"{base_log_info} | Failed to download or extract CSV file: {str(e)}", xbmc.LOGERROR)
        
            data_list = []
        
            with open(file_path_csv, 'r', encoding='utf-8') as file:
                csv_reader = csv.reader(file, delimiter=';')
        
                for row in csv_reader:
                    data_dict = {
                        'program_id': row[0],
                        'title': row[1],
                        'subtitle': row[2],
                        'episode': row[3],
                        'episodes': row[4],
                        'seriesId': row[5],
                        'quality': row[6],
                        'year': row[7],
                        'duration': row[8],
                        'short_description': row[9],
                        'released': row[10]
                    }
                    data_list.append(data_dict)
        
            with open(file_path_json, 'w', encoding='utf-8') as json_file:
                json.dump(data_list, json_file, ensure_ascii=False)
        else:
            xbmc.log(f"{base_log_info} | Meglévő json betöltve.", xbmc.LOGINFO)
        
            with open(file_paths['json'], 'r', encoding='utf-8') as json_file:
                data_list = json.load(json_file)
        
        search_word = search_this
        
        results = []
        for data in data_list:
            episode = data.get('episode')
            sec_title = data.get('title')
            series_title = data.get('seriesId')
            episodes = data.get('episodes')
            subtitle = data.get('subtitle')
            short_description = data.get('short_description')
            relesed_date = data.get('released')
            year = data.get('year')
        
            try_image = f'{base_url}/images/m3/{data["program_id"]}'
            
            quality = data.get('quality')
            if quality == 'UHD':
                quality = '4K'
        
            extra_title = ""
            if episode:
                if episode.isdigit():
                    extra_title = f"({episode}/{episodes})"
                else:
                    episode = "0"
            else:
                episode = "0"
        
            new_title_parts = [part for part in [series_title, sec_title, subtitle] if part]
            if sec_title and series_title and sec_title != series_title:
                new_title = " - ".join(new_title_parts)
            elif subtitle:
                new_title = " - ".join([series_title, subtitle])
            else:
                new_title = " - ".join([sec_title])
        
            if (
                search_word.lower() in data.get('program_id', '').lower() or
                search_word.lower() in data.get('title', '').lower() or
                search_word.lower() in data.get('subtitle', '').lower() or
                search_word.lower() in data.get('seriesId', '').lower()
            ):        
        
                results.append({'program_id': data['program_id'],
                                'title': new_title,
                                'extra_title': extra_title,
                                'subtitle': subtitle,
                                'episode': int(episode),
                                'episodes': episodes,
                                'seriesId': series_title,
                                'quality': quality,
                                'year': data.get('year'),
                                'duration': data['duration'],
                                'short_description': short_description,
                                'released': data.get('released'),
                                'image_link': try_image
                                })
        
        sorted_results = sorted(results, key=lambda x: x['released'])
        
        for idx, data in enumerate(sorted_results, start=1):
            if data['extra_title'] != "(0/0)":
                
                picked_info = f'extr_picked&program_id={data["program_id"]}&data_released={data["released"]}&data_title={data["title"]}&data_extra={data["extra_title"]}&data_image_link={data["image_link"]}&year={data["year"]}&duration={data["duration"]}&short_description={data["short_description"]}'
                
                meta_info = {'title': f'{data["title"]} - {data["extra_title"]}', 'plot': f'{data["released"]}\nid: {data["program_id"]}\n{data["year"]}\n{data["short_description"]}'}
                
                self.addDirectoryItem(f'[B]{data["released"]} - {data["title"]} - {data["extra_title"]}[/B]', 
                                      f'{picked_info}', 
                                      f'{data["image_link"]}', 'DefaultMovies.png', isFolder=True, meta=meta_info)

            else:
                
                picked_info = f'extr_picked&program_id={data["program_id"]}&data_released={data["released"]}&data_title={data["title"]}&data_extra={data["extra_title"]}&data_image_link={data["image_link"]}&year={data["year"]}&duration={data["duration"]}&short_description={data["short_description"]}'
                
                meta_info = {'title': f'{data["title"]}', 'plot': f'{data["released"]}\nid: {data["program_id"]}\n{data["year"]}\n{data["short_description"]}'}
                
                self.addDirectoryItem(f'[B]{data["released"]} - {data["title"]}[/B]', 
                                      f'{picked_info}', 
                                      f'{data["image_link"]}', 'DefaultMovies.png', isFolder=True, meta=meta_info)
        
        self.endDirectory('series')



    def ExtrPicked(self, program_id, data_released, data_title, data_extra, data_image_link, year, duration, short_description, url, hasSubtitle):

        import requests
        
        params = {
            'no_lb': '1',
            'target': program_id,
        }
        
        resp_m3u8 = requests.get(f'{base_url}/m3/stream', params=params, cookies=cookies, headers=headers).json()
        m3u8_url = resp_m3u8['url']
        
        import requests
        
        params_info = {
            'id': program_id,
        }
        
        resp_info = requests.get(f'{base_url}/api/m3/v3/item', params=params_info, cookies=cookies, headers=headers).json()
        hasSubtitle = resp_info['hasSubtitle']
        
        import requests
        
        check_m3u8 = requests.get(m3u8_url, headers=headers)
        
        if 'content-length' in check_m3u8.headers:
            content_length = int(check_m3u8.headers['content-length'])
            
            if content_length > 200:
                meta_info = {'title': f'{data_title} - {data_extra}', 'plot': f'id: {program_id}\n{year}\n{short_description}'}
                if '(0/0)' in meta_info['title']:
                    meta_info = {'title': f'{data_title}', 'plot': f'{data_released}\nid: {program_id}\n{year}\n{short_description}'}
                
                    self.addDirectoryItem(
                        f"[B]{data_released} - {data_title}[/B]", 
                        f"play_movie&url={quote_plus(m3u8_url)}&program_id={program_id}&hasSubtitle={hasSubtitle}", data_image_link, "DefaultMovies.png", 
                        isFolder=False, meta=meta_info
                    )
                else:
                    self.addDirectoryItem(
                        f"[B]{data_released} - {data_title} - {data_extra}[/B]", 
                        f"play_movie&url={quote_plus(m3u8_url)}&program_id={program_id}&hasSubtitle={hasSubtitle}", data_image_link, "DefaultMovies.png", 
                        isFolder=False, meta=meta_info
                    )            
            
            else:
                meta_info = {'title': f'{data_title} - {data_extra}', 'plot': f'id: {program_id}\n{year}\n{short_description}'}
                if '(0/0)' in meta_info['title']:
                    meta_info = {'title': f'{data_title}', 'plot': f'{data_released}\nid: {program_id}\n{year}\n{short_description}'}
                
                    self.addDirectoryItem(
                        f"[B][COLOR red]{data_released} - {data_title}[/COLOR][/B]", 
                        f"play_movie&url={quote_plus(m3u8_url)}&program_id={program_id}&hasSubtitle={hasSubtitle}", data_image_link, "DefaultMovies.png", 
                        isFolder=False, meta=meta_info
                    )
                else:
                    self.addDirectoryItem(
                        f"[B][COLOR red]{data_released} - {data_title} - {data_extra}[/COLOR][/B]", 
                        f"play_movie&url={quote_plus(m3u8_url)}&program_id={program_id}&hasSubtitle={hasSubtitle}", data_image_link, "DefaultMovies.png", 
                        isFolder=False, meta=meta_info
                    )
        
        self.endDirectory('series')

    def playMovie(self, url, program_id, hasSubtitle):
        xbmc.log(f'{base_log_info} | playMovie | url | {url}', xbmc.LOGINFO)
        
        try:
            play_item = xbmcgui.ListItem(path=url)

            if hasSubtitle and addon.getSetting('showSubtitle') == 'true':
                subtitle_url = f'https://nemzetiarchivum.hu/subtitle/{program_id}.srt'
                play_item.setSubtitles([subtitle_url])
                xbmc.Player().showSubtitles(True)            
            
            xbmcplugin.setResolvedUrl(syshandle, True, listitem=play_item)
        
        except Exception as e:
            xbmc.log(f'{base_log_info} | playMovie | Error: {e}', xbmc.LOGERROR)
            notification = xbmcgui.Dialog()
            notification.notification("M3 Online (Adatbázis)", f"Törölt tartalom: {e}", time=5000)


    def getSearches(self):
        self.addDirectoryItem('[COLOR lightgreen]Új keresés[/COLOR]', 'newsearch', '', 'DefaultFolder.png')
        try:
            file = open(self.searchFileName, "r")
            olditems = file.read().splitlines()
            file.close()
            items = list(set(olditems))
            items.sort(key=locale.strxfrm)
            if len(items) != len(olditems):
                file = open(self.searchFileName, "w")
                file.write("\n".join(items))
                file.close()
            for item in items:              
                self.addDirectoryItem(item, f'search_database&search_this={item}', '', 'DefaultFolder.png')

            if len(items) > 0:
                self.addDirectoryItem('[COLOR red]Keresési előzmények törlése[/COLOR]', 'deletesearchhistory', '', 'DefaultFolder.png')
        except:
            pass
        self.endDirectory()

    def deleteSearchHistory(self):
        if os.path.exists(self.searchFileName):
            os.remove(self.searchFileName)

    def doSearch(self):
        search_text = self.getSearchText()
        if search_text != '':
            if not os.path.exists(self.base_path):
                os.mkdir(self.base_path)
            file = open(self.searchFileName, "a")
            file.write(f"{search_text}\n")
            file.close()
            search_this = f"{search_text}"
            self.SearchDatabase('', '', '', '', '', '', '', '', search_this)

    def getSearchText(self):
        search_text = ''
        keyb = xbmc.Keyboard('', u'Add meg a keresend\xF5 film c\xEDm\xE9t')
        keyb.doModal()
        if keyb.isConfirmed():
            search_text = keyb.getText()
        return search_text


    def addDirectoryItem(self, name, query, thumb, icon, context=None, queue=False, isAction=True, isFolder=True, Fanart=None, meta=None, banner=None):
        url = f'{sysaddon}?action={query}' if isAction else query
        if thumb == '':
            thumb = icon
        cm = []
        if queue:
            cm.append((queueMenu, f'RunPlugin({sysaddon}?action=queueItem)'))
        if not context is None:
            cm.append((context[0].encode('utf-8'), f'RunPlugin({sysaddon}?action={context[1]})'))
        item = xbmcgui.ListItem(label=name)
        item.addContextMenuItems(cm)
        item.setArt({'icon': thumb, 'thumb': thumb, 'poster': thumb, 'banner': banner})
        if Fanart is None:
            Fanart = addonFanart
        item.setProperty('Fanart_Image', Fanart)
        if not isFolder:
            item.setProperty('IsPlayable', 'true')
        if not meta is None:
            item.setInfo(type='Video', infoLabels=meta)
        xbmcplugin.addDirectoryItem(handle=syshandle, url=url, listitem=item, isFolder=isFolder)

    def endDirectory(self, type='addons'):
        xbmcplugin.setContent(syshandle, type)
        xbmcplugin.endOfDirectory(syshandle, cacheToDisc=True)
