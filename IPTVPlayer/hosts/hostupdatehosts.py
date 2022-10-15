# -*- coding: utf-8 -*-
###################################################
# 2022-10-15 - UPDATEHOSTS - Blindspot
###################################################
HOST_VERSION = "4.6"
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, GetLogoDir, rm, rmtree, mkdirs, DownloadFile, GetFileSize, GetConfigDir, Which, MergeDicts
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist, getF4MLinksWithMeta, getMPDLinksWithMeta
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads, dumps as json_dumps
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config, ConfigText, ConfigYesNo, ConfigDirectory, getConfigListEntry
from os.path import normpath
import os
import re
import random
import codecs
try:
    import subprocess
    FOUND_SUB = True
except Exception:
    FOUND_SUB = False
from Tools.Directories import resolveFilename, fileExists, SCOPE_PLUGINS
from Screens.MessageBox import MessageBox
###################################################
###################################################

def gettytul():
    return 'updatehosts HU'

class UPDATEHOSTS(CBaseHostClass):

    def __init__(self):
        printDBG("Updatehosts.__init__")
        CBaseHostClass.__init__(self, {'history':'updatehosts', 'cookie':'updatehosts.cookie'})
        self.USER_AGENT = 'User-Agent=Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
        self.HEADER = self.cm.getDefaultHeader()
        self.versionpath = normpath("/usr/lib/enigma2/python/Plugins/Extensions/IPTVPlayer/version.py")
        self.hostspath = normpath("/usr/lib/enigma2/python/Plugins/Extensions/IPTVPlayer/hosts/")
        self.defaultParams = {'header':self.HEADER, 'use_cookie': False, 'load_cookie': False, 'save_cookie': False, 'cookiefile': self.COOKIE_FILE}
    
    def check(self):
        sts, data = self.cm.getPage('https://github.com/Blindspot76/e2iPlayer-Python3/blob/master/IPTVPlayer/version.py', self.defaultParams)
        version = self.cm.ph.getDataBeetwenMarkers(data, 'IPTV_VERSION', '</td>', False)[1]
        version = self.cm.ph.getDataBeetwenMarkers(version, '&quot;', '&quot;', False)[1]
        printDBG(version)
        local = self.getversion()
        if version != local:
            self._update()
            data = open(self.versionpath, 'w')
            text = "# -*- coding: utf-8 -*-\n#YYYY.MM.DD.DAY_RELEASE\n" + 'IPTV_VERSION="' + version + '"'
            data.write(text)
            data.close()
            rm(self.versionpath+"c")
        else:
           msg = 'Nem szükséges frissítés.'
           ret = self.sessionEx.waitForFinishOpen(MessageBox, msg, type=MessageBox.INFO, timeout = 10 )
    
    def getversion(self):
        data = open(self.versionpath, 'r')
        version = data.read()
        version = self.cm.ph.getDataBeetwenMarkers(version, 'IPTV_VERSION="', '"', False)[1]
        printDBG(version)
        data.close()
        return version
    
    def getupdate(self, url):
        sts, data = self.cm.getPage(url, self.defaultParams)
        items = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a class="js-navigation-open Link--primary"', '</span>', False)
        to_update = []
        num = 0
        while num != len(items):
           title = self.cm.ph.getDataBeetwenMarkers(items[num], '">', '</a>', False)[1]
           to_update.append(title)
           num = num+1
        return to_update
     
    def _update(self):
        msg = 'Frissítés szükséges. Egy kis időbe fog telni. (Nyomj igen-t, ha szeretnéd folytatni.)'
        ret = self.sessionEx.waitForFinishOpen(MessageBox, msg, type=MessageBox.TYPE_YESNO, default=True)
        if ret[0]:
            pass
        else:
           return
        url = 'https://github.com/Blindspot76/e2iPlayer-Python3/tree/master/IPTVPlayer/hosts/'
        need = self.getupdate(url)
        url = 'https://raw.githubusercontent.com/Blindspot76/e2iPlayer-Python3/master/IPTVPlayer/hosts/'
        for i in need:
            fname = i
            destination = "/tmp/" + fname
            if self.download(url+fname, destination):
                if self._copy(destination, self.hostspath + "/" + fname):
                    pass
                else:
                   msg = 'A frissítés sikertelen! (Másolási hiba)'
                   self.sessionEx.open(MessageBox, msg, type = MessageBox.TYPE_ERROR, timeout = 20 )
                   return
            else:
               msg = 'A frissítés sikertelen! (Letöltési hiba, próbáld újra.)'
               self.sessionEx.open(MessageBox, msg, type = MessageBox.TYPE_ERROR, timeout = 20 )
               return
            if fileExists(destination):
                rm(destination)
            if fileExists(self.hostspath+fname+"c"):
                rm(self.hostspath+fname+"c")
            if fileExists(self.hostspath+fname+"o"):
                rm(self.hostspath+fname+"o")
        msg = 'A frissítés sikeres! Indítsd újra a készüléket!'
        self.sessionEx.open(MessageBox, msg, type = MessageBox.TYPE_INFO, timeout = 20 )  
    
    def download(self, url, destination, tries=2, delay=3):
        vissza = False
        try:
            for i in range(tries):
                tmp = DownloadFile(url,destination)
                if tmp:
                    vissza = True
                    break
                else:
                    sleep(delay)
        except Exception:
            return False
        return vissza
    
    def _mycall(self, cmd):
        command = cmd
        back_state = -1
        try:
            back_state = subprocess.call(command)
        except Exception:
            return -1
        return back_state
    
    def _copy(self, filename, dest_dir):
        sikerult = False
        try:
           copy_command = 'cp -rf ' + filename + ' ' + dest_dir
           if subprocess.call(copy_command, shell=True) == 0:
               sikerult = True
        except Exception:
            return False
        return sikerult
    
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        try:
            CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
            name     = self.currItem.get("name", '')
            category = self.currItem.get("category", '')
            self.currList = []
            if name == None:
                self.check()
            else:
                printExc()
            CBaseHostClass.endHandleService(self, index, refresh)
        except Exception:
            return

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, UPDATEHOSTS(), True, [])
    
