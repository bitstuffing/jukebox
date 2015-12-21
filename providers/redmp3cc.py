# -*- coding: utf-8 -*-

import httplib
import urllib
import os
import binascii
import xbmc, xbmcaddon
from core.decoder import Decoder
from core import jsunpack
from core import logger
from core.downloader import Downloader
from core import downloadtools

class Redmp3cc(Downloader):

    MAIN_URL = "http://redmp3.cc"

    @staticmethod
    def getChannels(page,cookie='',referer=''):
        x = []
        html = ""
        if str(page) == '0':
            x = Redmp3cc.getMainSections()
        elif str(page) == 'songs.html':
            page=Redmp3cc.MAIN_URL+"/"
            html = Downloader.getContentFromUrl(page,"",cookie,"")
            x = Redmp3cc.extractElementsPlayer(html)
        elif str(page) == 'search.html':
            keyboard = xbmc.Keyboard("")
            keyboard.doModal()
            text = ""
            if (keyboard.isConfirmed()):
                text = keyboard.getText()
                x = Redmp3cc.search(text)
        elif str(page).find(".html")!=-1:
            if str(page) == 'albums.html'!=-1:
                page = Redmp3cc.MAIN_URL
                html = Downloader.getContentFromUrl(page,"",cookie,"")
                x = Redmp3cc.extractElementsAlbum(html)
            else:
                html = Downloader.getContentFromUrl(page,"",cookie,"")
                x = Redmp3cc.extractElementsPlayer(html)
        else:
            logger.info("page is: "+page)
            response = Redmp3cc.getContentFromUrl(page,"",cookie,Redmp3cc.MAIN_URL,True)
            #logger.info("will be used a mp3 url: "+Decoder.extract('<a href="','">here',response))
            host = response[response.find("://")+len("://"):]
            if host.find("/")>-1:
                host = host[0:host.find("/")]
            cookie = Redmp3cc.cookie
            referer = page
            logger.info("cookie is: "+cookie+", referer is: "+referer)
            headers = downloadtools.buildMusicDownloadHeaders(host,cookie,referer)
            filename= Decoder.extract('filename=','&',response)
            ROOT_DIR = xbmcaddon.Addon(id='org.harddevelop.kodi.juke').getAddonInfo('path')
            downloadtools.downloadfile(response,ROOT_DIR+"/"+filename,headers,False,True)
            #downloadtools.downloadfileGzipped(response,filename,headers)
            x.append(Redmp3cc.buildDownloadedFile(xbmc.makeLegalFilename(ROOT_DIR+"/"+filename)))
        return x

    @staticmethod
    def search(text,page=0,cookie=''):
        page = "http://redmp3.cc/mp3-"+urllib.unquote_plus(text)+"/"
        html = Downloader.getContentFromUrl(page,"",cookie,"")
        x = Redmp3cc.extractElementsPlayer(html)
        return x

    @staticmethod
    def getMainSections():
        x = []
        element = {}
        element["link"] = 'songs.html'
        element["title"] = 'Popular tracks'
        x.append(element)
        element2 = {}
        element2["link"] = 'albums.html'
        element2["title"] = 'Last added albums'
        x.append(element2)
        element3 = {}
        element3["link"] = 'search.html'
        element3["title"] = 'Search'
        x.append(element3)
        return x

    @staticmethod
    def buildDownloadedFile(filename,title='Empty title'):
        logger.info("building title: "+title+", link: "+filename)
        element = {}
        element["link"] = filename
        element["title"] = title
        return element

    @staticmethod
    def extractElementsPlayer(html):
        x = []
        i = 0
        for value in html.split('<div class="player"'):
            if i>0:
                element = {}
                title = Decoder.extract('data-title="','">',value)
                link = Decoder.extract('data-mp3url="','" ',value)
                element["title"] = title
                element["link"] = Redmp3cc.MAIN_URL+link
                logger.info("append: "+title+", link: "+element["link"])
                x.append(element)
            i+=1
        return x

    @staticmethod
    def extractElementsAlbum(table):
        x = []
        i = 0
        for value in table.split('<div class="album">'):
            if i>0:
                element = {}
                title = Decoder.extract(' alt="','"/>',value)
                link = Decoder.extract('<a href="','" ',value)
                img = Decoder.extract('src="','" ',value)
                element["title"] = title
                element["link"] = Redmp3cc.MAIN_URL+link
                element["thumbnail"] = Redmp3cc.MAIN_URL+img
                logger.info("append: "+title+", link: "+element["link"])
                x.append(element)
            i+=1
        return x

    @staticmethod
    def getContentFromUrl(url,data="",cookie="",referer="",ajax=False):
        form = urllib.urlencode(data)
        host = url[url.find("://")+len("://"):]
        subUrl = ""
        logger.info("url is: "+host)
        if host.find("/")>-1:
            host = host[0:host.find("/")]
            subUrl = url[url.find(host)+len(host):]
        logger.info("host: "+host+":80 , subUrl: "+subUrl)
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:41.0) Gecko/20100101 Firefox/41.0",
            "Accept-Language" : "en-US,en;q=0.8,es-ES;q=0.5,es;q=0.3",
            #"Accept-Encoding" : "gzip, deflate",
            "Conection" : "keep-alive",
            "Host":host,
            "DNT":"1",
            #"Content-Type" : "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Host":host
        }
        if referer!="":
            headers["Referer"] = referer

        if cookie !="":
            headers["Cookie"] = cookie
        if ajax:
            headers["X-Requested-With"] = "XMLHttpRequest"
            headers["Accept"] = "*/*"

        h = httplib.HTTPConnection(host+":80")
        h.request('GET', subUrl, data, headers)
        r = h.getresponse()

        headersReturned = r.getheaders()
        cfduid = ""
        location = ""
        for returnedHeader,rValue in headersReturned:
            if returnedHeader == 'set-cookie':
                #print "header1: "+returnedHeader+", value1: "+rValue
                if rValue.find("__cfduid=")>-1:
                    logger.info("detected cfduid: "+rValue)
                    cfduid = rValue[rValue.find("__cfduid="):]
                    if cfduid.find(";")>-1:
                        cfduid = cfduid[0:cfduid.find(";")]
            elif returnedHeader == 'location':
                logger.info("Location detected: using location: "+rValue)
                location = rValue
            else:
                logger.info("rejected cookie: "+returnedHeader+", "+rValue)
        if cfduid!= '':
            Downloader.cookie = cfduid
        logger.info("cookie was updated to: "+Downloader.cookie)
        html = r.read()
        if location != '': #disabled at this moment
            html = location
        return html