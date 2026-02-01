# -*- coding: utf-8 -*-
###################################################
# 2026-02-01 by WhiteWolf
###################################################
HOST_VERSION = "1.4"
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, GetLogoDir, MergeDicts
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist, getF4MLinksWithMeta, getMPDLinksWithMeta
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.libs import ph
###################################################

###################################################
# FOREIGN import
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, ConfigInteger, getConfigListEntry
import os
import re
import urllib.parse
from random import choice as random_choice
from Tools.Directories import resolveFilename, fileExists, SCOPE_PLUGINS
import requests
###################################################
# E2 GUI COMPONENTS
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvmultipleinputbox import IPTVMultipleInputBox
from Screens.MessageBox import MessageBox
###################################################
###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.videa_quality = ConfigYesNo(default = True)
###################################################
def GetConfigList():
    optionList = []
    optionList.append( getConfigListEntry(_("Elérhető legjobb minőség beállítása"), config.plugins.iptvplayer.videa_quality) )
    return optionList

def gettytul():
    return 'Videa'

class Videa(CBaseHostClass):

    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'videa', 'cookie':'videa.cookie'})
        self.USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36'
        self.HEADER = self.cm.getDefaultHeader()
        self.DEFAULT_ICON_URL = 'http://www.figyelmeztetes.hu/videa_logo.jpg'
        self.MAIN_URL = 'https://videa.hu'
        self.defaultParams = {'header':self.HEADER, 'use_cookie': False, 'load_cookie': False, 'save_cookie': False, 'cookiefile': self.COOKIE_FILE}
        
    def _uriIsValid(self, url):
        return '://' in url
        
    def getPage(self, baseUrl, addParams = {}, post_data = None):
        if addParams == {}:
            addParams = dict(self.defaultParams)
        
        def _getFullUrl(url):
            if self.cm.isValidUrl(url):
                return url
            else:
                return urllib.parse.urljoin(baseUrl, url)
            
        addParams['cloudflare_params'] = {'domain':self.up.getDomain(baseUrl), 'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT, 'full_url_handle':_getFullUrl}
        sts, data = self.cm.getPageCFProtection(baseUrl, addParams, post_data)
        return sts, data
        
    def listMainMenu(self, cItem):
        MAIN_CAT_TAB = [{'category':'list_filters', 'title': 'Kategóriák', 'desc':'Videa kategóriáinak megjelenítése'},
                            {'category':'list_filters', 'title': 'Csatornák', 'desc':'Videa csatornáinak megjelenítése'},
                            {'category':'search', 'title': _('Search'), 'search_item':True, 'desc':'Keresés'},
                            {'category':'search_history', 'title': _('Search history'), 'desc':'Keresés az előzmények között'} 
                       ]
        self.listsTab(MAIN_CAT_TAB, {'name':'category'})
    
    def listItems(self, cItem):
        printDBG('Videa.listItems')
        sts, data = self.getPage(cItem['url'])
        page = self.cm.ph.getDataBeetwenMarkers(data, '<li class="active">', 'következő', False)[1]
        page = self.cm.ph.getAllItemsBeetwenMarkers(page, '<a href="', '"', False)
        vids = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="panel panel-video">', '<div class="panel-footer">', False)
        for i in vids:
            url = self.cm.ph.getDataBeetwenMarkers(i, 'title"><a href="', '"', False)[1]
            title = self.cm.ph.getDataBeetwenMarkers(i, '" title="', '"', False)[1]
            replacemap = {'&':'&amp;', '\"':'&quot;', "'":"&#039;"}
            for key in replacemap:
                title = title.replace(replacemap[key], key)
            icon = self.cm.ph.getDataBeetwenMarkers(i, '" src="', '"', False)[1]
            desc = "Videó hossza: " + self.cm.ph.getDataBeetwenMarkers(i, 'video-length">', '</span>', False)[1]
            params = {'title': title, 'icon': icon, 'url': url, 'desc': desc}
            self.addVideo(params)
        try:
           if not page[0] == page[1]:
               title = "Következő oldal"
               params = {'category': 'list_items', 'title': title, 'icon': None, 'url': cItem['url'][:-1]+str(int(cItem['url'][-1])+1)}
               self.addDir(params)
        except:
           pass
    
    def listFilters(self, cItem):
        printDBG('Videa.listFilters')
        sts, data = self.getPage(self.MAIN_URL)
        if cItem['title'] == "Kategóriák":
            cat = self.cm.ph.getDataBeetwenMarkers(data, '>kategóriák', '</ul>', False)[1]
        else:
            cat = self.cm.ph.getDataBeetwenMarkers(data, '>csatornák', '</ul>', False)[1]
        cats = self.cm.ph.getAllItemsBeetwenMarkers(cat, '<li>', '</li>', False)
        for i in cats:
            url = self.MAIN_URL + self.cm.ph.getDataBeetwenMarkers(i, 'href="', '"', False)[1] + "?sort=0&category=0&page=1"
            title = self.cm.ph.getDataBeetwenMarkers(i, '">', '</a>', False)[1].upper()
            params = {'category': 'list_sort', 'title': title, 'icon': None, 'url': url}
            self.addDir(params)
    
    def sorting(self, cItem):
        title = "Feltöltés ideje szerint"
        title2 = "Nézettség szerint"
        url = cItem['url']
        chars = []
        for i in url:
            chars.append(i)
        chars[-19] = "1"
        url = "".join(chars)
        params2 = {'category': 'list_items', 'title': title2, 'icon': None, 'url': url}
        params = {'category': 'list_items', 'title': title, 'icon': None, 'url': cItem['url']}
        dirs = [params, params2]
        printDBG(dirs)
        for i in dirs:
            self.addDir(i)
    
    def getLinksForVideo(self, cItem):
        videoUrls = []
        url = cItem['url']
        baseUrl = strwithmeta(url)
        sts, data = self.cm.getPage(baseUrl)
        url = self.cm.ph.getDataBeetwenMarkers(data, '"embedURL": "', '"', False)[1]
        url = url.replace("/v/", "?v=").replace("?autoplay=1", "&autoplay=0")
        uri = urlparser.decorateParamsFromUrl(url)
        protocol = uri.meta.get('iptv_proto', '')
        
        printDBG("PROTOCOL [%s] " % protocol)
        
        urlSupport = self.up.checkHostSupport( uri )
        if 1 == urlSupport:
            retTab = self.up.getVideoLinkExt( uri )
            videoUrls.extend(retTab)
        elif 0 == urlSupport and self._uriIsValid(uri):
            if protocol == 'm3u8':
                retTab = getDirectM3U8Playlist(uri, checkExt=False, checkContent=True)
                videoUrls.extend(retTab)
            elif protocol == 'f4m':
                retTab = getF4MLinksWithMeta(uri)
                videoUrls.extend(retTab)
            elif protocol == 'mpd':
                retTab = getMPDLinksWithMeta(uri, False)
                videoUrls.extend(retTab)
            else:
                videoUrls.append({'name':'direct link', 'url':uri})
        use_best = config.plugins.iptvplayer.videa_quality.value
        printDBG("Legjobb minőség használata: "+str(use_best))
        if config.plugins.iptvplayer.videa_quality.value:
            return [videoUrls[-1]]
        else:
            return videoUrls
    
    def listSearchResult(self, cItem, searchPattern, searchType):
        cItem['url'] = "https://videa.hu/video_kereses/" + urllib.parse.quote_plus(searchPattern) + "?sort=0&category=0&page=1"
        self.listItems(cItem)
    
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        name = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        self.currList = []
        if name == None:
            self.listMainMenu( {'name':'category'} )
        elif category == 'list_filters':
            self.listFilters(self.currItem)
        elif category == 'list_items':
            self.listItems(self.currItem)
        elif category == 'list_sort':
            self.sorting(self.currItem)
        elif category == 'search':
            cItem = dict(self.currItem)
            cItem.update({'search_item': False, 'name': 'category'})
            self.listSearchResult(cItem, searchPattern, searchType)
        elif category == 'search_history':
            self.listsHistory({'name':'history', 'category': 'search'}, 'desc', _("Type: "))
        else:
            return
        CBaseHostClass.endHandleService(self, index, refresh)
    
class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, Videa(), True, [])
    