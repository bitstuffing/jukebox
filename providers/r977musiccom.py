import httplib
import urllib
import os
import binascii
import base64
from StringIO import StringIO
import gzip
from core.decoder import Decoder
from core import jsunpack
from core import logger

class R977Musiccom():

    cookie = ""
    MAIN_URL = "http://www.977music.com/"
    REFERER = "http://www.977music.com/swf/N77Music.swf"

    @staticmethod
    def getChannels(page,cookie=''):
        x = []
        referer = R977Musiccom.REFERER
        print page
        if str(page) == '0':
            page=R977Musiccom.MAIN_URL
            html = R977Musiccom.getContentFromUrl(page,"",R977Musiccom.cookie,referer)
            stations_lists = R977Musiccom.getContentFromUrl("http://www.977music.com/ajax/stations_list_xml.php","",R977Musiccom.cookie,referer)
            print "station list: "+stations_lists
        else:
            page = base64.standard_b64decode(page)
            logger.info("launching petition from page: "+page)
            #extract id
            id = Decoder.extract("?id=","&",page)
            songId = Decoder.extract("song_id=","&",page)
            if cookie=='':
                logger.info("launching to get an virgin cookie...")
                R977Musiccom.getContentFromUrl(R977Musiccom.MAIN_URL,"","","") #get a right cookie
                cookie = R977Musiccom.cookie
            else:
                logger.info("Detected a cookie: "+cookie)
            #logger.info("using always the same cookie: "+cookie)
            logger.info("simulating get referer (swf)... cookie: "+cookie)
            flashPlayer = R977Musiccom.getContentFromUrl(referer,"",cookie,R977Musiccom.MAIN_URL)
            logger.info("obtaining songs...")
            songs = R977Musiccom.getContentFromUrl("http://www.977music.com/ajax/rest/playlist.php/"+id+"/","",cookie,R977Musiccom.MAIN_URL,True)
            #print "songs: "+str(songs)
            logger.info("now is the vital petition, launching... ")
            html = R977Musiccom.getContentFromUrl(page,'',cookie,referer)
            x = R977Musiccom.parseListSongs(songs,html)
        #print "html: "+html
        if html.find('<div class="list_box">')>-1: #it's a list, needs decode
            table = Decoder.extract('<div class="list_box">','</ul>',html)
            x = R977Musiccom.extractElements(table,html)
            print "done!"
        else:
            print "else content!"
            print html
            pass
        return x

    @staticmethod
    def parseListSongs(songs,html):
        x = []
        #jsonSongs = json.load(songs)
        for elementHtml in html.split("<Channel "):
            element = {}
            title = Decoder.extract('name="','"',elementHtml)
            channel = Decoder.extract('<RTMP>','</RTMP>',elementHtml)
            url = Decoder.extract("<URL>","</URL>",elementHtml)
            element["title"] = title
            element["link"] = channel+" playpath="+(url.replace(' ','%20'))+" pageUrl="+R977Musiccom.MAIN_URL+" swfUrl="+R977Musiccom.REFERER
            element["finalLink"] = True
            if element["link"].find("rtmp")==0:
                logger.info("found element: "+element["title"]+", with link: "+element["link"])

                x.append(element)
        return x

    @staticmethod
    def extractElements(table,html=""):
        x = []
        splitter = 'data-playlist-id="'
        splitter2 = 'Flash Player">'
        splitter3 = "new_player_block.nss_load_playlist('"
        for fieldHtml in table.split('<li '):
            if fieldHtml.find(splitter)>-1:
                element = {}
                playlistId = Decoder.extract(splitter,'" >',fieldHtml)
                title = Decoder.extract(splitter2,'</a>',fieldHtml).strip()
                url = Decoder.extract(splitter3,"' + jQuery(",fieldHtml).replace("&amp;","&")
                rel = Decoder.rExtract('" rel="','">'+title+"</a>",html)
                url = R977Musiccom.MAIN_URL+url+rel+"&userId=0"
                element["title"] = title
                element["link"] = base64.standard_b64encode(url)
                logger.info("found title: "+element["title"]+", link: "+element["link"])
                if len(element["title"])>0:
                    #TODO: now we tries to extract the content from json 'html'
                    x.append(element)

        return x

    @staticmethod
    def getContentFromUrl(url,data="",cookie="",referer="",ajax=False):
        form = urllib.urlencode(data)
        host = url[url.find("://")+len("://"):]
        subUrl = ""
        print "url is: "+host
        if host.find("/")>-1:
            host = host[0:host.find("/")]
            subUrl = url[url.find(host)+len(host):]
        print "host: "+host+":80 , subUrl: "+subUrl
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:41.0) Gecko/20100101 Firefox/41.0",
            "Accept-Language" : "en-US,en;q=0.8,es-ES;q=0.5,es;q=0.3",
            "Accept-Encoding" : "gzip, deflate",
            "Conection" : "keep-alive",
            "Host":host,
            "DNT":"1",
            #"Content-Type" : "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        if referer!="":
            logger.info("using referer: "+referer)
            headers["Referer"] = referer
        if cookie!='':
            logger.info("petition was updated to use cookie: "+cookie)
            headers["Cookie"] = cookie

        h = httplib.HTTPConnection(host+":80")
        if ajax:
            headers["X-Requested-With"] = 'XMLHttpRequest'
            headers["Accept"] = 'application/json, text/javascript, */*; q=0.01'
        h.request('GET', subUrl, data, headers)
        r = h.getresponse()

        headersReturned = r.getheaders()
        cookieValue = ""
        location = ""
        contentEncoding = ""
        for returnedHeader,rValue in headersReturned:
            if returnedHeader == 'set-cookie':
                if rValue.find("PHPSESSID=")>-1:
                    cookieValue = rValue[rValue.find("PHPSESSID="):]
                    if cookieValue.find(";")>-1:
                        cookieValue = cookieValue[0:cookieValue.find(";")]
            elif returnedHeader == 'location':
                logger.info("Location detected: using location: "+rValue)
                location = rValue
            elif returnedHeader == 'content-encoding':
                logger.info("Detected gzip response...")
                contentEncoding = rValue
            else:
                logger.info("rejected cookie: "+returnedHeader+", "+rValue)
        if cookieValue!= '':
            R977Musiccom.cookie = cookieValue
        logger.info("cookie was updated to: "+R977Musiccom.cookie)
        if contentEncoding == 'gzip':
            logger.info("response: gzip to plain...")
            buf = StringIO(r.read())
            f = gzip.GzipFile(fileobj=buf)
            html = f.read()
            logger.info("response: gzip done!")
        else:
            html = r.read()
        if location != '':
            logger.info("launching redirection to: "+location)
            html = R977Musiccom.getContentFromUrl(location,data,R977Musiccom.cookie,url)
        return html
