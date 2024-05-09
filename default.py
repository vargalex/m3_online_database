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
import sys
from resources.lib.indexers import navigator

if sys.version_info[0] == 3:
    from urllib.parse import parse_qsl
else:
    from urlparse import parse_qsl

params = dict(parse_qsl(sys.argv[2].replace('?', '')))

action = params.get('action')
url = params.get('url')
page = 0 if not params.get('page') else int(params.get('page'))

program_id = params.get('program_id')
data_released = params.get('data_released')
data_quality = params.get('data_quality')
data_title = params.get('data_title')
data_extra = params.get('data_extra')
data_image_link = params.get('data_image_link')
year = params.get('year')
duration = params.get('duration')
short_description = params.get('short_description')

search = params.get('search')

hasSubtitle = params.get('hasSubtitle')


if action is None:
    navigator.navigator().root()

elif action == 'getitems':
    navigator.navigator().getItems(page, search)

elif action == 'extr_picked':
    navigator.navigator().ExtrPicked(program_id, data_released, data_title, data_extra, data_image_link, year, duration, short_description, url, hasSubtitle)

elif action == 'play_movie':
    navigator.navigator().playMovie(url, program_id, hasSubtitle)

elif action == 'search':
    navigator.navigator().getSearches()

elif action == 'newsearch':
    navigator.navigator().doSearch()

elif action == 'deletesearchhistory':
    navigator.navigator().deleteSearchHistory()

elif action == 'cleardatabase':
    navigator.navigator().clear_database()