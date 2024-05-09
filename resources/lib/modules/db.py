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
import sqlite3, os, requests, csv, gzip, xbmc, xbmcvfs, xbmcaddon, xbmcgui, time

version = xbmcaddon.Addon().getAddonInfo('version')
kodi_version = xbmc.getInfoLabel('System.BuildVersion')
base_log_info = f'M3 Online (Adatbázis) | v{version} | Kodi: {kodi_version[:5]}'

db_file = os.path.join(xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('profile')), "m3online.db")
gz_url = "https://m3.devs.space/public/m3-db.csv.gz"
con = None
cur = None

def open_db():
    con = sqlite3.connect(db_file)
    cur = con.cursor()
    return con, cur

def close_db(con, cur):
    cur.close()
    con.close()

def refresh_database(checkInSeconds):
    con, cur = open_db()
    cur.execute("CREATE TABLE IF NOT EXISTS METADATA(MEDIA_COUNT INTEGER, LAST_UPDATE TEXT, LAST_UPDATE_TIME INTEGER)")
    cur.execute("CREATE TABLE IF NOT EXISTS MEDIA(ROWNR INTEGER, PROGRAM_ID TEXT, TITLE TEXT, SUBTITLE TEXT, EPISODE TEXT, EPISODES TEXT, SERIESID TEXT, QUALITY TEXT, YEAR TEXT, DURATION TEXT, SHORT_DESCRIPTION TEXT, RELEASED TEXT, PRIMARY KEY(ROWNR))")
    """
    cur.execute("CREATE INDEX IF NOT EXISTS IDX_PROGRAM_ID ON MEDIA(LOWER(PROGRAM_ID))")
    cur.execute("CREATE INDEX IF NOT EXISTS IDX_TITLE ON MEDIA(LOWER(TITLE))")
    cur.execute("CREATE INDEX IF NOT EXISTS IDX_SUBTITLE ON MEDIA(LOWER(SUBTITLE))")
    cur.execute("CREATE INDEX IF NOT EXISTS IDX_SERIESID ON MEDIA(LOWER(SERIESID))")
    """
    cur.execute("CREATE INDEX IF NOT EXISTS IDX_PROGRAM_ID ON MEDIA(PROGRAM_ID)")
    cur.execute("CREATE INDEX IF NOT EXISTS IDX_TITLE ON MEDIA(TITLE)")
    cur.execute("CREATE INDEX IF NOT EXISTS IDX_SUBTITLE ON MEDIA(SUBTITLE)")
    cur.execute("CREATE INDEX IF NOT EXISTS IDX_SERIESID ON MEDIA(SERIESID)")

    res = cur.execute("SELECT LAST_UPDATE, LAST_UPDATE_TIME FROM METADATA")
    lastUpdate = res.fetchone()
    lastUpdateTime = None
    if lastUpdate:
        lastUpdateTime = lastUpdate[1]
        lastUpdate = lastUpdate[0]
    if lastUpdate == None or lastUpdateTime+checkInSeconds<int(time.time()):
        xbmc.log(f"{base_log_info} | Elapsed more than {checkInSeconds} seconds (now is {int(time.time())}) since last update check ({lastUpdateTime}), checking for update.", xbmc.LOGINFO)
        r = requests.head(gz_url)
        if r.ok:
            if r.headers["last-modified"] != lastUpdate:
                progressDialog = xbmcgui.DialogProgress()
                progressDialog.create("M3 online (Adatbázis)", "Tömörített állomány letöltése")
                xbmc.log(f"{base_log_info} | Database header last modified changed from {lastUpdate} to {r.headers['last-modified']}, updating the database.", xbmc.LOGINFO)
                lastUpdate = r.headers["last-modified"]
                r = requests.get(gz_url)
                if r.ok:
                    rows = None
                    csvText = None
                    csvList = None
                    rows = None
                    progressDialog.update(25, "Tömörített állomány kicsomagolása")
                    try:
                        csvText = gzip.decompress(r.content)
                    except:
                        xbmc.log(f"{base_log_info} | Error on decompressing downloaded gzip data", xbmc.LOGERROR)
                        close_db(con, cur)
                        progressDialog.close()
                        xbmcgui.Dialog.ok("M3 online (Adatbázis)", "Hiba a tömörített állomány kicsomaglásakor!")
                        return
                    progressDialog.update(50, "Kicsomagolt CSV elemzése")
                    try:
                        csvList = csvText.decode("utf-8").splitlines()
                        reader = csv.reader(csvList, delimiter = ";")
                        rows = list(reader)
                    except:
                        xbmc.log(f"{base_log_info} | Error on parsing csv data", xbmc.LOGERROR)
                        close_db(con, cur)
                        progressDialog.close()
                        xbmcgui.Dialog.ok("M3 online (Adatbázis)", "Hiba a CSV állomány elemzésekor!")
                        return
                    progressDialog.update(75, "CSV betöltése a helyi adatbázisba")
                    cur.execute("DELETE FROM MEDIA")
                    cur.execute("DELETE FROM METADATA")
                    con.commit()
                    cur.execute("VACUUM")
                    for idx in range(1, len(rows)):
                        cur.execute("INSERT INTO MEDIA(ROWNR, PROGRAM_ID, TITLE, SUBTITLE, EPISODE, EPISODES, SERIESID, QUALITY, YEAR, DURATION, SHORT_DESCRIPTION, RELEASED) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (idx, rows[idx][0], rows[idx][1], rows[idx][2], rows[idx][3], rows[idx][4], rows[idx][5], rows[idx][6], rows[idx][7], rows[idx][8], rows[idx][9], rows[idx][10]))
                    cur.execute(f"INSERT INTO METADATA(MEDIA_COUNT, LAST_UPDATE, LAST_UPDATE_TIME) VALUES({len(rows)-1}, '{lastUpdate}', {int(time.time())})")
                    con.commit()
                else:
                    xbmc.log(f"{base_log_info} | Database header download resulting: {r.status_code}, keep original data", xbmc.LOGERROR)
                    xbmcgui.Dialog.ok("M3 online (Adatbázis)", "Hiba a tömörített állomány letöltésekor!")
                progressDialog.close()
            else:
                xbmc.log(f"{base_log_info} | Database header last modified not changed: {lastUpdate}", xbmc.LOGINFO)
                cur.execute(f"UPDATE METADATA SET LAST_UPDATE_TIME={int(time.time())}")
                con.commit()
        else:
            xbmc.log(f"{base_log_info} | Database header download resulting: {r.status_code}", xbmc.LOGERROR)
    else:
        xbmc.log(f"{base_log_info} | Elapsed less than {checkInSeconds} seconds (now is {int(time.time())}) since last update check ({lastUpdateTime}), no need checking for update.", xbmc.LOGERROR)
    close_db(con, cur)

def get_results(page, pagesize, search):
    con, cur = open_db()
    cnt = None
    result = None
    extraFilter = ""
    if search:
        #extraFilter = f" WHERE (LOWER(PROGRAM_ID) LIKE LOWER('{'%'+search+'%'}') OR LOWER(TITLE) LIKE LOWER('{'%'+search+'%'}') OR LOWER(SUBTITLE) LIKE LOWER('{'%'+search+'%'}') OR LOWER(SERIESID) LIKE LOWER('{'%'+search+'%'}'))"
        extraFilter = f" WHERE (PROGRAM_ID LIKE '{'%'+search+'%'}' OR TITLE LIKE '{'%'+search+'%'}' OR SUBTITLE LIKE '{'%'+search+'%'}' OR SERIESID LIKE '{'%'+search+'%'}')"
    sql = "SELECT COUNT(*) FROM MEDIA " + extraFilter
    res = cur.execute(sql)
    cnt = res.fetchone()[0]
    sql = "SELECT PROGRAM_ID, TITLE, SUBTITLE, EPISODE, EPISODES, SERIESID, QUALITY, YEAR, DURATION, SHORT_DESCRIPTION, RELEASED FROM (SELECT ROW_NUMBER() OVER (ORDER BY ROWNR) RNR, PROGRAM_ID, TITLE, SUBTITLE, EPISODE, EPISODES, SERIESID, QUALITY, YEAR, DURATION, SHORT_DESCRIPTION, RELEASED FROM MEDIA" + extraFilter + ") WHERE RNR BETWEEN ? AND ?"
    res = cur.execute(sql, (page * pagesize + 1, (page + 1) * pagesize))
    result = res.fetchall()
    close_db(con, cur)
    return cnt, result

def clear_database():
    con, cur = open_db()
    cur.execute("DROP TABLE IF EXISTS METADATA")
    cur.execute("DROP TABLE IF EXISTS MEDIA")
    cur.execute("VACUUM")
    con.commit()
    close_db(con, cur)