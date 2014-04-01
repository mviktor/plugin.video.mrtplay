#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib
import urllib2
import socket
import sys
import os
import re
import xbmcplugin
import xbmcaddon
import xbmcgui
import HTMLParser

from BeautifulSoup import BeautifulSoup

addon = xbmcaddon.Addon()
socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
addonID = addon.getAddonInfo('id')
translation = addon.getLocalizedString
xbox = xbmc.getCondVisibility("System.Platform.xbox")

# while (not os.path.exists(xbmc.translatePath("special://profile/addon_data/"+addonID+"/settings.xml"))):
#     addon.openSettings()

BASE = 'http://play.mrt.com.mk'
ADDON=__settings__ = xbmcaddon.Addon(id='plugin.video.mrtplay')
DIR_USERDATA = xbmc.translatePath(ADDON.getAddonInfo('profile'))
VERSION_FILE = DIR_USERDATA+'version.txt'
VISITOR_FILE = DIR_USERDATA+'visitor.txt'

__version__ = ADDON.getAddonInfo("version")

user_agent = 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:11.0) Gecko/20100101 Firefox/11.0'
str_accept = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'

def platformdef():
	if xbmc.getCondVisibility('system.platform.osx'):
		if xbmc.getCondVisibility('system.platform.atv2'):
			log_path = '/var/mobile/Library/Preferences'
			log = os.path.join(log_path, 'xbmc.log')
			logfile = open(log, 'r').read()
		else:
			log_path = os.path.join(os.path.expanduser('~'), 'Library/Logs')
			log = os.path.join(log_path, 'xbmc.log')
			logfile = open(log, 'r').read()
	elif xbmc.getCondVisibility('system.platform.ios'):
		log_path = '/var/mobile/Library/Preferences'
		log = os.path.join(log_path, 'xbmc.log')
		logfile = open(log, 'r').read()
	elif xbmc.getCondVisibility('system.platform.windows'):
		log_path = xbmc.translatePath('special://home')
		log = os.path.join(log_path, 'xbmc.log')
		logfile = open(log, 'r').read()
	elif xbmc.getCondVisibility('system.platform.linux'):
		log_path = xbmc.translatePath('special://home/temp')
		log = os.path.join(log_path, 'xbmc.log')
		logfile = open(log, 'r').read()
	else:
		logfile='Starting XBMC (Unknown Git:.+?Platform: Unknown. Built.+?'

	match=re.compile('Starting XBMC \((.+?) Git:.+?Platform: (.+?)\. Built.+?').findall(logfile)
	for build, platform in match:
		if re.search('12.0',build,re.IGNORECASE):
			build="Frodo"
		if re.search('11.0',build,re.IGNORECASE):
			build="Eden"
		if re.search('13.0',build,re.IGNORECASE):
			build="Gotham"
		return platform

	return "Unknown"

def fread(filename):
	ver = ''
	h = open(filename, "r")
	try:
		data = h.read()
	finally:
		h.close()
	return data

def fwrite(filename, data):
	h = open(filename, "wb")
	try:
		h.write(data)
	finally:
		h.close()

def get_visitorid():
	if os.path.isfile(VISITOR_FILE):
		visitor_id = fread(VISITOR_FILE)
	else:
		from random import randint
		visitor_id = str(randint(0, 0x7fffffff))
		fwrite(VISITOR_FILE, visitor_id)

	return visitor_id

__visitor__ = get_visitorid()

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

def setView(content='movies', mode=503):
	return 0
#	xbmcplugin.setContent(int(sys.argv[1]), content)
#	xbmc.executebuiltin("Container.SetViewMode("+str(mode)+")")

def registerVersion(ver):
	result = True
	url = 'http://localhost:8001/register_plugin.php?ver='+ver+'&platform='+urllib.quote(platformdef())
	req = urllib2.Request(url)
	req.add_header('User-Agent', user_agent)
	try:
		response = urllib2.urlopen(req)
		link = response.read()
		response.close()
	except:
		result = False
	return result

def mrtfrontList():
	url = BASE
	req = urllib2.Request(url)
	req.add_header('User-Agent', user_agent)
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()
	match=re.compile('<li class="">\n        <a href="(.+?)">\n            (.+?)        </a>\t\n    </li>').findall(link)
	return match

def duration_in_minutes(duration):
	split_duration=duration.split(':')
	minutes=0
	for i in range(0, len(split_duration)-1):
		minutes = minutes*60 + int(split_duration[i])
	return minutes

def list_mrtchannel(url):
	url = BASE+url
	req = urllib2.Request(url)
	req.add_header('User-Agent', user_agent)
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()
	list=[]
	match=re.compile('<div class="col-xs-6 col-sm-3 (.+?) content">\n.+?<a href="(.+?)".+?\n.+?<img src="(.+?)".+?\n.+?\n.+?<span class="title gradient">(.+?)</span>').findall(link)

	# extract channels
	for type,url,thumb,title in match:
		list.append([type,url,thumb,'',title])

	match=re.compile('<div class="col-xs-6 col-sm-3 (.+?) content">\n.+?<a href="(.+?)".+?\n.+?<img src="(.+?)".+?\n.+?\n.+?<span class="duration">(.+?)</span>\n.+?<span class="title gradient">(.+?)</span>').findall(link)

	# extract latest videos on current channel
	for type,url,thumb,duration,title in match:
		list.append([type,url,thumb,str(duration_in_minutes(duration)),title])

	return list

def list_mrtlive():
	url = BASE
	req = urllib2.Request(url)
	req.add_header('User-Agent', user_agent)
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()
	start=link.find('<ul class="dropdown-menu text-left')
	end=link.find('</ul', start)
	match=re.compile('<a class="channel" href=".+?" data-href="(.+?)" .+? title="(.+?)">\n.*?<img src="(.+?)"').findall(link[start:end])
	return match

def playmrtvideo(url):
	pDialog = xbmcgui.DialogProgress()
	pDialog.create('MRT Play live stream', 'Initializing')
	req = urllib2.Request(url)
	req.add_header('User-Agent', user_agent)
	pDialog.update(50, 'Fetching video stream')
	response = urllib2.urlopen(req)
	link = response.read()
	response.close()

	match2=re.compile('"playlist":\[{"url":"(.+?)"').findall(link)
	match1 = re.compile('"baseUrl":"(.+?)"').findall(link)

	title = re.compile('<meta property="og:title" content="(.+?)"').findall(link)

	if match2 != [] and match1 != []:
		stream=match1[0]+"/"+match2[0]
		stream=stream[:stream.rfind('/')]+'/master.m3u8'
		if title != []:
			videotitle = title[0]
		else:
			videotitle = 'MRT Video'
		pDialog.update(70, 'Playing')
		playurl(stream)
		pDialog.close()

	return True

def playurl(url):
	if name == '':
		guititle = 'Video'
	else:
		guititle = name

	if url[:4] == 'rtmp':
		url = url + ' timeout=10'

	listitem = xbmcgui.ListItem(guititle)
	play=xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
	play.clear()
	play.add(url, listitem)
	player = xbmc.Player(xbmc.PLAYER_CORE_AUTO)
	player.play(play)
	return True

def readurl(url):
	if url==urllib.unquote(url):
		quoted_url=urllib.quote(url).replace('%3A', ':')
	else:
		quoted_url=url
	req = urllib2.Request(quoted_url)
	req.add_header('User-Agent', user_agent)
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()
	return link
	
def PROCESS_PAGE(page,url='',name=''):

	if page == None:
		listing = mrtfrontList()
		for url,channel in listing:
			addDir(channel, 'list_mrtchannel', url, '')
		addDir('ВО ЖИВО', 'list_mrtlive', '', '')

		setView()
		xbmcplugin.endOfDirectory(int(sys.argv[1]))

	elif page == 'list_mrtlive':
		listing = list_mrtlive()
		for url,title,thumb in listing:
			addLink(title, url, 'play_mrt_video', thumb)

		setView()
		xbmcplugin.endOfDirectory(int(sys.argv[1]))

	elif page == 'list_mrtchannel':
		listing = list_mrtchannel(url)
		for type,url,thumb,duration,title in listing:
			if type=="video":
				addLink(title, url, 'play_mrt_video', thumb, '', duration)
			elif type=="channel":
				addDir(">>  "+title, 'list_mrtchannel', url, thumb)

		setView()
		xbmcplugin.endOfDirectory(int(sys.argv[1]))

	elif page == 'play_mrt_video':
		playmrtvideo(url)
		
def addLink(name,url,page,iconimage,fanart='',duration='00:00', published='0000-00-00', description=''):
        ok=True
	if page != '':
		u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&page="+str(page)+"&name="+urllib.quote_plus(name)
	else:
		u=url
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )

	if duration != '00:00':
		liz.setInfo('video', { 'Duration':duration })

	if published != '0000-00-00':
		liz.setInfo('video', {'Aired':published})

	if description != '':
		liz.setInfo('video', { 'plot':description })

	#liz.setProperty('IsPlayable', 'false')
	if fanart!='':
		liz.setProperty('fanart_image', fanart)
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)
        return ok

def addDir(name,page,url,iconimage,fanart=''):
        u=sys.argv[0]+"?page="+urllib.quote_plus(page)+"&url="+urllib.quote_plus(url)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
	if fanart!='':
		liz.setProperty('fanart_image', fanart)
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok

params=get_params()
url=None
name=None
page=None

old_version = ''

if os.path.isfile(VERSION_FILE):
	old_version = fread(VERSION_FILE)

if old_version != __version__:
	result = registerVersion(__version__)
	#result = True
	if result:
		fwrite(VERSION_FILE, __version__)
result = True

try:
        url=urllib.unquote_plus(params["url"])
except:
        pass

try:
        name=urllib.unquote_plus(params["name"])
except:
        pass

try:
	page=urllib.unquote_plus(params["page"])
except:
        pass

if result:
	PROCESS_PAGE(page, url, name)
