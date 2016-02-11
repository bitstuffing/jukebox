# -*- coding: utf-8 -*-

import httplib
import urllib
import os
import binascii
import base64
import xbmc, xbmcaddon
from core.decoder import Decoder
from core import jsunpack
from core import logger
from core.downloader import Downloader
from core import downloadtools

try:
    import json
except:
    import simplejson as json


class Fildonet(Downloader):

    MAIN_URL = "http://fildo.net/"
    ARTIST = "http://fildo.net/info.php?show=1&artist="
    PLAY = "http://fildo.net/images/icons/play.png"
    ALBUM = "http://fildo.net/albumInfo.php?picAlbum=ok&albumId="
    SONG = "http://fildo.net/albumInfo.php?songId="

    @staticmethod
    def getChannels(page,cookie='',referer=''):
        x = []
        html = ""
        if str(page) == '0':
            x = Fildonet.getMainSections()
        elif str(page) == '100artist':
            page=Fildonet.MAIN_URL
            html = Downloader.getContentFromUrl(page,"",cookie,"")
            x = Fildonet.extractElementsArtist(html)
        elif str(page) == 'topalbums':
            page=Fildonet.MAIN_URL
            html = Downloader.getContentFromUrl(page,"",cookie,"")
            x = Fildonet.extractElementsAlbum(html)
        elif str(page) == 'lastestplaylists':
            pass
        elif str(page).find('search')!=-1:
            keyboard = xbmc.Keyboard("")
            keyboard.doModal()
            text = ""
            if (keyboard.isConfirmed()):
                text = keyboard.getText()
                x = Fildonet.search(text)
        else:
            page = base64.standard_b64decode(page)
            logger.info("ELSE --- page is: "+page)
            html = Downloader.getContentFromUrl(page,"",cookie,"")
            if page.find("albumId=")!=-1:
                jsonData = json.loads(html)
                x = Fildonet.buildFromJSON(jsonData)
            else:
                x = Fildonet.extractElementsPlayer(html)
        return x

    @staticmethod
    def buildFromJSON(jsonData):
        x = []
        for value in jsonData["songs"]:
            element = {}
            link = value["mp3Url"]
            logger.debug("brute link is: "+link)
            element["link"] = link
            element["thumbnail"] = jsonData["picUrl"]
            element["title"] = value["name"]
            element["finalLink"] = True
            logger.info("append element: "+element["title"]+", link: "+element["link"])
            x.append(element)
        return x

    @staticmethod
    def parseLinkToLoadBalancer(link):
        if link.find("http://p")>-1 and link.find(".")>-1: #.replace("http://p3.","http://219.138.27.58/m2.")
            logger.debug("detected link: "+link)
            postLink = link[link.find(".")+1:]
            link = "http://219.138.27.58/m2."+postLink
        logger.info("processed link is: "+link)
        return link

    @staticmethod
    def search(text,page=0,cookie=''):
        page = "http://fildo.net/autocomplete163.php?term="+urllib.quote_plus(text)
        html = Downloader.getContentFromUrl(page,"",cookie,"")
        x = Fildonet.extractElementsSearch(html)
        return x

    @staticmethod
    def extractElementsSearch(html):
        jsonContent = json.loads(html)
        x = []
        for jsonValues in jsonContent:
            element = {}
            element["title"] = jsonValues["label"]+" - "+jsonValues["category"]
            if jsonValues["category"] == 'Artists':
                link = base64.standard_b64encode(Fildonet.ARTIST+str(jsonValues["label"]))
            elif jsonValues["category"] == 'Albums':
                link = base64.standard_b64encode(Fildonet.ALBUM+str(jsonValues["id"]))
            elif jsonValues["category"] == 'Songs':
                id = jsonValues["id"]
                html2 = Downloader.getContentFromUrl(Fildonet.SONG+str(id))
                songsJSONS = json.loads(html2)
                for songsJSON in songsJSONS:
                    link = songsJSON["mp3Url"]
                    element["thumbnail"] = songsJSON["picUrl"]
            element["link"] = link
            x.append(element)
        return x

    @staticmethod
    def getMainSections():
        x = []
        element = {}
        element["link"] = '100artist'
        element["title"] = 'Top 100 artist'
        x.append(element)
        element2 = {}
        element2["link"] = 'topalbums'
        element2["title"] = 'Top Albums'
        x.append(element2)
        '''
        element3 = {}
        element3["link"] = 'lastestplaylists'
        element3["title"] = 'Latest 100 Playlists'
        x.append(element3)
        '''
        elementS = {}
        elementS["link"] = 'search'
        elementS["title"] = 'Search'
        x.append(elementS)
        return x

    @staticmethod
    def buildDownloadedFile(filename,title='Empty title'):
        logger.info("building title: "+title+", link: "+filename)
        element = {}
        element["link"] = filename
        element["title"] = title
        return element

    @staticmethod
    def extractElementsArtist(html):
        x = []
        i=0
        for value in html.split('<li class="topListenedBox click js-lateral-info " >'):
            if i>0:
                element = {}
                title = Decoder.extract('<div class="topListenedBoxDiv click js-lateral-info ">','</div>',value)
                element["title"] = title
                element["link"] = base64.standard_b64encode(Fildonet.ARTIST+title)
                if value.find('data-src="')!=-1:
                    element["thumbnail"] = Fildonet.MAIN_URL+Decoder.extract('data-src="','" ',value)
                logger.info("append1: "+title+", link: "+element["link"])
                x.append(element)
            i+=1
        return x

    @staticmethod
    def extractElementsPlayer(html):
        x = []
        i = 0
        for value in html.split("<li class='hotSongsItem' songid="):
            if i>0:
                element = {}
                title = Decoder.extract("songname='","'",value)+" - "+Decoder.extract("songartist='","'",value)
                link = Decoder.extract("songmp3='","'",value)
                element["title"] = title
                if link.find(".mp3")==-1:
                    element["link"] = base64.standard_b64encode(Fildonet.MAIN_URL+link)
                else:
                    element["link"] = link
                element["thumbnail"] = Fildonet.PLAY
                logger.info("append2: "+title+", link: "+element["link"])
                x.append(element)
            i+=1
        return x

    @staticmethod
    def extractElementsAlbum(table):
        x = []
        i = 0
        for value in table.split('<li class="topListenedBox click js-lateral-info" onclick=\'albumClick('):
            if i>0:
                element = {}
                title = Decoder.extract('<div class="topListenedBoxDiv">','</div>',value).replace('<br>'," - ")
                link = Decoder.extract('","','");\'>',value)
                img = Decoder.extract(' data-src="','" ',value)
                element["title"] = title
                if link.find(".mp3")==-1:
                    element["link"] = base64.standard_b64encode(Fildonet.ALBUM+link)
                else:
                    element["link"] = link
                element["thumbnail"] = img
                logger.info("append3: "+title+", link: "+element["link"]+", thumbnail: "+element["thumbnail"])
                x.append(element)
            i+=1
        return x