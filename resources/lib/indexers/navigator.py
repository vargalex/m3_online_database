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

import os, sys, re, xbmc, xbmcgui, xbmcplugin, xbmcaddon, xbmcvfs, locale
import requests
import resources.lib.modules.db as db

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

db_data_mapping = {
    'program_id': 0,
    'title': 1,
    'subtitle': 2,
    'episode': 3,
    'episodes': 4,
    'seriesId': 5,
    'quality': 6,
    'year': 7,
    'duration': 8,
    'short_description': 9,
    'released': 10
}

class navigator:
    def __init__(self):
        try:
            locale.setlocale(locale.LC_ALL, "hu_HU.UTF-8")
        except:
            try:
                locale.setlocale(locale.LC_ALL, "")
            except:
                pass
        self.base_path = translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
        self.searchFileName = os.path.join(self.base_path, "search.history")
        self.pageSize = int(addon.getSetting("pageSize"))
        if not os.path.exists(self.base_path):
            os.mkdir(self.base_path)
        db.refresh_database(int(addon.getSetting("checkDatabase"))*60*60)

    def root(self):
        self.addDirectoryItem("M3 Online (Adatbázis)", f"getitems&page=0", '', 'DefaultFolder.png')
        self.addDirectoryItem("Keresés", f"search", '', 'DefaultFolder.png')
        self.endDirectory()

    def getItems(self, page, search):
        cnt, results = db.get_results(page, self.pageSize, search)
        for data in results:
            program_id = data[db_data_mapping['program_id']]
            episode = data[db_data_mapping['episode']]
            sec_title = data[db_data_mapping['title']]
            series_title = data[db_data_mapping['seriesId']]
            episodes = data[db_data_mapping['episodes']]
            subtitle = data[db_data_mapping['subtitle']]
            short_description = data[db_data_mapping['short_description']]
            released_date = data[db_data_mapping['released']]
            year = data[db_data_mapping['year']]
            duration = data[db_data_mapping['duration']]

            try_image = f'{base_url}/images/m3/{data[db_data_mapping["program_id"]]}'
            
            quality = data[db_data_mapping['quality']]
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
        
            if extra_title != "(0/0)":
                
                picked_info = f'extr_picked&program_id={program_id}&data_released={released_date}&data_title={new_title}&data_extra={extra_title}&data_image_link={try_image}&year={year}&duration={duration}&short_description={short_description}'
                
                meta_info = {'title': f'{new_title} - {extra_title}', 'plot': f'{released_date}\nid: {program_id}\n{year}\n{short_description}'}
                
                self.addDirectoryItem(f'[B]{released_date} - {new_title} - {extra_title}[/B]', 
                                      f'{picked_info}', 
                                      f'{try_image}', 'DefaultMovies.png', isFolder=True, meta=meta_info)

            else:
                
                picked_info = f'extr_picked&program_id={program_id}&data_released={released_date}&data_title={new_title}&data_extra={extra_title}&data_image_link={try_image}&year={year}&duration={duration}&short_description={short_description}'
                
                meta_info = {'title': f'{new_title}', 'plot': f'{released_date}\nid: {program_id}\n{year}\n{short_description}'}
                
                self.addDirectoryItem(f'[B]{released_date} - {new_title}[/B]', 
                                      f'{picked_info}', 
                                      f'{try_image}', 'DefaultMovies.png', isFolder=True, meta=meta_info)
        if (page + 1) * (self.pageSize) < cnt:
            self.addDirectoryItem(f"[I]Következő oldal ({page + 2} / {-(-1*cnt // self.pageSize)}) >>>[/I]", f"getitems&page={page + 1}&search={search if search else ''}", '', 'DefaultMovies.png', isFolder=True)
        self.endDirectory('series')

    def ExtrPicked(self, program_id, data_released, data_title, data_extra, data_image_link, year, duration, short_description, url, hasSubtitle):

        params = {
            'no_lb': '1',
            'target': program_id,
        }
        
        resp_m3u8 = requests.get(f'{base_url}/m3/stream', params=params, cookies=cookies, headers=headers).json()
        m3u8_url = resp_m3u8['url']
        
        params_info = {
            'id': program_id,
        }
        
        resp_info = requests.get(f'{base_url}/api/m3/v3/item', params=params_info, cookies=cookies, headers=headers).json()
        hasSubtitle = resp_info['hasSubtitle']
        
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
                self.addDirectoryItem(item, f'getitems&page=0&search={item}', '', 'DefaultFolder.png')

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
            self.getItems(0, search_this)

    def getSearchText(self):
        search_text = ''
        keyb = xbmc.Keyboard('', u'Add meg a keresend\xF5 film c\xEDm\xE9t')
        keyb.doModal()
        if keyb.isConfirmed():
            search_text = keyb.getText()
        return search_text

    def clear_database(self):
        if xbmcgui.Dialog().yesno("M3 online (Adatbázis)", "Biztosan törli a helyi adatbázist?"):
            db.clear_database()
            xbmcgui.Dialog().notification("M3 online (Adatbázis)", "Adatbázis törlése sikeres")
        return


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
