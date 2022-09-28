# -*- coding: utf-8 -*-
###################################################
# 2022-09-28 by Blindspot
###################################################
HOST_VERSION = "3.1"
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, rm, GetTmpDir, MergeDicts
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import dumps as json_dumps
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
###################################################

###################################################
# FOREIGN import
###################################################
import re
import urllib
import random
import os
from Components.config import config, ConfigText, ConfigYesNo, getConfigListEntry
###################################################

###################################################
# E2 GUI COMPONENTS 
###################################################
from Screens.MessageBox import MessageBox
###################################################
def gettytul():
    return 'https://filmezz.club/'

class Filmezz(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'filmezz.club', 'cookie':'filmezzeu.cookie'})
        self.DEFAULT_ICON_URL = 'http://plugins.movian.tv/data/3c3f8bf962820103af9e474604a0c83ca3b470f3'
        self.USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        self.HEADER = {'User-Agent': self.USER_AGENT, 'DNT':'1', 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        self.MAIN_URL = 'https://filmezz.club/'
        self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
    
    def getPage(self, baseUrl, addParams = {}, post_data = None):
        if addParams == {}: addParams = dict(self.defaultParams)
        addParams['cloudflare_params'] = {'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT}
        sts, data = self.cm.getPageCFProtection(baseUrl, addParams, post_data)
        return sts, data
    
    def _uriIsValid(self, url):
        return '://' in url
    
    def listMainMenu(self, cItem):
        MAIN_CAT_TAB = [
                        {'category':'list_items', 'title': _('Filmek'), 'url':'https://filmezz.club/kereses.php?t=1'},
                        {'category':'list_items', 'title': _('Sorozatok'), 'url':'https://filmezz.club/kereses.php?t=2'},
                        {'category':'list_items', 'title': _('Friss'), 'url':'https://filmezz.club/kereses.php?q=0&l=0&e=0&c=0&t=0&h=0&o=feltoltve'},
                        {'category':'list_items', 'title': _('Legnézettebb filmek'), 'url':'https://filmezz.club/kereses.php?q=0&l=0&e=0&c=0&t=1&h=0&o=nezettseg'},
                        {'category':'list_items', 'title': _('Legnézettebb sorozatok'), 'url':'https://filmezz.club/kereses.php?q=0&l=0&e=0&c=0&t=2&h=0&o=nezettseg'},
                        {'category':'list_filters', 'title': _('Kategóriák'), 'url':'https://filmezz.club/'},
                        {'category':'search', 'title': _('Keresés'), 'search_item':True},
                        {'category':'search_history', 'title': _('Keresési előzmények')} 
                          ]
        self.listsTab(MAIN_CAT_TAB, {'name':'category'})
    
    def listFilters(self, cItem):
        printDBG("Filmezz.listFilters")
        sts, data = self.getPage(cItem['url'])
        cat = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="row list', '</ul>', False)[1]
        cats = self.cm.ph.getAllItemsBeetwenMarkers(cat, '<a', '</li>', False)
        for i in cats:
            url = "https://filmezz.club" + self.cm.ph.getDataBeetwenMarkers(i, '<a href="', '"', False)[1]
            title = self.cm.ph.getDataBeetwenMarkers(i, '">', '</a>', False)[1]
            params = {'category':'list_items','title':title, 'icon': None , 'url': url}
            self.addDir(params)
    
    def listItems(self, cItem):
        printDBG("Filmezz.listItems")
        sts, data = self.getPage(cItem['url'])
        film = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="row list-unstyled movie-list">', '<center>', False)[1]
        filmek = self.cm.ph.getAllItemsBeetwenMarkers(film, '<li class="', '</a>', False)
        for i in filmek:
            url = "https://filmezz.club" + self.cm.ph.getDataBeetwenMarkers(i, '<a href="', '"', False)[1]
            title = self.cm.ph.getDataBeetwenMarkers(i, '<span class="title">', '</span>', False)[1]
            icon = self.cm.ph.getDataBeetwenMarkers(i, 'src="', '"', False)[1]
            desc = self.cm.ph.getDataBeetwenMarkers(i, '<ul class="list-unstyled more-info">', '</ul>', False)[1]
            desc = self.cm.ph.getAllItemsBeetwenMarkers(desc, '<span>', '</li>', False)
            kat  = self.cm.ph.getSearchGroups(i, '''Kategória:</span[>]([^"^']+?)[<]''', 1, True)[0].strip()
            
            if len(desc) == 3:
                if "Rendező" in desc[0] or "rendező" in desc[0]:
                    desc = desc[0].replace("</span>", "") + "\n"+ desc[1].replace("</span>", "").strip()+ "\n" + "Kategória: " + kat + "\n" + "IMDb értékelés: " + self.cm.ph.getDataBeetwenMarkers(i, 'IMDb értékelés">', '</span>', False)[1]
                else:
                   desc = "Rendező: " + desc[0].replace("</span>", "") + "\n" +desc[1].replace("</span>", "").strip('		') + "\n" + "Kategória: " + desc[2].replace("</span>", "") + "\n" + "IMDb értékelés: " + self.cm.ph.getDataBeetwenMarkers(i, 'IMDb értékelés">', '</span>', False)[1]
            else:
               if "Rendező" in desc[0] or "rendező" in desc[0]:
                   desc = desc[0].replace("</span>", "") + "\n" + "Kategória: " + desc[1].replace("</span>", "") + "\n" + "IMDb értékelés: " + self.cm.ph.getDataBeetwenMarkers(i, 'IMDb értékelés">', '</span>', False)[1]
               else:
                  desc = "Rendező: " + desc[0].replace("</span>", "") + "\n" + "Kategória: " + desc[1].replace("</span>", "") + "\n" + "IMDb értékelés: " + self.cm.ph.getDataBeetwenMarkers(i, 'IMDb értékelés">', '</span>', False)[1]
            params = {'category':'explore_items','title':title, 'icon': icon , 'url': url, 'desc': desc}
            self.addDir(params)
        if '<ul class="list-inline pagination">' in data:
            next = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="list-inline pagination">', '</ul>')[1]
            next = self.cm.ph.getDataBeetwenMarkers(next, '<li class="active">', '</ul>', False)[1]
            url = "https://filmezz.club" + self.cm.ph.getDataBeetwenMarkers(next, '<li><a href="', '"', False)[1]
            params = {'category':'list_items','title':"Következő oldal", 'icon': None, 'url': url}
            self.addDir(params)
    
    def exploreItems(self, cItem):
        printDBG("Filmezz.exploreItems")
        sts, data = self.getPage(cItem['url'])
        desc  = self.cm.ph.getSearchGroups(data, '''<div class="text"[>]([^"^']+?)[<]''', 1, True)[0].strip()
        url = self.cm.ph.getDataBeetwenMarkers(data, 'Filmmel kapcsolatos linkek', 'Beküldött', False)[1]
        url = self.cm.ph.getDataBeetwenMarkers(url, 'href="', '"', False)[1]
        sts, data = self.getPage(url)
        urls = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="col-sm-4 col-xs-12 host">', '</a>', False)
        icon = self.cm.ph.getDataBeetwenMarkers(data, '" src="', '"', False)[1]
        for i in urls:
            host = self.cm.ph.getDataBeetwenMarkers(i, '</ul>', '<div', False)[1].strip()
            if not host:
               host = "Ismeretlen megosztó"
            title = self.cm.ph.getDataBeetwenMarkers(i, '<div class="col-sm-4 col-xs-12">', '</div>', False)[1].replace("&nbsp;", "")
            if title:
                title = title + ", " + host
            else:
               title = host
            url = self.cm.ph.getDataBeetwenMarkers(i, 'href="', '>', False)[1]
            url = self.cm.ph.getDataBeetwenMarkers(url, 'https://online', '"')[1].strip('"')
            params = {'title':title, 'icon': icon , 'url': url, 'desc': desc}
            self.addVideo(params)
    
    def getLinksForVideo(self, cItem):
        printDBG("Filmezz.getLinksForVideo")
        videoUrls = []
        sts, data = self.cm.getPage(cItem['url'])
        url = self.cm.meta['url']
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
        return videoUrls
    
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG("Filmezz.handleService start")
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        self.currList = []
        if name == None:
            self.listMainMenu( {'name':'category'} )        
        elif category == 'list_filters':
            self.listFilters(self.currItem)
        elif category == 'list_items':
            self.listItems(self.currItem)
        elif category == 'explore_items':
            self.exploreItems(self.currItem)
        elif category == "search":
            cItem = dict(self.currItem)
            cItem.update({'search_item':False, 'name':'category'})
            self.listSearchResult(cItem, searchPattern, searchType)
        elif category == "search_history":
            self.listsHistory({'name':'history', 'category': 'search'}, 'desc', _("Type: "))
        CBaseHostClass.endHandleService(self, index, refresh)
    
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("Filmezz.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        searchPattern = searchPattern.replace(" ", "+")
        url = 'https://filmezz.club/kereses.php?s=' + searchPattern + '&w=0'
        cItem['url'] = url
        self.listItems(cItem) 

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, Filmezz(), True, [])
    