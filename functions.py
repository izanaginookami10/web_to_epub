import requests
import cloudscraper
#due to ww denying requests with cloudflare. need to use cloudscraper
#as it works like requests and anti bot measures will most likely be present
#in the future in other websites as well, cloudscraper will be used 
import os
import zipfile
import re
import sys
from bs4 import BeautifulSoup

forbidden_filenames = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']

#PARSERS
ww = 'www.wuxiaworld.com'
rr = 'www.royalroad.com'
wp = 'wordpress'
bs = 'blogspot'
parsers = [ww, rr, wp, bs]
wp_sites = ['isekailunatic.com', 'defiring.com', 'shirusekai.com']
bs_sites = ['skythewood']

#CORE

def download(link, file_name):
    '''get content from provided link to a html file, ie download a webpage''' 
    s = cloudscraper.create_scraper()
    #using cloudscraper to bypass cloudflare bot check
    
    ua_edge = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36 Edg/84.0.522.59')
    headers = {'User-Agent': ua_edge,
    }
    #setting user agent as PC Edge browser to avoid getting low image res
    
    page = s.get(link, headers=headers).text 
    #get content from linked page and store it as text in var page
    with open(file_name, "w", encoding = "utf8") as html:
    #create a file in write mode, it will be a html one
        html.write(page)
        #write the content of var page onto the just created/opened file
    
    
def get_link_list(toc_html, link_list, flag, chapter_start, chapter_end, 
    parser):
    '''given a RoyalRoad toc, fill the link_list with its chapters link
    and return chapter_start and chapter_end for later use'''
    if parser == 'www.royalroad.com':
        toc = get_toc_rr(toc_html)
    elif parser == 'www.wuxiaworld.com':
        toc = get_toc_ww(toc_html)
    elif parser == 'wordpress':
        toc = get_toc_wp(toc_html)
    elif parser == bs:
        toc = get_toc_bs(toc_html)
        
    if flag.lower() == 'y':
        chapter_start = input('From which chapter do you want to start? ')
        chapter_end = input('Until which chapter? ')
        chapter_start, chapter_end = check_error_number(chapter_start, 
            chapter_end)
        #past newbie me made a list to get 2 values from function, just return
        #2 values. Oh, past silly me.
        if (not chapter_start or not chapter_end or
            (len(toc) - (int(chapter_end)-int(chapter_start)))<1):
            print('Chapters range not available. Retry with another one.')
            sys.exit()
        try:
            if int(chapter_start) == 0:
                chapter_start = '1'
                #temporarily fallback: in case the user want to start from 0
                #(if the series start with that), ie beginning, there shouldn't
                #be errors now
            for c in range(int(chapter_start)-1, int(chapter_end)):
                #range doesn't include the 2nd arg, but since c is going to be
                #the list index, which starts from 0 and thus is one digit behind
                #than the usual counting, it's correct (unless there is a 
                #chapter named 0 and user choose that one... 
                #need to implement some fallback code as well as the possibility
                #to put only one of the start or end and without the other, either
                #start from first available chapter or until the last
                link_list.append(toc[c]['href'])
        except:
            print('Chapters range not available. Retry with another one.')
            sys.exit()
    elif flag.lower() == 'n':
        for a in toc:
            link_list.append(a['href'])
            
 
    return chapter_start, chapter_end #maybe I should make them glob vars...
    
def clean(file_name_in, file_name_out, parser, info, imgs):
    '''takes html file from download function and give as output a cleaned
    version of it'''
    chapter, chapter_title = get_chapter_content(file_name_in, info, 
        parser, imgs)
        
    #in order to try to keep the original chapter formatting as much as possible,
    #the tags were substituted with -tag- and are now returned as tags
    if '-em-' in chapter:
        chapter = chapter.replace('-em-', '<em>').replace('-/em-', '</em>')
    if '-i-' in chapter:
        chapter = chapter.replace('-i-', '<i>').replace('-/i-', '</i>')
    if '-b-' in chapter:
        chapter = chapter.replace('-b-', '<b>').replace('-/b-', '</b>')
    if '-strong-' in chapter:
        chapter = chapter.replace('-strong-', '<strong>').replace('-/strong-', 
            '</strong>')
    
    #b4s' tag.text keeps '\n', so no need for a p_list (check prev vers)
    #the if sequence is to keep italic or bold formatting
    chapter = chapter.strip().split('\n')
    nav = ['Previous Chapter', 'Next Chapter', '|', 'Main Page', 'Toc',
        'Table of Content']
    last_line = chapter[-1]
    for i in nav:
        if i in last_line:
            last_line = last_line.replace(i, '')    
    chapter[-1] = last_line
    chapter = '\n'.join(chapter)
    #in case there are unnecessary prev, next chapters
    chapter = chapter.strip()
    #delete any excessive whitespace just to be safe
    chapter = chapter.replace('\n', '</p>\n\n<p>')
    #as we have to make an epub and thus use html format, after we've 
    #cleaned the chapter from all the useless stuff and tags, we put each
    #line within <p> tags by replacing each '\n' with a closing and opening
    #<p> tag, this will leave a missing opening tag at the beginning and a
    #closing tag at the end 
    
    img_tag = '-img-'
    if img_tag in chapter:
        chapter = chapter.replace('-img-', '<img src="').replace('-/img-',
            '">')
        parts = re.split('(<img.+>)', chapter.strip())
        og_filename_out = file_name_out
        og_chapter_title = chapter_title
        for part in parts:
            counter = 1
            img_counter = 1
            img_name = ' - illustration ' + str(img_counter)
            file_name_out = og_filename_out
            chapter_title = og_chapter_title
            #at next loops they would be edited by prev loops otherwise
            file_name_out = file_name_out.split('.')
            #parts with image will have "illustration (n)" while chapter
            #text parts just a number after their filenames/titles
            if '<img' in part:
                file_name_out[0] += img_name
            else:
                file_name_out[0] += '-' + str(counter)
            
            file_name_out = '.'.join(file_name_out)
            #edit file_name_out adding number for each part before the
            #.xhtml part
            
            if '<img' in part:
                chapter_title = chapter_title + img_name
            else:
                chapter_title = chapter_title + ' (' + str(counter) + ')'
            chapter = part
            
            #<opf:item id="cover" href="cover.jpg" media-type="image/jpeg"/>
            write_xhtml(file_name_out, chapter_title, chapter)
            
            if '<img' in part:
                img_counter += 1
            else:
                counter += 1
    else: 
        write_xhtml(file_name_out, chapter_title, chapter)
    
    #closed all tags and file, now we delete the file_name_in, ie raws
    os.remove(file_name_in)

def write_xhtml(file_name_out, chapter_title, chapter):
    '''write chapter to xhtml file'''
    with open(file_name_out, 'w', encoding='utf8') as xhtml:
        xhtml.write('<html xmlns="http://www.w3.org/1999/xhtml">')
        #epub xhtmls by convetion use the xhtml format
        xhtml.write('\n<head>')
        xhtml.write('\n<title>' + chapter_title + '</title>')
        xhtml.write('\n</head>')
        #after the xhtml attribute statement, we put the title, then the body
        xhtml.write('\n<body>')
        if '<img' not in chapter:
            xhtml.write('\n<h4><b>' + chapter_title + '</b></h4>')
            #no need to have title written in illustration pages
        xhtml.write('\n<p>' + chapter + '</p>')
        #we then insert the title and the chapter text with additional p tags
        xhtml.write('\n</body>')
        xhtml.write('\n</html>')

def get_chapter_content(file_name_in, info, parser, imgs):
    if parser == rr:
        chapter, chapter_title = find_chapter_content_rr(file_name_in, info)
    elif parser == ww:
        chapter, chapter_title = find_chapter_content_ww(file_name_in)
    elif parser == wp:
        chapter, chapter_title = find_chapter_content_wp(file_name_in)
    elif parser == bs:
        chapter, chapter_title = find_chapter_content_bs(file_name_in)

    chapter = get_imgs(chapter, imgs) 
    #get img filenames, download them and mark the tags in the html file
    
    tags = ['em', 'i', 'b', 'strong']
    #to keep as much formatting as possible, will insert tags markers
    #in order to restore them later
    chapter = str(chapter) 
    #BeautifulSoup.tag obj -> str object in order to use str.replace
    for tag in tags:
        otag = '<' + tag 
        ctag = '</' + tag
        mtag = '-' + tag + '-' #tag marker
        cmtag = '-/' + tag + '-' #closing tag marker
        if tag in chapter:
            chapter = chapter.replace(otag+'>', otag+'>'+mtag)
            #<tag> -> <tag>-tag-
            chapter = chapter.replace(ctag, cmtag+ctag)
            #</tag -> -/tag-</tag
    #img tags were marked with get_imgs() through tag.wrap(new_tag)
    
    chapter = BeautifulSoup(chapter, 'html.parser')
    #str obj -> BeautifulSoup obj again
    chapter = chapter.text

    return chapter, chapter_title

def get_imgs(chapter, imgs):
    '''append images filenames to given list (2nd arg), download them 
    and mark their tags in the html files'''
    
    chapter = str(chapter)
    chapter = BeautifulSoup(chapter, 'html.parser')
    #necessary to convert chapter from bs4.element.Tag to 
    #bs4.BeautifulSoup obj in order to add new p tag
    
    for img in chapter.findAll('img'): #find all img tags
        src = img['src'] #their source link/url
        if '?' in src: 
            #if they have '?' parts for different res, filter them out
            src = src.split('?', 1) #split with max 2 elements
            src = src[0] #keep only first part of url
        
        #download imgs
        i = requests.get(src).content #get img content
        filename = src.split('/')[-1] #get img filename 
        with open(filename, 'wb') as image:
            image.write(i) #download img 
        imgs.append(filename) #append img name to images list
        
        #wrap the img tags in chapter html with p tag to mark them 
        p = chapter.new_tag('p')
        p.string = '-img-' + filename + '-/img-'
        img.wrap(p)
    return chapter

def find_between(file):
    with open(file, 'r', encoding='utf8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    return soup.title.get_text(strip=True)
    #return the text of the title tag of a html file

def get_title_list(cleaned_html_files):
    
    title_list = []
    for f in cleaned_html_files:
        with open(f, 'r', encoding='utf8') as file:
            soup = BeautifulSoup(file, 'html.parser')
            title_list.append(soup.title.get_text(strip=True))
    return title_list

def generate(cleaned_html_files, novel_name, author, epub_name, imgs):
    #chapter_s and _e are starting and ending chapters
    epub_name = delete_forbidden_c(forbidden_filenames, epub_name)
    #delete any unallowed characters in epub filename
    
    print('Creating Epub file (0/4)...')
    epub = zipfile.ZipFile(epub_name, 'w')
    #create empty zip archive, as epub are essentially zip files
    
    epub.writestr('mimetype', 'application/epub+zip')
    #zipfile.writestr('namefile', 'chapter') 
    #create in epub a file named 'mimetype' which contain the string
    #application/epub+zip'. This file is the same for all epub files
    print('Creating Epub file (1/4)...'
        '\nmimetype created')
    
    epub.writestr('META-INF/container.xml', '<container version="1.0"'
        '\nxmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
        '\n<rootfiles>'
        '\n<rootfile full-path="OEBPS/Content.opf" '
        'media-type="application/oebps-package+xml"/>'
        '\n</rootfiles>'
        '\n</container>')
    #make file 'container.xml' in folder 'META-INF'. Same for every epub
    print('Creating Epub file (2/4)...'
        '\ncontainer.xml created'
        '\ncreating content.opf...')
    
    #content.opf is more complex and it will be like this
    index_tpl = '''
    <package version="3.1"
        xmlns="http://www.idpf.org/2007/opf">
        <metadata>
            %(metadata)s
        </metadata>
        <manifest>
            %(manifest)s
        </manifest>
        <spine>
            <itemref idref="toc" linear="no"/>
            %(spine)s
        </spine>
    </package>'''
    #keeping the "old school" f-strings istead of f'string' here because %(var)s
    #allows me to define the var later, which I can't seem to do with f'string'
    #it can obviously be easily fixed by changing the orders of the elements and
    #variables, but as I do not have deep knowledge about epubs, better to keep
    #the structure clear 
    
    #we need to fill %(metadata)s, %(manifest)s and %(spine)s
    #manifest and spine will be filled through a loop, so let's make empty 
    #vars to hold their contents
    manifest = ''
    spine = ''
    
    #metadata is the same but with few var data such as novelname and author
    metadata = f'''<dc:title xmlns:dc="http://purl.org/dc/elements/1.1/">
        {epub_name}</dc:title>'
        <dc:creator xmlns:dc="http://purl.org/dc/elements/1.1/" 
        xmlns:ns0="http://www.idpf.org/2007/opf" ns0:role="aut" 
        ns0:file-as="NaN">{author}</dc:creator>
        <meta xmlns:dc="http://purl.org/dc/elements/1.1/" 
        name="calibre:series" content="{novel_name}"/>'''
    
    #standard string at end of manafest string
    toc_manifest = ('<item href="toc.xhtml" id="toc" '
        'properties="nav" media-type="application/xhtml+xml"/>')
    
    for n, html in enumerate(cleaned_html_files):
        #enumerate(list) gives a tuple for each item in a list containing 
        #a number starting from 0 and the corresponding item ie (0, item0)
        basename = os.path.basename(html)
        #os.path.basename(path) return name of last path, ie
        #"python_work\Epub Converter\epub_converter.py" -> "epub_converter.py"
        manifest += (f'<item id="file_{str(n+1)}" href="{basename}" '
            'media-type="application/xhtml+xml"/>')
        spine += f'<itemref idref = "file_{str(n+1)}" />' 
        epub.write(html, "OEBPS/" + basename)
        #zipfile.write(file, filename) is different from .writestr(filename,
        #content): the former write an existing file to the zipfile with
        #'filename' as its name, while the latter create a new file
        
        #add cleaned chapter file (html) on the epub file in folder 'OEBPS' 
        #with 'basename' as filename
    
    if imgs: #if the imgs list isn't empty
        for img in imgs:
            if 'cover_' in img:
                cover = 'properties="cover-image"' #for cover image only
            else:
                cover = ''
            
            manifest += (f'<itemd id="{img}" {cover} href="{img}" '
                'media-type="image/jpeg"')
            #add images to manifest
            epub.write(img, "OEBPS/" + img)
            #write images files in epub file
            os.remove(img)
            #remove imgs from working folder
    #now we write the completed content.opf file onto the epub archive
    epub.writestr("OEBPS/Content.opf", index_tpl % {
        "metadata": metadata,
        "manifest": manifest + toc_manifest,
        "spine": spine, })
        #write first 'OPEBPS...' and then the index_tpl, substituting the
        #placeholder variables in the %()s with their filled counterparts
        
    print('Creating Epub file (3/4)...'
        '\ncontent.opf created')
        
    #content.opf is finished, now last file: ToC, which we divide into 3 
    #parts: start, of which we only need to fill the novelname, mid, of which 
    #we need to add the chapter titles and end, which is already good
    toc_start = ( 
'''<?xml version='1.0' encoding='utf-8'?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>%(novelname)s</title>
</head>
<body>
    <section class="frontmatter TableOfContents">
        <header>
            <h1>Contents</h1>
        </header>
        <nav id="toc" role="doc-toc" epub:type="toc">
            <ol>
                %(toc_mid)s
                %(toc_end)s''')
    #using %()s here for same reason as before: it allows me to define vars later
    
    toc_mid = ""
    toc_end = '''</ol></nav></section></body></html>'''
    for n, f in enumerate(cleaned_html_files):
        chapter = find_between(cleaned_html_files[n])
        chapter = str(chapter)
        toc_mid += f'''<li class="toc-Chapter-rw" id="num_{n}">
            <a href="{cleaned_html_files[n]}">{chapter}</a></li>''' 
    #for each file in the list 'html_files', find the respective title tag and
    #add to toc_mid the string while substituting the variable values
    
    #now we add the finished Toc flie to the epub/zip archive and close it
    #and delete the downloaded and cleaned html files now unnecessary
    epub.writestr("OEBPS/toc.xhtml", toc_start % {"novelname": novel_name,
        "toc_mid": toc_mid, "toc_end": toc_end})
        #write OEB... and the toc filled with the variables
    print('Creating Epub file (4/4)...'
        '\ntoc.xhtml created')
    
    epub.close()
    for x in cleaned_html_files:
        os.remove(x)
    print('Epub created'
        '\nFinished')


#PARSER
def parser_choice(toc_link):
    '''Will choose the parser by checking the toc_link'''
    parser_check = False
    for site in parsers:
        if site in toc_link:
            parser = site
            parser_check = True
            break
    if not parser_check:
        for site in wp_sites:
            if site in toc_link:
                parser = wp
                parser_check = True
                break
    if not parser_check:
        print('Site not yet compatible.')
        sys.exit()
    return parser

def get_info(parser, toc_html):
    if parser == ww:
        info = get_metadata_ww(toc_html)
    elif parser == rr:
        info = get_metadata_rr(toc_html)
    elif parser == wp:
        info = get_metadata_wp(toc_html)
    elif parser == bs:
        info = get_metadata_bs(toc_html)
    else:
        print('Site not yet compatible.')
        sys.exit()
    for k, v in info.items():
        v = delete_forbidden_c(forbidden_filenames, v)
        info[k] = v
        
    return info

    
#royalroad.com
def get_toc_rr(toc_html):
    with open(toc_html, 'r', encoding = 'utf8') as raw:
        soup = BeautifulSoup(raw, 'html.parser')
        soup = soup.find(id = 'chapters')
        toc = soup.find_all(href=re.compile('chapter'))
        #toc is now a list of a tags
        for a in toc:
            a['href'] = 'https://www.royalroad.com' + a['href']
        return toc

def get_metadata_rr(toc_html):
    '''given the toc.html file, it returns a info dict on novel name, 
    author and chapter file names'''
    with open(toc_html, 'r', encoding='utf8') as toc:
        soup = BeautifulSoup(toc, 'html.parser')
        author = soup.find(property='author')
        author = author.find('a')
        author = author.get_text(strip=True)
        
        novel_name = soup.find('h1')
        novel_name = novel_name.get_text(strip=True)
        raw_novel_name = novel_name
        novel_name = delete_forbidden_c(forbidden_filenames, novel_name)
        
        chapter_file_names = novel_name.lower().replace(' ', '-') + '-chapter-'
        chapter_file_names = delete_forbidden_c(forbidden_filenames, 
            chapter_file_names)
    info = {
    'chapter_file_names': chapter_file_names, 
    #base xhtml file name for each chapter of the epub
    'novel_name': novel_name, #name of epub file
    'author': author, #name of author, meta data
    'raw_novel_name': raw_novel_name 
    #novel_name with possible forbidden characters to use to format the
    #chapter titles later on
    }
    return info

def find_chapter_content_rr(file_name_in, info):
    '''given a raw royalroad html chapter, returns list of its chapter content 
    p tags and its title'''
    with open(file_name_in, 'r', encoding='utf8') as raw:
        soup = BeautifulSoup(raw, 'html.parser')
    chapter_title = soup.title.get_text(strip=True)
    chapter_title = chapter_title.replace('-', '').replace(info['raw_novel'
        '_name'], '').replace('| Royal Road', '')
    chapter_title = chapter_title.strip()

    chapter = soup.find(class_='chapter-content')
    p_list = chapter.find_all('p')
    for p in p_list.copy():
        x = ''
        p_text = p.get_text(strip=True).lower()
        p_text = p_text.replace('.', x).replace('-', x).replace(' ', x)
        title = (chapter_title.lower().replace('.', x).replace('-', x)
            .replace(' ', x))
        if title in p_text or p_text in title:
            p_list.remove(p)

    return chapter, chapter_title

#wuxiaworld.com
def get_toc_ww(file_name_in):
    '''given a toc_html, return a list of a tags (chapters), ie the toc'''
    with open(file_name_in, 'r', encoding='utf8') as raw:
        soup = BeautifulSoup(raw, 'html.parser')
    chapters = soup.find_all(class_="chapter-item")
    toc = [chapter.a for chapter in chapters]
    for a in toc:
        a['href'] = 'https://www.wuxiaworld.com' + a['href']
    return toc

def get_metadata_ww(file_name_in):
    with open(file_name_in, 'r', encoding='utf8') as raw:
        soup = BeautifulSoup(raw, 'html.parser')
    metadata = soup.find('div', class_= 'novel-body')
    #now ww won't allow requests from bots, need to implement cookies usage 
    author = metadata.find('dt', string = 'Author:')
    author = author.next_sibling.next_sibling.get_text(strip=True)
    #twice next_sibling because between the tags there a '\n' which is the true
    #first next_sibling of <dt>Author:</dt>. Can check with
    #for string in metadata.strings:
    #   print(repr(string))
    translator = metadata.find('dt', string = 'Translator:')
    translator = translator.next_sibling.next_sibling.get_text(strip=True)

    author = 'Author: ' + author + ', Translator: ' + translator.strip()
    novel_name = metadata.h2.get_text(strip=True)
    raw_novel_name = novel_name
    novel_name = delete_forbidden_c(forbidden_filenames, novel_name)
    chapter_file_names = novel_name.lower().replace(' ', '-') + '-chapter-'
    info = {
    'chapter_file_names': chapter_file_names, #base xhtml file name for each chapter of the epub
    'novel_name': novel_name, #name of epub file
    'author': author, #name of author, meta data
    'raw_novel_name': raw_novel_name,
    }
    return info

def find_chapter_content_ww(file_name_in):
    '''given a raw wuxiaworld html chapter, returns list of its chapter
    content p tags and its title'''
    with open(file_name_in, 'r', encoding='utf8') as raw:
        soup = BeautifulSoup(raw, 'html.parser')
    chapter_title = soup.title.get_text(strip=True)
    chapter_title = chapter_title.split('-')
    del chapter_title[0]
    del chapter_title[-1]
    chapter_title = '-'.join(chapter_title)
    chapter_title = chapter_title.strip()

    chapter = soup.find(id='chapter-content')
    p_list = chapter.find_all('p')
    for p in p_list[:10]:
        p_text = p.get_text(strip=True).lower()
        p_text = re.sub('[._-]', '', p_text)
        p_text = set(p_text.split())
        title = re.sub('[._-]', '', chapter_title.lower())
        title = set(title.split())
        if title.issubset(p_text) or p_text.issubset(title):
            p_list.remove(p)
  
    return chapter, chapter_title

#wordpress
def get_toc_wp(file_name_in):
    '''given a toc_html, return a list of a tags (chapters), ie the toc'''
    with open(file_name_in, 'r', encoding='utf8') as raw:
        soup = BeautifulSoup(raw, 'html.parser')
    chapters = soup.find(class_="entry-content")
    share = chapters.find(id="jp-post-flair")
    share.decompose()
    chapters = chapters.findAll('a')
    toc = []
    for c in chapters:
    #    if 'wordpress' in c['href']:
        toc.append(c)
    #won't work for wp sites that have bougth a custom domain
    #need to use either "wordpress" or the site name
    return toc

def get_metadata_wp(file_name_in):
    with open(file_name_in, 'r', encoding='utf8') as raw:
        soup = BeautifulSoup(raw, 'html.parser')
    title = soup.find(class_="entry-title").get_text(strip=True)
    info = {
    'chapter_file_names': title,
    'novel_name': title,
    'author': '',
    'raw_novel_name': '',
    }
    return info

def find_chapter_content_wp(file_name_in):
    '''given a raw wordpress html chapter, returns its content
    content p tags and its title'''
    with open(file_name_in, 'r', encoding='utf8') as raw:
        soup = BeautifulSoup(raw, 'html.parser')
        
    chapter_title = soup.find(class_="entry-title")
    chapter_title = chapter_title.get_text(strip=True)
    chapter = soup.find(class_="entry-content")
    share = chapter.find(id="jp-post-flair")
    share.decompose()
    #remove "share this post" part
    p_list = chapter.find_all('p')
      
    return chapter, chapter_title

#blogspot
def get_toc_bs(file_name_in):
    '''given a toc_html, return a list of a tags (chapters), ie the toc'''
    with open(file_name_in, 'r', encoding='utf8') as raw:
        soup = BeautifulSoup(raw, 'html.parser')
    chapters = soup.find(class_="entry-content")
    chapters = chapters.findAll('a')
    toc = []
    for c in chapters:
        toc.append(c)

    return toc

def get_metadata_bs(file_name_in):
    with open(file_name_in, 'r', encoding='utf8') as raw:
        soup = BeautifulSoup(raw, 'html.parser')
    title = soup.find(class_="entry-title").get_text(strip=True)
    
    info = {
    'chapter_file_names': title,
    'novel_name': title,
    'author': '',
    'raw_novel_name': '',
    }
    return info

def find_chapter_content_bs(file_name_in):
    '''given a raw blogspot html chapter, returns its content
    content p tags and its title'''
    with open(file_name_in, 'r', encoding='utf8') as raw:
        soup = BeautifulSoup(raw, 'html.parser')
        
    chapter_title = soup.find(class_="entry-title")
    chapter_title = chapter_title.get_text(strip=True)
    chapter = soup.find(class_="entry-content")

    #remove "share this post" part
    
    return chapter, chapter_title

#MISCELLANEOUS    
def check_error_yn(flag):
    '''check that the flag has y or n as answer and returns it'''
    error_flag = True
    while error_flag:
        if flag.lower().strip() == 'y':
            error_flag = False
        elif flag.lower().strip() == 'n':
            error_flag = False
        else:
            flag = input("You didn't write a correct input, "
                "please write 'y' or 'n'. ")
    return flag.strip()    

def check_error_number(chapter_start, chapter_end):
    '''check if input of chapter start and end are digits and return them'''
    error = True
    while error:
        #.isdigit() works only on string, to check if both input are digits, 
        #checking their combination is enough as digit+digit=digit
        if ((str(chapter_start).strip() + str(chapter_end).strip()).isdigit()
            and chapter_start and chapter_end): #cannot be ""
            error = False
        else:
            print('Please write digits only.')
            chapter_start = input('Start from? ')
            chapter_end = input('End at? ')
    return chapter_start, chapter_end

def get_chapter_s_e(title_list):
    '''define and return starting chapter and ending chapter of epub'''
    chapter_s = ''
    for c in title_list[0]:
        if c.isdigit():
            chapter_s += c
    if len(chapter_s) > 1:
        if '1' in chapter_s:
            chapter_s = '1'
    if chapter_s == '':
        chapter_s = '0'
    chapter_s = chapter_s.strip()

    chapter_e = ''
    for c in title_list[-1]:
        if c.isdigit():
            chapter_e += c
    if chapter_e == '':
        chapter_e = title_list[-1]
    chapter_e = chapter_e.strip()
    return chapter_s, chapter_e

def delete_forbidden_c(forbidden_filenames, string_to_check):
    '''delete any forbidden characters in a given string and returns it clean'''
    for c in string_to_check:
        if c in forbidden_filenames:
            string_to_check = string_to_check.replace(c, '')
    return string_to_check
