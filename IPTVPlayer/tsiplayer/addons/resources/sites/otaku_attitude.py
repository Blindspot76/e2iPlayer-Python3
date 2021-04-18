# -*- coding: utf-8 -*-
# vStream https://github.com/Kodi-vStream/venom-xbmc-addons
# Makoto

import re

from Plugins.Extensions.IPTVPlayer.tsiplayer.addons.resources.lib.gui.hoster import cHosterGui
from Plugins.Extensions.IPTVPlayer.tsiplayer.addons.resources.lib.gui.gui import cGui
from Plugins.Extensions.IPTVPlayer.tsiplayer.addons.resources.lib.handler.inputParameterHandler import cInputParameterHandler
from Plugins.Extensions.IPTVPlayer.tsiplayer.addons.resources.lib.handler.outputParameterHandler import cOutputParameterHandler
from Plugins.Extensions.IPTVPlayer.tsiplayer.addons.resources.lib.handler.requestHandler import cRequestHandler
from Plugins.Extensions.IPTVPlayer.tsiplayer.addons.resources.lib.parser import cParser
from Plugins.Extensions.IPTVPlayer.tsiplayer.addons.resources.lib.comaddon import progress
from Plugins.Extensions.IPTVPlayer.tsiplayer.addons.resources.lib.util import cUtil


SITE_IDENTIFIER = 'otaku_attitude'
SITE_NAME = 'Otaku-Attitude'
SITE_DESC = 'Animes, Drama et OST en DDL et Streaming'

URL_MAIN = 'https://www.otaku-attitude.net/'
OST_MAIN = 'https://forum.otaku-attitude.net/musicbox/playlists/'

URL_SEARCH_ANIMS = (URL_MAIN + 'recherche.html?cat=1&q=', 'showAnimes')
URL_SEARCH_DRAMAS = (URL_MAIN + 'recherche.html?cat=2&q=', 'showAnimes')
FUNCTION_SEARCH = 'showAnimes'

ANIM_ANIMS = ('http://', 'load')
ANIM_VOSTFRS = (URL_MAIN + 'liste-dl-animes.php', 'showAnimes')

DRAMA_SERIES = (URL_MAIN + 'liste-dl-dramas.php', 'showAnimes')

OST_ANIME = (True, 'showGenres')


def load():
    oGui = cGui()

    oOutputParameterHandler = cOutputParameterHandler()
    oOutputParameterHandler.addParameter('siteUrl', URL_SEARCH_ANIMS[0])
    oGui.addDir(SITE_IDENTIFIER, 'showSearch', 'Recherche (Animés)', 'search.png', oOutputParameterHandler)

    oOutputParameterHandler.addParameter('siteUrl', URL_SEARCH_DRAMAS[0])
    oGui.addDir(SITE_IDENTIFIER, 'showSearch', 'Recherche (Dramas)', 'search.png', oOutputParameterHandler)

    oOutputParameterHandler.addParameter('siteUrl', ANIM_VOSTFRS[0])
    oGui.addDir(SITE_IDENTIFIER, ANIM_VOSTFRS[1], 'Animés (VOSTFR)', 'animes.png', oOutputParameterHandler)

    oOutputParameterHandler.addParameter('siteUrl', DRAMA_SERIES[0])
    oGui.addDir(SITE_IDENTIFIER, DRAMA_SERIES[1], 'Dramas (VOSTFR)', 'dramas.png', oOutputParameterHandler)

    oOutputParameterHandler.addParameter('siteUrl', OST_ANIME[0])
    oGui.addDir(SITE_IDENTIFIER, OST_ANIME[1], 'Musicbox (OST)', 'music.png',  oOutputParameterHandler)

    oGui.setEndOfDirectory()


def showGenres():
    oGui = cGui()

    liste = []
    liste.append(['Animés', OST_MAIN + '1-anime/'])
    liste.append(['Dramas', OST_MAIN + '6-drama/'])
    liste.append(['Jeux Vidéo', OST_MAIN + '7-jeu-vidéo/'])

    oOutputParameterHandler = cOutputParameterHandler()
    for sTitle, sUrl in liste:
        oOutputParameterHandler.addParameter('siteUrl', sUrl)
        oGui.addDir(SITE_IDENTIFIER, 'showOst', sTitle, 'music.png', oOutputParameterHandler)

    oGui.setEndOfDirectory()


def showSearch():
    oGui = cGui()
    oInputParameterHandler = cInputParameterHandler()
    sUrl = oInputParameterHandler.getValue('siteUrl')

    sSearchText = oGui.showKeyBoard()
    if (sSearchText != False):
        sUrl = sUrl + sSearchText.replace(' ', '+')
        showAnimes(sUrl)
        oGui.setEndOfDirectory()
        return


def showAnimes(sSearch=''):
    oGui = cGui()
    oInputParameterHandler = cInputParameterHandler()
    sUrl = oInputParameterHandler.getValue('siteUrl')
    if sSearch:
        sUrl = sSearch

    # On memorise le lien de base ce qui permet d'avoir un nextpage fonctionnel sans modif et peut importe la categorie
    if not sSearch:
        if 'scroll' not in sUrl:
            memorisedUrl = sUrl
            Page = 1
        else:
            memorisedUrl = oInputParameterHandler.getValue('memorisedUrl')
            Page = oInputParameterHandler.getValue('Page')

    oRequestHandler = cRequestHandler(sUrl)
    sHtmlContent = oRequestHandler.request()

    oParser = cParser()
    if sSearch:
        sPattern = 'href="([^"]+)" class="liste_dl"><img src="([^"]+)".+?alt=".+?strong>([^<]+)<.+?all">([^<]+)</.+?>'
    else:
        sPattern = 'href="([^"]+)".+?><img src="([^"]+)".+?alt=".+?strong>([^<]+)<.+?all">([^<]+)<br.+?>'

    aResult = oParser.parse(sHtmlContent, sPattern)

    if (aResult[0] == False):
        oGui.addText(SITE_IDENTIFIER)

    if (aResult[0] == True):
        total = len(aResult[1])
        progress_ = progress().VScreate(SITE_NAME)
        oOutputParameterHandler = cOutputParameterHandler()
        for aEntry in aResult[1]:
            progress_.VSupdate(progress_, total)
            if progress_.iscanceled():
                break

            sUrl2 = URL_MAIN + aEntry[0]
            sThumb = aEntry[1]
            sTitle = aEntry[2].replace('-...', '').replace('...', '').replace('!', ' !')
            sDesc = aEntry[3]

            # filtre search
            if sSearch and total > 5:
                if cUtil().CheckOccurence(sSearch, sTitle) == 0:
                    continue

            oOutputParameterHandler.addParameter('siteUrl', sUrl2)
            oOutputParameterHandler.addParameter('sMovieTitle', sTitle)
            oOutputParameterHandler.addParameter('sThumb', sThumb)
            oOutputParameterHandler.addParameter('sDesc', sDesc)
            oGui.addAnime(SITE_IDENTIFIER, 'showEpisodes', sTitle, '', sThumb, sDesc, oOutputParameterHandler)

        progress_.VSclose(progress_)

    if not sSearch:
        Page = int(Page) + 1
        oOutputParameterHandler = cOutputParameterHandler()
        oOutputParameterHandler.addParameter('siteUrl', memorisedUrl + '?&scroll=' + str(Page))
        # On renvoi l'url memoriser et le numero de page pour l'incrementer a chaque fois
        oOutputParameterHandler.addParameter('memorisedUrl', memorisedUrl)
        oOutputParameterHandler.addParameter('Page', Page)
        oGui.addNext(SITE_IDENTIFIER, 'showAnimes', 'Page ' + str(Page), oOutputParameterHandler)

        oGui.setEndOfDirectory()


def showOst():
    oGui = cGui()
    oInputParameterHandler = cInputParameterHandler()
    sUrl = oInputParameterHandler.getValue('siteUrl')

    if 'page' not in sUrl:
        memorisedUrl = sUrl
        Page = 1
    else:
        memorisedUrl = oInputParameterHandler.getValue('memorisedUrl')
        Page = oInputParameterHandler.getValue('Page')

    oRequestHandler = cRequestHandler(sUrl)
    sHtmlContent = oRequestHandler.request()

    oParser = cParser()
    sPattern = "<div class='plWrapper'>.+?href='([^']+)' title='([^']+)'.+?src=\"([^\"]+)\""
    aResult = oParser.parse(sHtmlContent, sPattern)

    if (aResult[0] == False):
        oGui.addText(SITE_IDENTIFIER)

    if (aResult[0] == True):
        total = len(aResult[1])
        progress_ = progress().VScreate(SITE_NAME)
        oOutputParameterHandler = cOutputParameterHandler()
        for aEntry in aResult[1]:
            progress_.VSupdate(progress_, total)
            if progress_.iscanceled():
                break

            sUrl2 = aEntry[0]
            sTitle = aEntry[1].replace('- Artiste non défini', '')
            sThumb = aEntry[2]

            oOutputParameterHandler.addParameter('siteUrl', sUrl2)
            oOutputParameterHandler.addParameter('sMovieTitle', sTitle)
            oOutputParameterHandler.addParameter('sThumb', sThumb)

            oGui.addAnime(SITE_IDENTIFIER, 'showMusic', sTitle, '', sThumb, '', oOutputParameterHandler)

        progress_.VSclose(progress_)

        Page = int(Page) + 1
        oOutputParameterHandler = cOutputParameterHandler()
        oOutputParameterHandler.addParameter('siteUrl', memorisedUrl + '?page=' + str(Page))
        # On renvoi l'url memoriser et le numero de page pour l'incrementer a chaque fois
        oOutputParameterHandler.addParameter('memorisedUrl', memorisedUrl)
        oOutputParameterHandler.addParameter('Page', Page)
        oGui.addNext(SITE_IDENTIFIER, 'showOst', 'Page ' + str(Page), oOutputParameterHandler)

        oGui.setEndOfDirectory()


def showEpisodes():
    oGui = cGui()
    oParser = cParser()
    oInputParameterHandler = cInputParameterHandler()
    sUrl = oInputParameterHandler.getValue('siteUrl')
    sMovieTitle = oInputParameterHandler.getValue('sMovieTitle')
    sThumb = oInputParameterHandler.getValue('sThumb')
    sDesc = oInputParameterHandler.getValue('sDesc')

    oRequestHandler = cRequestHandler(sUrl)
    sHtmlContent = oRequestHandler.request()

    # On recupere l'id de l'anime dans l'url
    serieID = re.search('fiche-.+?-(\d+)-.+?.html', sUrl).group(1)
    sPattern = 'class="(?:download cell_impaire|download)" id="([^"]+)".+?(\d+).+?class="cell".+?>([^<]+)</td'

    aResult = oParser.parse(sHtmlContent, sPattern)

    if (aResult[0] == False):
        oGui.addText(SITE_IDENTIFIER)

    if (aResult[0] == True):
        oOutputParameterHandler = cOutputParameterHandler()
        for aEntry in sorted(aResult[1], key=lambda aResult: aResult[1]):
            sQual = aEntry[2]
            # Changemement de formats ...x... -> ....P
            if '1920×' in sQual or '1440×' in sQual or '1904×' in sQual:
                sQual = re.sub('(\d+×\d+)px', '[1080P]', sQual)
            elif '1728×' in sQual:
                sQual = re.sub('(\d+×\d+)px', '[800P]', sQual)
            elif '1280×' in sQual:
                # VSlog(sQual)
                sQual = re.sub('(\d+×\d+)px', '[720P]', sQual)
            elif '1024×' in sQual:
                sQual = re.sub('(\d+×\d+)px', '[600P]', sQual)
            elif '480×' in sQual:
                sQual = re.sub('(\d+×\d+)px', '[360P]', sQual)
            else:
                sQual = re.sub('(\d+×\d+)px', '[480P]', sQual)

            sTitle = 'E' + aEntry[1] + ' ' + sMovieTitle + ' ' + sQual
            idEpisode = aEntry[0]

            oOutputParameterHandler.addParameter('sMovieTitle', sTitle)
            oOutputParameterHandler.addParameter('siteUrl', sUrl)
            oOutputParameterHandler.addParameter('sThumb', sThumb)
            oOutputParameterHandler.addParameter('serieID', serieID)
            oOutputParameterHandler.addParameter('idEpisode', idEpisode)
            oGui.addEpisode(SITE_IDENTIFIER, 'showHosters', sTitle, '', sThumb, sDesc, oOutputParameterHandler)

    oGui.setEndOfDirectory()


def showMusic():
    oGui = cGui()
    oInputParameterHandler = cInputParameterHandler()
    sUrl = oInputParameterHandler.getValue('siteUrl')
    sThumb = oInputParameterHandler.getValue('sThumb')

    oParser = cParser()
    oRequestHandler = cRequestHandler(sUrl)
    sHtmlContent = oRequestHandler.request()
    sPattern = '<div data-track-file="([^"]+)".+?data-track-name="([^"]+)".+?"><span.+?>([^<]+)</span>'
    aResult = oParser.parse(sHtmlContent, sPattern)

    if (aResult[0] == False):
        oGui.addText(SITE_IDENTIFIER)

    if (aResult[0] == True):
        oOutputParameterHandler = cOutputParameterHandler()
        for aEntry in aResult[1]:
            sTitle = aEntry[2] + ' ' + aEntry[1]
            mp3Url = aEntry[0]

            oOutputParameterHandler.addParameter('sMovieTitle', sTitle)
            oOutputParameterHandler.addParameter('mp3Url', mp3Url)
            oOutputParameterHandler.addParameter('sThumb', sThumb)
            oGui.addEpisode(SITE_IDENTIFIER, 'showMp3', sTitle, '', sThumb, '', oOutputParameterHandler)

    oGui.setEndOfDirectory()


def showMp3():
    oGui = cGui()
    oInputParameterHandler = cInputParameterHandler()
    mp3Url = oInputParameterHandler.getValue('mp3Url')
    sMovieTitle = oInputParameterHandler.getValue('sMovieTitle')
    sThumb = oInputParameterHandler.getValue('sThumb')

#     if 'mp3' in mp3Url:
#         sHosterUrl = mp3Url

    oHoster = cHosterGui().checkHoster('m3u8')
    if (oHoster != False):
        oHoster.setDisplayName(sMovieTitle)
        oHoster.setFileName(sMovieTitle)
        cHosterGui().showHoster(oGui, oHoster, mp3Url, sThumb)

    oGui.setEndOfDirectory()


def showHosters():
    oGui = cGui()
    oInputParameterHandler = cInputParameterHandler()
    sUrl = oInputParameterHandler.getValue('siteUrl')
    sMovieTitle = oInputParameterHandler.getValue('sMovieTitle')
    sThumb = oInputParameterHandler.getValue('sThumb')
    serieID = oInputParameterHandler.getValue('serieID')
    idEpisode = oInputParameterHandler.getValue('idEpisode')

    sHosterUrl = ''
    if 'fiche-anime' in sUrl:
        sHosterUrl = URL_MAIN + 'launch-download-1-' + serieID + '-ddl-' + idEpisode + '.html'
    elif 'fiche-drama' in sUrl:
        sHosterUrl = URL_MAIN + 'launch-download-2-' + serieID + '-ddl-' + idEpisode + '.html'

    oHoster = cHosterGui().checkHoster('m3u8')
    if (oHoster != False):
        oHoster.setDisplayName(sMovieTitle)
        oHoster.setFileName(sMovieTitle)
        cHosterGui().showHoster(oGui, oHoster, sHosterUrl, sThumb)

    oGui.setEndOfDirectory()