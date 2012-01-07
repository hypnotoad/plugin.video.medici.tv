# -*- coding: utf-8 -*-

# Debug
Debug = False

# Imports
import urllib, requests, simplejson, shelve
import xbmc, xbmcgui, xbmcplugin, xbmcaddon
from xml.sax import saxutils
from requests.exceptions import RequestException
from BeautifulSoup import BeautifulStoneSoup as BSS, BeautifulSoup as BS, SoupStrainer, BeautifulSOAP

__addon__ = xbmcaddon.Addon(id='plugin.video.medici.tv')
__info__ = __addon__.getAddonInfo
__plugin__ = __info__('name')
__version__ = __info__('version')
__icon__ = __info__('icon')
__cachedir__ = __info__('profile')
__language__ = __addon__.getLocalizedString
__get_settings__ = __addon__.getSetting
__set_settings__ = __addon__.setSetting

MAIN_URL = 'http://www.medici.tv/'
AUTH_URL = 'http://www.medici.tv/ajax_login/'
_username = __get_settings__('username')
_password = __get_settings__('password')
_headers = {'Referer':'http://www.medici.tv/',
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Host':'www.medici.tv',
            'Accept' : 'application/json, text/javascript, */*; q=0.01'}

class Main:
  def __init__(self):
    if ('action=play' in sys.argv[2]):
      self.play(self.Arguments('url', True), self.Arguments('mode'))
    elif ('action=subcats' in sys.argv[2]):
      self.subcats(self.Arguments('title'))
    elif ('action=catalogue' in sys.argv[2]):
      self.cats(self.Arguments('page') + '/')
    elif ('action=list' in sys.argv[2]):
      try:
        self.list(self.Arguments('next_page') + '/')
      except:
        if self.Arguments('page').startswith('/live/previous'):
          self.list(self.Arguments('page') + '/')
        else:
          self.list(self.Arguments('page'))
    else:
      self.START()

  def START(self):
    if Debug: self.LOG('DEBUG: START()')
    category = [{'title':'Live', 'page':'/live/previous/', 'action':'list'},
                {'title':'Catalogue', 'page':'/films/', 'action':'catalogue'}]
    for i in category:
      listitem = xbmcgui.ListItem(i['title'], iconImage='DefaultFolder.png', thumbnailImage=__icon__)
      parameters = '%s?action=%s&page=%s' % (sys.argv[0], i['action'], i['page'] + '/')
      xbmcplugin.addDirectoryItems(int(sys.argv[1]), [(parameters, listitem, True)])
    # Sort methods and content type...
    xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_NONE)
    # End of directory...
    xbmcplugin.endOfDirectory(int(sys.argv[1]), True)

  def cats(self, page):
    if Debug: self.LOG('DEBUG: cats()')
    _json = simplejson.loads(self._get(page))
    soup = BS(_json['data'])
    for i in soup('div', 'spc-t spc-l spc-r')[0]('h2'):
      title = i.string
      listitem = xbmcgui.ListItem(title, iconImage="DefaultFolder.png", thumbnailImage=__icon__)

      parameters = '%s?action=subcats&title=%s' % (sys.argv[0], title)
      xbmcplugin.addDirectoryItems(int(sys.argv[1]), [(parameters, listitem, True)])
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.endOfDirectory(int(sys.argv[1]), True)

  def subcats(self, page):
    if Debug: self.LOG('DEBUG: subcats()')
    _json = simplejson.loads(self._get('/films/'))
    soup = BS(_json['data'].replace('<b>View all</b>', ''))
    if page == 'Categories': integer = 0
    elif page == 'Musical periods': integer = 2
    elif page == 'Performers': integer = 1
    if integer == 0 or integer == 2:
      for i in soup('div', 'bck-1 spc-t spc-l spc-r')[integer]('a'):
        title = i.string
        directory = i['href'].split('#!')[1]
        listitem = xbmcgui.ListItem(title, iconImage="DefaultFolder.png", thumbnailImage=__icon__)
        parameters = '%s?action=list&page=%s' % (sys.argv[0], directory)
        xbmcplugin.addDirectoryItems(int(sys.argv[1]), [(parameters, listitem, True)])
    elif integer == 1:
      for i in soup('div', 'bck-1 spc-t spc-l spc-r')[integer]('b'):
        title = i('a')[0].string
        directory = i('a')[0]['href'].split('#!')[1]
        listitem = xbmcgui.ListItem(title, iconImage="DefaultFolder.png", thumbnailImage=__icon__)
        parameters = '%s?action=list&page=%s' % (sys.argv[0], directory)
        xbmcplugin.addDirectoryItems(int(sys.argv[1]), [(parameters, listitem, True)])
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.endOfDirectory(int(sys.argv[1]), True)

  def list(self, page):
    if Debug: self.LOG('DEBUG: list()')
    _json = simplejson.loads(self._get(page))
    if page.startswith('/baroque') or \
       page.startswith('/classicism') or \
       page.startswith('/romantism') or \
       page.startswith('/piano') or \
       page.startswith('/singer') or \
       page.startswith('/violin') or \
       page.startswith('/instrument-cello') or \
       page.startswith('/conducting'):
      _soup = BS(_json['data'], parseOnlyThese=SoupStrainer('div', 'list-small'))
      totalitems = len(_soup('div', 'block_media small spc-t'))
      soup = _soup('div', 'block_media small spc-t')
    elif page.startswith('/live/previous/'):
      _soup = BS(_json['data'], parseOnlyThese=SoupStrainer('table', 'tbl_live bck-1'))
      #remove unneded lines.
      comments = _soup.findAll('a', 'button3 flt-r')
      [comment.extract() for comment in comments]
      totalitems = len(_soup('td', 'info'))
      soup = _soup('td', 'info')
    else:
      _soup = BS(_json['data'], parseOnlyThese=SoupStrainer('div', 'list-medium'))
      totalitems = len(_soup('div', 'block_media spc-t'))
      soup = _soup('div', 'block_media spc-t')
    try:
      next_page = BS(_json['data']).find('div', 'next').a['href'].split('#!')[1]
      pagination = True
    except:
      pagination = False
    for i in soup:
      if i.a:
        folders = i('a')[0]['href'].split('#!')[1]
        try:
          if Debug: self.LOG('DEBUG: Trying to read from cache!')
          s = shelve.open(xbmc.translatePath(__cachedir__) + '/medici.db')
          try:
            entry = s[str(folders)]
          finally:
            s.close()
        except:
          if Debug: self.LOG('DEBUG: Not cached! Get from website!')
          entry = self._details(folders)
        title = entry['title']
        desc = entry['description']
        fanart = entry['fanart']
        quality = __get_settings__('quality')
        if quality == '0':
          video = entry['video_low']
        if quality == '1':
          video = entry['video_mid']
        if quality == '2':
          if entry['video_high'] == '':
            video = entry['video_mid']
            if Debug: self.LOG('DEBUG: high video quality is not found. Revert to mid quality!')
          else:
            video = entry['video_high']
        try:
          mode = entry['mode']
        except:
          mode = ''

        if Debug: self.LOG('DEBUG:\n\tfolder: %s\n\ttitle: %s\n\tdescription: %s\n\tvideo: %s\n\tfanart: %s\n\tmode: %s\n' % \
                           (folders, title, desc, video, fanart, mode))
        listitem = xbmcgui.ListItem(title, iconImage="DefaultFolder.png", thumbnailImage=fanart)
        listitem.setProperty('fanart_image', fanart)
        # set list information
        listitem.setInfo('video', {'title' : title,
                                   'label' : title,
                                   'plot' : desc,
                                   'PlotOutline' : desc, })
        if mode == '' or video == '':
          parameters = '%s' % (sys.argv[0])
        else:
          parameters = '%s?action=play&url=%s&mode=%s' % (sys.argv[0], urllib.quote_plus(video), mode)
        xbmcplugin.addDirectoryItems(int(sys.argv[1]), [(parameters, listitem, False)], totalitems)
      else:
        pass
    if pagination:
      listitem = xbmcgui.ListItem('Next Page >>', iconImage='DefaultVideo.png', thumbnailImage=__icon__)
      parameters = '%s?action=list&next_page=%s' % (sys.argv[0], next_page)
      xbmcplugin.addDirectoryItem(int(sys.argv[1]), parameters, listitem, True)
    xbmcplugin.setContent(int(sys.argv[1]), 'musicvideos')
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.endOfDirectory(int(sys.argv[1]), True)

  def _details(self, page):
    if Debug: self.LOG('DEBUG: _details()')
    details = {}
    _json = simplejson.loads(self._get(page))
    details['description'] = _json['meta_description'].strip().replace('\r\n\r\n', ' ')
    try:
      details['fanart'] = _json['main_image']
    except:
      details['fanart'] = ''
    details['title'] = title = _json['title']
    video = _json['video']
    if video != None:
      try:
        details['mode'] = video['mode']
      except:
        details['mode'] = ''
      if video['qualities']:
        video_qualities = video['qualities']
        details['video_low'] = video_qualities['url_1']
        details['video_mid'] = video_qualities['url_2']
        try:
          details['video_high'] = video_qualities['url_3']
        except:
          details['video_high'] = ''
      if video['tiny_type'] == 'full':
        details['title'] = '%s - %s' % (title, '[[COLOR=ff00FF00]Full[/COLOR]]')
      else:
        details['title'] = '%s - %s' % (title, '[[COLOR=ffFFFF00]Teaser[/COLOR]]')
    else:
      details['title'] = '%s - %s' % (title, '[[COLOR=FFFF0000]Not Availible[/COLOR]]')
      details['video_low'] = details['video_mid'] = details['video_high'] = ''
    if Debug: self.LOG('DEBUG: Adding to cache!')
    self._cache(page, details)
    return details

  def play(self, page, mode=''):
    if Debug: self.LOG('DEBUG: _play()\nurl: %s' % page)
    # Get current list item details...
    title = unicode(xbmc.getInfoLabel("ListItem.Title"), "utf-8")
    thumbnail = xbmc.getInfoImage("ListItem.Thumb")
    plot = unicode(xbmc.getInfoLabel("ListItem.Plot"), "utf-8")

    if mode == 'smil':
      smil = BSS(self._get(page))
      rtmp = smil.meta['base']
      video = smil.video['src']
      swfUrl = 'http://medici.tv/medici.swf'
      # rtmpdump script for console use 
      rtmpdump = "rtmpdump -r %s --swfUrl http://medici.tv/medici.swf --tcUrl '%s' --playpath '%s' -o '%s.mp4'" % \
                  (rtmp, rtmp, saxutils.unescape(video), saxutils.unescape(title))
      # Build rtmp url...
      video_url = rtmp + ' swfUrl=' + swfUrl + ' tcUrl=' + rtmp + ' playpath=' + saxutils.unescape(video)
      if Debug: self.LOG('DEBUG: rtmp link details.\n\trtmp: %s\n\tswfUrl: %s\n\ttcUrl: %s\n\tplaypath: %s\n\trtmpdump: %s' % \
                         (rtmp, swfUrl, rtmp, saxutils.unescape(video), rtmpdump))
    elif mode == 'rtmp_daily':
      video_url = page.split('&rtmp=1')[0]
      if Debug: self.LOG('DEBUG: video link details.\n\turl: %s' % video_url)
    else:
      video_url = ''
      if Debug: self.LOG('DEBUG: no video link!')
      raise
    # only need to add label, icon and thumbnail, setInfo() and addSortMethod() takes care of label2
    listitem = xbmcgui.ListItem(title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail)
    # set listitem information
    listitem.setInfo('video', {'title': title,
                               'label' : title,
                               'plot': plot,
                               'plotoutline': plot, })
    # Play video...
    xbmc.Player().play(video_url , listitem)

  def _cache(self, key, value):
    if Debug: self.LOG('DEBUG: _cache()')
    s = shelve.open(xbmc.translatePath(__cachedir__) + '/medici.db')
    try:
      s[str(key)] = value
    finally:
      s.close()

  def _auth(self, username, password):
    if Debug: self.LOG('DEBUG: _auth()')
    data = {'username':username, 'password':password}
    r = requests.post(AUTH_URL, data=data, headers=_headers)
    try:
      if simplejson.loads(r.content)['success'] and \
         simplejson.loads(r.content)['is_authenticated'] == True:
        if Debug: self.LOG('DEBUG: saving cookies to settings.\n\tcontent: %s\n\tcookies: %s\n\tstatus: %s' % \
                           (r.content, r.cookies, r.status_code))
        __set_settings__('m_session', r.cookies['m_session'])
        return r.cookies
    except RequestException, e:
        self.LOG('DEBUG: Error on _auth()\n\texception: %s\n\tstatus: %s' % \
                 (e, r.status_code))

  def _get(self, page):
    if Debug: self.LOG('DEBUG: _get()')
    if page.endswith('.smil'):
      if Debug: self.LOG('DEBUG: get .smil file')
      r = requests.get(page)
    else:
      data = { 'json':'true',
               'page':page,
               # no idea how to get this value!
               'timezone_offset':'-120' }
      if __get_settings__('username') == '':
        if Debug: self.LOG('DEBUG: no username configured!')
        r = requests.post(MAIN_URL, data=data, headers=_headers)
      else:
        if Debug: self.LOG('DEBUG: cookies getting from settings!')
        cookies = dict(m_session=__get_settings__('m_session'))
        r = requests.post(MAIN_URL, data=data, headers=_headers, cookies=cookies)
      if simplejson.loads(r.content)['is_authenticated'] == False and \
         not __get_settings__('username') == '':
        if Debug: self.LOG('DEBUG: not authenticated. Tyring _auth()')
        r = requests.post(MAIN_URL, data=data, headers=_headers, cookies=self._auth(_username, _password))
    if Debug: self.LOG('DEBUG:\n\tcontent: %s\n\tcookies: %s\n\tstatus: %s' % \
                       (r.content, r.cookies, r.status_code))
    return r.content

  def Arguments(self, arg, unquote=False):
    Arguments = dict(part.split('=') for part in sys.argv[2][1:].split('&'))
    if unquote:
      return urllib.unquote_plus(Arguments[arg])
    else:
      return Arguments[arg]

  def LOG(self, description):
    xbmc.log("[ADD-ON] '%s v%s': %s" % (__plugin__, __version__, description.encode('ascii', 'ignore')), xbmc.LOGNOTICE)

if __name__ == '__main__':
  Main()
