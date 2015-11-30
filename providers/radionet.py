import httplib
import urllib
from StringIO import StringIO
import gzip
from core.decoder import Decoder
from core import logger

class Radionet():

    cookie = ""
    MAIN_URL = "http://www.radio.net/stations/"
    REFERER = "http://www.radio.net/stations/"

    @staticmethod
    def getChannels(page,cookie=''):
        x = []
        print page
        if str(page) == '0':
            page=Radionet.MAIN_URL
            stations_lists = Radionet.getContentFromUrl("http://www.radio.net/stations/","",Radionet.cookie,Radionet.REFERER)
            x = Radionet.parseListStations(stations_lists)
        else:
            html = Radionet.getContentFromUrl(page,"",cookie,Radionet.REFERER)
            element = {}
            element["title"] = Decoder.extract('"seoTitle":"','",',html)
            element["link"] = Decoder.extract('"streamUrl":"','",',html)
            element["thumbnail"] = Decoder.extract('"logo100x100":"','",',html)
            element["finalLink"] = True
            x.append(element)
        return x

    @staticmethod
    def parseListStations(html):
        x = []
        html = Decoder.extract('<div class="col-sm-7 col-md-8 station-list">','aside class="col-sm-5 col-md-4">',html)
        for elementHtml in html.split('<a class="stationinfo-info-toggle" href="" ng-click="toggle()"></a>'):
            element = {}
            link = Decoder.extract('<a href="//','" class="stationinfo-link">',elementHtml)
            title = Decoder.extract('<strong>','</strong>',elementHtml)
            img = Decoder.extract('<img src="','"',elementHtml)
            element["title"] = title
            element["link"] = link
            element["thumbnail"] = img
            if element["link"].find("http")!=0:
                element["link"] = "http://"+element["link"]
            if element["title"].find('</div>')==-1:
                logger.info("found element: "+element["title"]+", with link: "+element["link"])
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
                if rValue.find("JSESSIONID=")>-1:
                    cookieValue = rValue[rValue.find("JSESSIONID="):]
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
            Radionet.cookie = cookieValue
        logger.info("cookie was updated to: "+Radionet.cookie)
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
            html = Radionet.getContentFromUrl(location,data,Radionet.cookie,url)
        return html
