#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import urllib.request
import re
import html
import sys
import os
import datetime

from PySide2.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QVBoxLayout
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QLabel
from PySide2.QtWidgets import QMessageBox
from PySide2.QtCore import QFile

class Form(QDialog):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        #QMessageBox.warning(self, self.tr("My Application"), self.tr("The document has been modified.\nDo you want to save your changes?"))
        file = QFile("forms/url2corpus.ui")
        file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.w = loader.load(file)
        layout = QVBoxLayout()
        layout.addWidget(self.w)
        self.setLayout(layout)
        self.w.accepted.connect(self.isaccepted)
        self.w.rejected.connect(self.isrejected)
        self.setWindowTitle("Estrai corpus da sito web")

        #there are a few urls we should ignore
        self.ignore = ['quotidiano.repubblica.it', 'rep.repubblica.it', 'trovacinema.repubblica.it', 'miojob.repubblica.it', 'racconta.repubblica.it', 'video.repubblica.it', 'www.repubblica.it/economia/miojob/', 'facebook.com', 'google.com', 'yahoo.com', 'twitter.com', 'ansa.it/games/', 'ansa.it/meteo/', 'ansa.it/nuova_europa/', 'corporate.ansa.it', 'filmalcinema.shtml', 'trovacinema', 'splash.repubblica.it', 'd.repubblica.it/ricerca', 'video.d.repubblica.it', 'finanza.repubblica.it', '/static/servizi/']

        self.useragent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'

        self.thisurl = ""
        self.visited = []
        self.visitedfile = ""
        self.firstrun = True
        self.vdb = []
        self.vdbfile = ""

    def find_between(s, first, last ):
        try:
            start = 0
            if first != "":
                start = s.index( first ) + len( first )
            end = len(s)-1
            if last != "":
                end = s.index( last, start )
            return s[start:end]
        except ValueError:
            return ""

    def geturl(thisurl):
        #global useragent
        if thisurl == '':
            return ''
        req = urllib.request.Request(
            thisurl,
            data=None,
            headers={
                'User-Agent': self.useragent
            }
        )

        thishtml = ""
        try:
            f = urllib.request.urlopen(req)
            ft = f.read()
        except:
            ft = ""
        try:
            encoding = f.info().get_content_charset() #f.headers.get_content_charset()
            if encoding == None:
                encoding = 'windows-1252'
            thishtml = ft.decode(encoding)
            print(encoding)
        except:
            try:
               thishtml = ft.decode('utf-8', 'backslashreplace')
            except:
               thishtml = str(ft)
        try:
            thishtml = html.unescape(thishtml)
        except:
            thishtml = ""
        return thishtml


    def cleanRepubblica(thishtml):
        #look for known article delimiters
        start = ['<div class="body-text".*?>', '<div class="entrytext".*?>', '<div class="post-entry".*?>', '<div class="entry-content".*?>', '<div class="article-maincolblog".*?>', '<div class="detail-articles".*?>', '<div class="entry".*?>']
        end = ['<div id="fb-facepile">','<p class="dettagliotag">', '<footer', '<p class="postmetadata">', '<!-- fine TESTO -->', '<div class=\'sociable\'>']
        cs = 0
        ce = 0
        for i in range(len(start)):
            if (bool(re.search(start[i], thishtml))):
                cs = i
        for i in range(len(end)):
            if (bool(re.search(end[i], thishtml))):
                ce = i
        #if we didn't find delimitier, this is an unknown article type so we stop here
        indexes = [(m.start(0), m.end(0)) for m in re.finditer(start[cs], thishtml)]
        if len(indexes)<1:
            return ""
        ns = indexes[0][1]
        indexes = [(m.start(0), m.end(0)) for m in re.finditer(end[ce], thishtml)]
        if len(indexes)<1:
            return ""
        ne = indexes[0][0]
        #get only the article
        if ns < 0 or ne < 0:
            return ""
        thishtml = thishtml[ns:ne]

        #remove photogalleries
        start = re.escape('<div class="snappedPlaceholder"')
        end = re.escape('</div>')
        thishtml = re.sub(start+".*?"+end, "", thishtml, flags=re.DOTALL)

        #remove share buttons
        start = re.escape('<span class="gs-share-count-text">')
        end = re.escape('</span>')
        thishtml = re.sub(start+".*?"+end, "", thishtml, flags=re.DOTALL)

        #remove twitter feed
        start = re.escape('<blockquote class="twitter-tweet"')
        end = re.escape('</blockquote>')
        thishtml = re.sub(start+".*?"+end, "", thishtml, flags=re.DOTALL)

        return thishtml

    def cleanRepubblicaSearch(thishtml):
        #look for known article delimiters
        start = ['<section id="lista-risultati">']
        end = ['<!-- /risultati -->']
        cs = 0
        ce = 0
        for i in range(len(start)):
            if (bool(re.search(start[i], thishtml))):
                cs = i
        for i in range(len(end)):
            if (bool(re.search(end[i], thishtml))):
                ce = i
        #if we didn't find delimitier, this is an unknown article type so we stop here
        indexes = [(m.start(0), m.end(0)) for m in re.finditer(start[cs], thishtml)]
        if len(indexes)<1:
            return ""
        ns = indexes[0][1]
        indexes = [(m.start(0), m.end(0)) for m in re.finditer(end[ce], thishtml)]
        if len(indexes)<1:
            return ""
        ne = indexes[0][0]
        #get only the search results
        if ns < 0 or ne < 0:
            return ""
        thishtml = thishtml[ns:ne]

        return thishtml

    def cleanAnsa(thishtml):
        #look for known article delimiters
        start = ['<div itemprop="articleBody".*?>']
        end = ['<div id="relatedMobile"']
        cs = 0
        ce = 0
        for i in range(len(start)):
            if (bool(re.search(start[i], thishtml))):
                cs = i
        for i in range(len(end)):
            if (bool(re.search(end[i], thishtml))):
                ce = i
        #if we didn't find delimitier, this is an unknown article type so we stop here
        indexes = [(m.start(0), m.end(0)) for m in re.finditer(start[cs], thishtml)]
        if len(indexes)<1:
            return ""
        ns = indexes[0][1]
        indexes = [(m.start(0), m.end(0)) for m in re.finditer(end[ce], thishtml)]
        if len(indexes)<1:
            return ""
        ne = indexes[0][0]
        #get only the article
        if ns < 0 or ne < 0:
            return ""
        thishtml = thishtml[ns:ne]

        return thishtml

    def cleanGeneric(thishtml):

        #clean headers
        thishtml = re.sub("<h[0-9].*?<\/h[0-9]>", "", thishtml, flags=re.DOTALL)

        #clean links
        repl = ""
        if 1==1:
            repl = "\g<1>"#NOTE \g<\> is equal to \1, meaning group 1, but it's less ambiguous
        thishtml = re.sub("<[aA]\s.*?>(.*?)<\/[aA]>", repl, thishtml, flags=re.DOTALL)

        #clean js and css
        thishtml = re.sub("<script.*?<\/script>", "", thishtml, flags=re.IGNORECASE|re.DOTALL)
        thishtml = re.sub("<style.*?<\/style>", "", thishtml, flags=re.IGNORECASE|re.DOTALL)

        #remove strong tag if in caps lock
        thishtml = re.sub("<strong>[^a-z]+?<\/strong>", "", thishtml)

        #clean all useless symbols
        mysymbols = re.escape('+*#')
        thishtml = re.sub("["+mysymbols+"]", "", thishtml)

        #clean all tags (NOTE: DOTALL means that . matches every characters including \n)
        thishtml = re.sub("<.*?>", "", thishtml, flags=re.DOTALL)

        #remove all empty lines
        #stripped = [line for line in thishtml.split('\n') if line.strip() != '']
        #thishtml = "".join(stripped)
        nl = '\n' #switch to ' ' if you don't want paragraph separation
        stripped = ""
        for line in thishtml.split('\n'):
            if line.strip() != '':
                for word in line.split():
                    #it's a good idea to check if at least a few words in every lines belong to the vdb
                    if word in vdb or len(vdb)<1:
                        stripped = stripped + line + nl
                        break
        thishtml = stripped

        #remove double spaces
        while (bool(re.search('\s\s', thishtml))):
            thishtml = re.sub("\s\s", " ", thishtml)

        #remove initial spaces
        thishtml = re.sub("^\s", "", thishtml)
        thishtml = re.sub("^\s*?-", "", thishtml)
        thishtml = re.sub("^(di)\s", "", thishtml)

        #delete spaces at the end of the lines, then delete line if it does not end with a dot
        stripped = ""
        for line in thishtml.split('\n'):
            line = re.sub("\s*?$", "", line)
            if len(line)<200 and bool(re.match('.*?[\.,;\?!]$', line))==False:
                line = ''
            stripped = stripped + line + nl
        thishtml = stripped

        return thishtml

    def getLinks(thishtml):
        #regex = "<[aA] .*?href=\"(http.*?|\/.*?)\".*?<\/[aA]>"
        regex = ".*?href=[\"'](.*?)[\"']"
        links = [m.group(1) for m in re.finditer(regex, thishtml, flags=re.DOTALL)]
        return links

    def getSearchLinks(thishtml):
        links = [m.group(1) for m in re.finditer("<a .*?href=\"(http.*?|\/.*?)\".*?title=.*?<\/a>", thishtml, flags=re.DOTALL)]
        return links

    def getRSSLinks(thishtml):
        links = [m.group(1) for m in re.finditer("<link>.*?(http.*?)(\]\]>)*?<\/link>", thishtml, flags=re.DOTALL)]
        return links

    def url2name(thisurl):
        myname = re.sub(re.escape('http://'), "", thisurl)
        myname = re.sub(re.escape('https://'), "", myname)
        #myname = re.sub("\?.*$", "", myname)
        myname = re.sub("[\\\/\.\?&]", "-", myname)
        if len(myname)>200:
            myname = myname[0:200]
        myname = myname + ".txt"
        return myname

    def runOnPage(thisurl, output = ""):
        global ignore

        firstrun = False
        thishtml = geturl(thisurl)
        links = getLinks(thishtml)
        m = re.match(r"(http.*?\..*?)(\/|$)", thisurl)
        baseurl = m.group(1)
        for i in range(len(links)):
            if links[i][0] == '/':
                links[i] = baseurl + links[i]
            if links[i][:5] != 'http:' and links[i][:6] != 'https:':
                links[i] = baseurl + "/" + links[i]
            print(links[i])
            if links[i] == thisurl:
                links[i] = ''
            else:
                for ii in range(len(ignore)):
                    if ignore[ii] in links[i]:
                        links[i] = ''
        for ii in range(len(ignore)):
            if ignore[ii] in thisurl:
                return []
        #cleaning for Repubblica.it
        if 'repubblica.it' in thisurl:
            if 'rss2.0.xml' in thisurl:
                links = getRSSLinks(thishtml)
                return links
            thishtml = cleanRepubblica(thishtml)
        #cleaning for ANSA.it
        if 'ansa.it' in thisurl:
            if 'rss.xml' in thisurl:
                links = getRSSLinks(thishtml)
                return links
            thishtml = cleanAnsa(thishtml)
        thishtml = cleanGeneric(thishtml)
        if output == "":
            print(thishtml)
        else:
            fname = output + "/" + url2name(thisurl)
            if thishtml != "":
                text_file = open(fname, "w")
                text_file.write(thishtml)
                text_file.close()
        return links

    def runRecursive(thisurl, output = ""):
        #global visited
        #before going on, check if we previously worked on this page
        m = re.match(r"http.*?\.(.*?)(\/|$)", thisurl)
        baseurl = m.group(1)
        fname = output + "/" + url2name(thisurl)
        if os.path.isfile(fname) == False or firstrun:
            #if re.sub("\?.*$", "", thisurl) not in visited:
            if thisurl not in visited:
                links = runOnPage(thisurl, output)
                self.visited.append(thisurl)
            else:
                links = []
            #look for every link in the page with the same starting url (up to the first /)
            for i in range(len(links)):
                m = re.match(r"http.*?:\/\/(.*?)(\/|$)", links[i])
                lbaseurl = ''
                if m:
                    lbaseurl = m.group(1)
                if re.sub("\?.*$", "", links[i]) not in visited and baseurl in lbaseurl:
                    print(links[i])
                    with open(self.visitedfile, "a") as myfile:
                        myfile.write(links[i]+"\n")
                    runRecursive(links[i],output)

    def runSearchRepubblica(thisquery, output, fromdate, todate):
        query = thisquery.replace('RICERCAREPUBBLICA:','')
        if query == '':
            query = '+'
        query = query.replace(' ','+')
        #we are not allowed to get more than 250 pages
        for npage in range(250):
            #http://ricerca.repubblica.it/ricerca/repubblica-it?author=&sortby=adate&query=+&fromdate=2000-10-01&todate=2018-05-22&mode=all&page=1
            thisurl = 'http://ricerca.repubblica.it/ricerca/repubblica-it?author=&sortby=adate&query=' +query +'&fromdate='+fromdate+'&todate='+todate+'&mode=all&page='+str(npage)
            thishtml = geturl(thisurl)
            thishtml = cleanRepubblicaSearch(thishtml)
            links = getSearchLinks(thishtml)
            #m = re.match(r"(http.*?\..*?)(\/|$)", 'http://www.repubblica.it')
            baseurl = 'http://www.repubblica.it' #m.group(1)
            alllinks = []
            articlesfile = output + "/articles.tmp"
            if os.path.isfile(articlesfile):
                alllinks = [line.rstrip('\n') for line in open(articlesfile)]
            for i in range(len(links)):
                if links[i][0] == '/':
                    links[i] = baseurl+ links[i]
                if links[i] not in alllinks and 'www.repubblica.it/?ref=search' not in links[i] and 'ricerca.repubblica.it' not in links[i]:
                    fname = output + "/" + url2name(links[i])
                    if os.path.isfile(fname) == False:
                        print(links[i])
                        pagehtml = geturl(links[i])
                        pagehtml = cleanGeneric(pagehtml)
                        if pagehtml != "":
                            text_file = open(fname, "w")
                            text_file.write(pagehtml)
                            text_file.close()
                            alllinks.append(links[i])
                            with open(articlesfile, "a") as myfile:
                                myfile.write(links[i]+"\n")

    def do_search(self,):
        if len(sys.argv)>1:
            thisurl = sys.argv[1]
            vdbfile = os.path.abspath(os.path.dirname(sys.argv[0]))+"/vdb2016.txt"
            if os.path.isfile(vdbfile):
                vdb = [line.rstrip('\n') for line in open(vdbfile)]
            if len(sys.argv)>4:
                if sys.argv[4] == "-novdb":
                    vdb = []
            if 'RICERCAREPUBBLICA:' in thisurl:
                fromdate = '2000-01-01'
                todate = datetime.datetime.now().strftime('%Y-%m-%d')
                if len(sys.argv)>3 and len(sys.argv[3].split('-'))==3:
                    fromdate = sys.argv[3]
                if len(sys.argv)>2 and os.path.isdir(sys.argv[2]):
                    output = sys.argv[2]
                    fromyear = int(fromdate.split('-')[0])
                    frommonth = int(fromdate.split('-')[1])
                    toyear = int(todate.split('-')[0])
                    for iy in range(1+toyear-fromyear):
                        for im in range(13-frommonth):
                            nfromdate = str(fromyear+iy)+'-'+str(frommonth+im).zfill(2) +'-01'
                            print(nfromdate)
                            fdatefile = output + "/fromdate.tmp"
                            with open(fdatefile, "a") as myfile:
                                myfile.write(str(nfromdate)+"\n")
                            runSearchRepubblica(thisurl, output, nfromdate, todate)
                        frommonth = 1
                    sys.exit()
                else:
                    sys.exit()
        else:
            print('USAGE: ./url2corpus.py URL ./corpus/ -r')
            print('Example URLS:\n http://www.repubblica.it/esteri/2018/05/18/news/aereo_incidente_schianto_cuba_decollo-196760241/\n https://www.ansa.it/sito/notizie/politica/2018/05/14/governo-di-maio-e-salvini-al-colle-nel-pomeriggio.-resta-nodo-premier_308ebf3c-4e34-4251-876c-9c9d83606e91.html\n http://www.repubblica.it/rss/homepage/rss2.0.xml\n http://www.ansa.it/sito/notizie/cronaca/cronaca_rss.xml\nYou can also download from Repubblica.it search engine:\n ./url2corpus.py "RICERCAREPUBBLICA:" ./corpus-ricerche/ 2000-01-01\nin this case the last argument should be the date from which you want to start downloading (YYYY-MM-DD). In the first argument you can specify a search query after the double mark.\nIf you append -novdb option after -r, then the VdB will not be used.')
            sys.exit()
        output = ""
        if len(sys.argv)>2 and os.path.isdir(sys.argv[2]):
            output = sys.argv[2]
        if len(sys.argv)>3:
            if sys.argv[3] == "-r" and output != "":
                visitedfile = output + "/visited.tmp"
                if os.path.isfile(visitedfile):
                    visited = [line.rstrip('\n') for line in open(visitedfile)]
                #here we cycle for all the urls we can find
                print("I'm scanning the URL recursively looking for other pages to download. This is going to be endless (I mean it). When you are tired, just hit Ctrl+C.")
                runRecursive(thisurl, output)
        else:
            runOnPage(thisurl, output)


    def isaccepted(self):
            self.accept()
    def isrejected(self):
            self.reject()