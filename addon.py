# -*- coding: utf-8 -*-

# Debug
Debug = False

# Imports
import urllib, urllib2
import xbmc, xbmcgui, xbmcplugin, xbmcaddon
from xml.sax import saxutils
from BeautifulSoup import BeautifulStoneSoup as BSS, SoupStrainer, BeautifulSOAP

__settings__ = xbmcaddon.Addon(id='plugin.video.medici.tv')
__plugin__ = __settings__.getAddonInfo('name')
__version__ = __settings__.getAddonInfo('version')
__icon__ = __settings__.getAddonInfo('icon')
__language__ = __settings__.getLocalizedString

API_URL = 'http://www.medici.tv/api/'
MAIN_URL = 'http://www.medici.tv/'
CATALOG_MENU_URL = 'http://www.medici.tv/api/menu/catalog/'
CATALOG_URL = 'http://www.medici.tv/api/catalog/%s/'

class Main:
  def __init__(self):
    if ("action=play" in sys.argv[2]):
      self.PLAY(self.Arguments('url'))
    elif ("action=list" in sys.argv[2]):
      self.LIST(self.Arguments('id'))
    elif ("action=subdirectories" in sys.argv[2]):
      self.subSTART(self.Arguments('id'))
    else:
      self.START()

  def START(self):
    if Debug: self.LOG('\nSTART function')
    xml = urllib2.urlopen(CATALOG_MENU_URL).read()
    BSS.NESTABLE_TAGS['item'] = []
    soup = BSS(xml, parseOnlyThese=SoupStrainer('result'))
    for i in soup.menu.findChildren('item', recursive=False):
      title = i.findChild('title', recursive=False).string
      id = i.findChild('tags', recursive=False).id.string
      action = 'list'
      if len(i.tags.findAll('title')) > 1:
        id = i.findChild('id', recursive=False).string
        action = 'subdirectories'
      listitem = xbmcgui.ListItem(title, iconImage="DefaultFolder.png", thumbnailImage=__icon__)
      parameters = '%s?action=%s&id=%s' % (sys.argv[0], action, id)
      xbmcplugin.addDirectoryItems(int(sys.argv[1]), [(parameters, listitem, True)])
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.endOfDirectory(int(sys.argv[1]), True)

  def subSTART(self, catid):
    if Debug: self.LOG('\nsubSTART function\ncatid: %s' % catid)
    xml = urllib2.urlopen(CATALOG_MENU_URL).read()
    BSS.NESTABLE_TAGS['item'] = []
    soup = BeautifulSOAP(xml).find('item', {'id':catid})
    #TODO: totalItems for addDirectoryItems
    for i in soup.findAll('item'):
      id = i['id']
      title = i['title'].encode('utf-8').replace('&amp;', '&')
      print title, id
      listitem = xbmcgui.ListItem(title, iconImage="DefaultFolder.png", thumbnailImage=__icon__)
      parameters = '%s?action=list&id=%s' % (sys.argv[0], id)
      xbmcplugin.addDirectoryItems(int(sys.argv[1]), [(parameters, listitem, True)])
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.endOfDirectory(int(sys.argv[1]), True)

  def LIST(self, id):
    if Debug: self.LOG('\nLIST function\nURL: %s' % (CATALOG_URL % id))
    url = urllib2.urlopen(CATALOG_URL % id).read()
    soup = BSS(url, fromEncoding='utf-8')
    title = soup.control.title.string
    url = soup.control.parent.string
    first_page = soup.page.first_page.string
    last_page = soup.page.last_page.string
    path = API_URL + soup.page.path_prefix.string
    link = path + '%d/'
    for i in range(int(first_page), int(last_page) + 1):
      pages = urllib2.urlopen(link % i).read()
      soup = BSS(pages)
      for x in soup.findAll('item'):
        if x.play_path.string == None:
          if x.preview_path.string == None:
            title = x.title.string + ' - [[COLOR=FFFF0000]No Video[/COLOR]]' # RED
            url = ''
            rating = 'No Video'
          else:
            title = x.title.string + ' - [[COLOR=ffFFFF00]Preview[/COLOR]]' # YELLOW
            url = API_URL + x.preview_path.string
            rating = 'Preview'
        else:
          title = x.title.string + ' - [[COLOR=ff00FF00]Full[/COLOR]]' # GREEN
          url = API_URL + x.play_path.string
          rating = 'Full'
        if x.line1.string == None:
          desc = ''
        else:
          desc = x.line1.string
        if x.line2.string == None:
          desc += ''
        else:
          desc += ' %s' % x.line2.string
        if x.line3.string == None:
          desc += ''
        else:
          desc += ' %s' % x.line3.string
        id = x.id.string
        if x.image.string == None:
          thumb = ''
        else:
          thumb = MAIN_URL + x.image.string

        listitem = xbmcgui.ListItem(title, iconImage="DefaultVideo.png", thumbnailImage=thumb)
        # set the key information
        listitem.setInfo('video', {'title' : title,
                                   'label' : title,
                                   'plot' : desc,
                                   'PlotOutline' : desc,
                                   'mpaa': rating })
        parameters = "%s?action=play&url=%s" % (sys.argv[0], urllib.quote_plus(url))
        xbmcplugin.addDirectoryItems(int(sys.argv[1]), [(parameters, listitem, False)])
    # content type...
    xbmcplugin.setContent(int(sys.argv[1]), 'musicvideos')
    # sorting methods...
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_MPAA_RATING)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    # End of directory...
    xbmcplugin.endOfDirectory(int(sys.argv[1]), True)


  def PLAY(self, url):
    if Debug: self.LOG('\nPLAY function\nURL: %s' % url)
    url = urllib2.urlopen(url).read()
    soup = BSS(url)
    stream = soup.video.remote.stream.string
    #title = soup.video.title.string
    smil = BSS(urllib2.urlopen(stream).read())
    rtmp = smil.meta['base']
    video = smil.video['src']
    swfUrl = 'http://medici.tv/medici.swf'

    #"rtmpdump -r %s --swfUrl http://medici.tv/medici.swf --tcUrl '%s' --playpath '%s' -o '%s.mp4'" % (rtmp, rtmp, saxutils.unescape(video), saxutils.unescape(title))

    # Get current list item details...
    title = unicode(xbmc.getInfoLabel("ListItem.Title"), "utf-8")
    thumbnail = xbmc.getInfoImage("ListItem.Thumb")
    plot = unicode(xbmc.getInfoLabel("ListItem.Plot"), "utf-8")

    # Build rtmp url...
    video_url = rtmp + ' swfUrl=' + swfUrl + ' tcUrl=' + rtmp + ' playpath=' + saxutils.unescape(video)
    if Debug: self.LOG('\nrtmp URL: %s' % video_url)

    # only need to add label, icon and thumbnail, setInfo() and addSortMethod() takes care of label2
    listitem = xbmcgui.ListItem(title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail)

    # set the key information
    listitem.setInfo('video', {'title': title,
                               'label' : title,
                               'plot': plot,
                               'plotoutline': plot, })

    # Play video...
    xbmc.Player().play(video_url , listitem)

  def Arguments(self, arg):
    Arguments = dict(part.split('=') for part in sys.argv[2][1:].split('&'))
    return urllib.unquote_plus(Arguments[arg])

  def LOG(self, description):
    xbmc.log("[ADD-ON] '%s v%s': '%s'" % (__plugin__, __version__, description), xbmc.LOGNOTICE)

if __name__ == '__main__':
  Main()
