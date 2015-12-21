# -*- coding: utf-8 -*-

import CommonFunctions as common
import urllib
import urllib2
import os,sys
import xbmcplugin
import xbmcgui
import xbmcaddon
from core import updater
from core import logger
from providers.r977musiccom import R977Musiccom
from providers.radionet import Radionet
from providers.redmp3cc import Redmp3cc
from core.decoder import Decoder
#import re

##INIT GLOBALS##

addon = xbmcaddon.Addon(id='org.harddevelop.kodi.juke')
home = addon.getAddonInfo('path')
icon = xbmc.translatePath( os.path.join( home, 'icon.png' ) )
MAIN_URL = xbmcplugin.getSetting(int(sys.argv[1]), "remote_repository")

##CONSTANTS PARTS##
BROWSE_CHANNELS = "browse_channels"
MAX = 103

def get_params():
    param=[]
    paramstring=sys.argv[2]
    if len(paramstring)>=2:
        params=sys.argv[2]
        cleanedparams=params.replace('?','')
        if (params[len(params)-1]=='/'):
            params=params[0:len(params)-2]
        pairsofparams=cleanedparams.split('&')
        param={}
        for i in range(len(pairsofparams)):
            splitparams={}
            splitparams=pairsofparams[i].split('=')
            if (len(splitparams))==2:
                param[splitparams[0]]=splitparams[1]

    return param

def add_dir(name,url,mode,iconimage,provider,page="", thumbnailImage='',lastCookie=''):
    type = "Video"
    #print url
    #print mode
    #print page

    #name = re.sub('[^A-Za-z0-9]+', '',name)
    #print page
    u=sys.argv[0]+"?url="+urllib.quote_plus(url.decode('utf-8', 'replace').encode('iso-8859-1', 'replace'))
    u+="&cookie="+lastCookie
    u+="&mode="+str(mode)+"&page="
    try:
        u+=str(page)
    except:
        u+=page
        pass
    provider = str(provider)
    u+="&provider="+provider

    ok=True

    liz=xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
    liz.setInfo(type='Video', infoLabels={'Title': name})

    if mode == 2 or (mode >=100 and mode<=MAX): #playable, not browser call, needs decoded to be playable or rtmp to be obtained
        liz.setProperty("IsPlayable", "true")
        liz.setPath(url)
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False) #Playable
    else:
        liz.setProperty('Fanart_Image', thumbnailImage)
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True) #Folder

    return ok

def get_main_dirs():
    add_dir(addon.getLocalizedString(10001), BROWSE_CHANNELS, 3, '', icon, 0)
    try:
        if updater.isUpdatable():
            add_dir(addon.getLocalizedString(10011), '', 0, icon, 0)
    except:
        logger.error("Couldn't add update option: probably server is down!")

def get_dirs(url,name,page):
    #print "using url: "+url
    response = urllib2.urlopen(url)
    html = response.read()
    if url.endswith(".xml"): #main channels, it's a list to browse
        lists = common.parseDOM(html,"list")
        for item in lists:
            name = common.parseDOM(item,"name")[0].encode("utf-8")
            value = common.parseDOM(item,"url")[0].encode("utf-8")
            add_dir(name, value, 1, icon,'', 0)
    else: #it's the final list channel, split
        bruteChannels = html.split("#EXTINF")
        for item in bruteChannels:
            item = item[item.find(",")+1:]
            name = item[:item.find("\n")]
            value = item[item.find("\n")+1:]
            value = value[:value.find("\n")]
            #print "detected channel: "+name+" with url: "+value
            if name <> "" and value <> "": ##check for empty channels, we don't want it in our list
                add_dir(name, value, 2, icon, '', name)

def open(url,page):
    listitem = xbmcgui.ListItem(page)
    listitem.setProperty('IsPlayable','true')
    listitem.setPath(url)
    listitem.setInfo("video",page)
    try:
        player = xbmc.Player(xbmc.PLAYER_CORE_AUTO)
        if player.isPlaying() :
            player.stop()
        #xbmc.sleep(1000)
        player.showSubtitles(False)
        #urlPlayer = urllib.unquote_plus(url.replace("+","@#@")).replace("@#@","+")
        #urlPlayer = urllib.unquote_plus(url) ##THIS METHOD FAILS IN SOME CASES SHOWING A POPUP (server petition and ffmpeg internal problem)
        #player.play(urlPlayer,listitem) ##THIS METHOD FAILS IN SOME CASES SHOWING A POPUP (server petition and ffmpeg internal problem)
        #print 'opening... '+url
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem) ##FIX FOR PREVIEWS LINE##
        #xbmc.executebuiltin('Dialog.Close(all, true)') ## could be returned an empty element in a list, so player open the next and shows a invalid popup
    except:
        pass
        #print(traceback.format_exc())

def browse_channels(url,page): #BROWSES ALL PROVIDERS
    add_dir("977music.com", '977musiccom', 4, "http://www.977music.com/images11/logo.png", '977musiccom', 0)
    add_dir("radio.net", 'radionet', 4, "http://www.aquaradio.net16.net/Media/Logos/radio.net.png", 'radionet', 0)
    add_dir("redmp3.cc", 'redmp3cc', 4, "", 'redmp3cc', 0)

def browse_channel(url,page,provider,cookie=''): #MAIN TREE BROWSER IS HERE!
    if provider == "977musiccom":
        jsonChannels = R977Musiccom.getChannels(page,cookie)
        for item in jsonChannels:
            mode = 4
            image = icon
            if item.has_key("thumbnail"):
                image = item["thumbnail"]
            if item.has_key("finalLink"):
                mode = 2
            add_dir(item["title"],item["link"],mode,image,"977musiccom",item["link"],'',R977Musiccom.cookie)
    elif provider== "radionet":
        jsonChannels = Radionet.getChannels(page,cookie)
        mode = 102
        for item in jsonChannels:
            image = icon
            if item.has_key("thumbnail"):
                image = item["thumbnail"]
            add_dir(item["title"],item["link"],mode,image,"radionet",item["link"],'',Radionet.cookie)
    elif provider== "redmp3cc":
        jsonChannels = Redmp3cc.getChannels(page,cookie)
        mode = 4
        for item in jsonChannels:
            image = icon
            if item.has_key("thumbnail"):
                image = item["thumbnail"]
            if item["link"].find(".html")==-1:
                mode = 103
            add_dir(item["title"],item["link"],mode,image,"redmp3cc",item["link"],'',Redmp3cc.cookie)
    logger.info(provider)

def open_channel(url,page,provider=""):
    finalUrls = R977Musiccom.getChannelUrl(url)
    for finalUrl in finalUrls:
        add_dir(page+", "+finalUrl["name"],finalUrl["url"],2,provider,page)

def init():
    params=get_params()

    url=""
    mode=None
    page=""
    cookie=""

    try:
        page=urllib.unquote_plus(params["page"])
    except:
        pass
    try:
        url=urllib.unquote_plus(params["url"])
    except:
        pass
    try:
        mode=int(params["mode"])
    except:
        pass
    try:
        provider=urllib.unquote_plus(params["provider"])
    except:
        pass
    try:
        logger.info("cookie was filled with: "+params["cookie"])
        cookie=urllib.unquote_plus(params["cookie"])
    except:
        pass

    #print "Mode: "+str(mode)
    print "URL: "+str(url)
    print "cookie: "+str(cookie)

    if mode==None: #init
        get_main_dirs()

    elif mode==1: #get channels
        get_dirs(url, '', page)

    elif mode == 2: #open video in player
        open(url,page)
    elif mode == 3:
        browse_channels(url,page)
    elif mode == 4:
        browse_channel(url,page,provider,cookie)
    elif mode == 5:
        open_channel(url,page)
    elif mode == 0: #update
        updater.update()
        get_main_dirs()
    elif mode == 100: #decode provider link
        logger.info("decoding: "+url)
        link = Decoder.decodeLink(url)
        logger.info("decoded: "+link)
        open(link,page)
    elif mode == 101:
        jsonChannels = R977Musiccom.getChannels(page,cookie)
        url = jsonChannels[0]["link"]
        logger.info("found link: "+url+", launching...")
        open(url,page) #same that 2, but reserved for rtmp
    elif mode == 102:
        jsonChannels = Radionet.getChannels(page,cookie)
        url = jsonChannels[0]["link"]
        logger.info("found link: "+url+", launching...")
        open(url,page) #same that 2, but reserved for rtmp
    elif mode == 103:
        jsonChannels = Redmp3cc.getChannels(url,cookie)
        url = jsonChannels[0]["link"]
        logger.info("found link: "+url+", launching...")
        open(url,page) #same that 2, but reserved for rtmp
        os.remove(url)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

init()
