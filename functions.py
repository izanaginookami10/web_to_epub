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
import bs4 #for the isinstance check
from pprint import pprint

forbidden_filenames = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', "'",
    '’', '!']
not_chapter_links = ['.jpg', '.jpeg', '.png', '.gif', 'amazon.com', 
    'amazon.jp', 'amazon.uk', '.ico', '.jp']

debug = True
tags = False
imgs = False
#^ will need to link these to some general settings

#the get_toc functions need editing for the a tags: sometimes they're returned as
#a tags list, sometimes as url list. Better to have them act the same...
#maybe make them all return a tags and do the polishing in a common later phase

#PARSERS
gp = 'general parser'
ww = 'www.wuxiaworld.com'
rr = 'www.royalroad.com'
wp = 'wordpress'
bs = 'blogspot'
parsers = [ww, rr, wp, bs]
perfect_parsers = [ww, rr]
wp_sites = ['isekailunatic.com', 'defiring.com', 'shirusekai.com',
    'rhextranslations.com', 'dreamsofjianghu.ca']
bs_sites = ['skythewood']

#CORE
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
        parser = gp
        
    re_url = 'http.+\/\/.+?\/' #http any until // any until first /
    url = re.match(re_url, toc_link).group() #group to get matched str
    url = url[:-1] #exclude the last '/'
    return parser, url

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
        info = get_metadata_gp(toc_html)
    for k, v in info.items():
        v = delete_forbidden_c(forbidden_filenames, v)
        info[k] = v
    if debug:
        debug_folder = '_debug ' + str(info['novel_name'])
        if not os.path.exists(debug_folder):
            os.mkdir(debug_folder)
    
    return info

def download(link, file_name):
    '''get content from provided link to a html file, ie download a webpage''' 
    s = cloudscraper.create_scraper()
    #using cloudscraper to bypass cloudflare bot checks
    
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
    
    
def get_link_list(toc_html, parser, url):
    '''given a toc, fill the link_list with its chapters link
    and return chapter_start and chapter_end for later use'''
    if parser == 'www.royalroad.com':
        toc, titles = get_toc_rr(toc_html)
    elif parser == 'www.wuxiaworld.com':
        toc, titles = get_toc_ww(toc_html)
    elif parser == 'wordpress':
        toc, titles = get_toc_wp(toc_html)
    elif parser == bs:
        toc, titles = get_toc_bs(toc_html)
    else:
        toc, titles = get_toc_gp(toc_html)
    #toc is a list of url, NOT a tags.
    if not toc:
        print('Sorry, wasn\'t able to parse any links.')
        sys.exit()
    
    link_list = toc
    #adjust link list in case the links aren't full url but partial ones
    for n, link in enumerate(link_list): 
        if link[0] == '/': #it means they're implying a site sub dir
            #using enumerate to get link_list items directly as otherwise
            #can't edit them by using the loop items (link!=link_list[n])
            link_list[n] = url + link #add main url of site to implied link
            #(requests won't be able to get it otherwise)         
            
    for link in link_list.copy(): #bettr not to edit list while looping it
        for i in not_chapter_links:
            if i in link:
                link_list.remove(link)
                break #if a link is removed due to having a match with a
                #not_chapter_links items, mustn't continue searching for
                #other matches with other items: another match would try
                #to remove an already removed link
    return link_list
    
def edit_link_list(parser, link_list):
    '''edit link list on demand'''
    if parser in perfect_parsers:
        edit = input('Do you want to edit (select chapters range, skip ' +
            ' specific chapters, delete wrong links...) the link list? y/n ')
        edit = check_error_yn(edit)
    else:
        print('Please check link list and edit it if necessary.')
    if parser not in perfect_parsers or edit.lower() == 'y' :
        with open('temp.txt', 'w', encoding='utf8') as t:
            for link in link_list:
                t.write(link)
                t.write('\n')
            os.startfile('temp.txt')
        link_edit = input('Edit list in txt editor and press any ' +
            ' button to continue. Press "R" and then ENTER if you ' +
            'need to reverse the list order.')
        with open('temp.txt', 'r', encoding='utf8') as t:
            links = t.read()
            links = links.strip()
            links = links.split('\n')
            links = [link for link in links if link != '']
            link_list = []
            for link in links:
                link_list.append(link.strip())
        if str(link_edit).upper() == 'R':
            link_list.reverse()
        os.remove('temp.txt')
    return link_list
    
def chapters_selection(titles, flag, toc):
    for n, title in enumerate(titles):
        print(str(n+1) + ' - ' + title.strip())
        
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
            if isinstance(a, bs4.element.Tag):
                if a.has_attr('href'): #avoid fake links
                    link_list.append(a['href'])
    return chapter_start, chapter_end #maybe I should make them glob vars...          
    
    
def get_chapter_content(file_name_in, info, parser, imgs):
    if parser == rr:
        chapter, chapter_title = find_chapter_content_rr(file_name_in, info)
    elif parser == ww:
        chapter, chapter_title = find_chapter_content_ww(file_name_in)
    elif parser == wp:
        chapter, chapter_title = find_chapter_content_wp(file_name_in)
    elif parser == bs:
        chapter, chapter_title = find_chapter_content_bs(file_name_in)
    else:
        chapter, chapter_title = find_chapter_content_gp(file_name_in)
    #chapter is the whole div/whatever tag the chapter content is in,
    #necessary to have the "raw" chapter html for get_imgs()
    
    if debug: #to get an untouched copy of original source to check results
        debug_folder = '_debug ' + str(info['novel_name'])
        with open(debug_folder + '\\' + chapter_title + '.html', 'w', 
            encoding='utf-8') as html:
             html.write(str(chapter))
    
    if imgs: #to opt out of getting imgs due to eventual bugs
        chapter = get_imgs(chapter, imgs) 
    #get img filenames, download them and mark the tags in the html file
    
    if tags: #to make it optional, because of eventual bugs to fix
        chapter = keep_tags(chapter)
    #mark tags in chapter 
    
    
    if tags:
        chapter = BeautifulSoup(chapter, 'html.parser')
    #str obj -> BeautifulSoup obj again
    if imgs:
        chapter.div.unwrap() #due to making it a bs4 object in get_img, 
    #contents will get also the outer chapter content div, so we delete it 
    if not isinstance(chapter, list):
        chapter = chapter.contents #if chapter is already a p tags list skip this
    #attribute contents get whatever element once, full with eventual 
    #children tags.
    #findAll get redundant tags (parent and children separatedly, so 
    #children show up multiple times). Can't use .text or .get_text() as it 
    #doen't assure \n in the string, so it might result in a wall of text. 
    
    return chapter, chapter_title
    
def keep_tags(chapter):    
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
            chapter = chapter.replace(otag, mtag+otag)
            #<tag -> -tag-<tag
            #because the otag might contains unknown attributes
            chapter = chapter.replace(ctag, cmtag+ctag)
            #</tag -> -/tag-</tag
    #img tags were marked with get_imgs() through tag.wrap(new_tag)
    return chapter

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
        
        if 'data:image' in src:
            continue
        #due to the possibility of imgs being data URI, ie something like
        #'data:image/png;base64,xxxxxxx...' ie coded in basecode64 or similar
        #I'll ignore them for now, until I bump in a site that has them
        
        
        
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
    
    
    
def clean(file_name_in, file_name_out, parser, info, imgs):
    '''takes html file from download function and give as output a cleaned
    version of it, return chapter title for later use'''
    
    chapter, chapter_title = get_chapter_content(file_name_in, info, 
        parser, imgs)
    
    txt = ''
    for t in chapter: #chapter is a list of bs4 obj (tag and navstrings)
    #in order to try to keep the original chapter formatting as much as possible,
    #the tags were substituted with -tag- and are now returned as tags
        
        if isinstance(t, bs4.element.Tag): #navstring don't have get_text
            #need to have a tag, not a navstring to check for br tags, 
            #as for some reason navstring always satisfy the tag.find() method
            if t.find('br'): #if there are any br tags in t
                for b in t.findAll('br'): #for all br tags in t
                    b.replaceWith('-br-') #replace tag <br/> with navString
                    #'-br-'. Precious attempt of using soup.new_tag() failed
                    #because I cannot use soup.insert(new_tag) as soup 
                    #(ie chapter) is now a list of tags and because I need
                    #to insert them in the 't', ie each item of chapter.contents
                    #which isn't a BeautifulSoup obj but a bs4.element.Tag
                    #that in turn doesn't allow new_tag() or insert() arising
                    #errors
                #sometimes there are <br> tags within <p> tags, which aren't
                #kept with the get_text() function as they are ignored
                #since they're tags and not text
            if t.find('hr'): #if there are any hr tags in t
                print('hr')
                for h in t.findAll('hr'): #for all hr tags in t
                    h.replaceWith('-hr-') #replace tag <hr> with navString
           #of course it doesn't find any hr or br... chapter is a bunch of p tags already isn't it
            
            t = t.get_text() 
            #if strip=True, it will delete \xa0, which I don't want as I
            #need to replace it with a normal space
            
        if '\xa0' in t:
            t = t.replace('\xa0', ' ') 
            #ww had them instead of spaces after the dots, they are
            #non-breaking space, in html it's "&nbsp", it becomes '\xa0'
            #in unicode
            
        if tags:
            if '-em-' in t:
                t = t.replace('-em-', '<em>').replace('-/em-', '</em>')
            if '-i-' in t:
                t = t.replace('-i-', '<i>').replace('-/i-', '</i>')
            if '-b-' in t:
                t = t.replace('-b-', '<b>').replace('-/b-', '</b>')
            if '-strong-' in t:
                t = t.replace('-strong-', '<strong>').replace('-/strong-', 
                    '</strong>')
        #the above code WON'T work like in gamers chapter 2, because the---------------------------------
        #opening tags could contain other stuff other than <b>, like
        #<b something something>. So these ones will not be replaced with
        #-b-, but </b> will be with -/b-. And since the if triggers are
        #if -b- appears, and in this case they don't, the substituted
        #-/b- will remain. Meaning that I need to put the -b- before the
        #the opening tag, as I can't predict what's inside the opening 
        #tag, like replace ('<b', '-b-<b') or maybe use regex... if it
        #has a replace function, re.replace('<b.*>', '<b.*>-b-')
        #I don't think it will be a issue putting it before the opening
        #tag though.
        t = t.replace('-br-', '<br>') #substittue eventual br marker with tags
        t = t.replace('-hr-', '<hr>') #substittue eventual hr marker with tags
        txt += t + '\n'
    chapter = txt

    chapter = chapter.strip().split('\n') #now a list of lines
    
    if len(chapter) > 10:
        nav = ['Previous Chapter', 'Next Chapter', '|', 'Main Page', 'Toc',
            'Table of Content', 'Patreon', 'adblock']
        first_lines = 5
        last_lines = 10
        for n in range(last_lines):
            n += 1 #range will go from 0 to 9
            ll = chapter[-n] #each loop will go over line from the end
            for i in nav:
                if i.lower() in ll.lower():
                    chapter[-n] = chapter[-n].replace(ll, '')    
                    #can't use ll because it won't edit the real list item 
        
    chapter = '\n'.join(chapter)
    #in case there are unnecessary prev, next chapters in last 3 lines
    chapter = chapter.strip()
    #delete any excessive whitespace just to be safe
    chapter = chapter.replace('\n', '</p>\n<p>')
    #as we have to make an epub and thus use html format, after we've 
    #cleaned the chapter from all the useless stuff and tags, we put each
    #line within <p> tags by replacing each '\n' with a closing and opening
    #<p> tag, this will leave a missing opening tag at the beginning and a
    #closing tag at the end 
    
    if imgs:
        img_tag = '-img-'
        if img_tag in chapter:
            chapter = chapter.replace('-img-', '<br><img src="').replace(
                '-/img-','"><br>') #adding break lines before and after img
    write_xhtml(file_name_out, chapter_title, chapter)  
        
    #closed all tags and file, now we delete the file_name_in, ie raws
    os.remove(file_name_in)
    return chapter_title
    
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

def generate(cleaned_html_files, novel_name, author, epub_name, imgs, info):
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
        '\n-mimetype created')
    
    epub.writestr('META-INF/container.xml', '<container version="1.0"'
        '\nxmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
        '\n<rootfiles>'
        '\n<rootfile full-path="OEBPS/Content.opf" '
        'media-type="application/oebps-package+xml"/>'
        '\n</rootfiles>'
        '\n</container>')
    #make file 'container.xml' in folder 'META-INF'. Same for every epub
    print('Creating Epub file (2/4)...'
        '\n-container.xml created'
        '\n-creating content.opf...')
    
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
            'media-type="application/xhtml+xml"/>\n')
        spine += f'<itemref idref = "file_{str(n+1)}" />\n' 
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
            
            manifest += (f'<item id="{img}" {cover} href="{img}" '
                'media-type="image/jpeg"/>\n')
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
        '\n-content.opf created')
        
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
    if debug:
        debug_folder = '_debug ' + str(info['novel_name'])
        '''
        epub_contents = epub.namelist()
        for namefile in epub_contents:
            with epub.open(namefile) as content:
                content = content.read()
            with open(debug_folder + '\\' + namefile.replace('/', '_') 
                + '.txt', 'w', encoding='utf-8') as f:
                f.write(str(content))
    #if debug is on, make a readable txt copy of the epub files
        '''
        with zipfile.ZipFile(epub_name, 'r') as zip_ref:
            zip_ref.extractall(debug_folder)
        #get all epub contents in debug folder to check
        

    for x in cleaned_html_files:
        os.remove(x)
    print('Epub created'
        '\nFinished')
        

    
#royalroad.com
def get_toc_rr(toc_html):
    with open(toc_html, 'r', encoding = 'utf8') as raw:
        soup = BeautifulSoup(raw, 'html.parser')
        soup = soup.find(id = 'chapters')
        toc = soup.find_all(href=re.compile('chapter'))
        #toc is now a list of a tags
        for a in toc:
            a['href'] = 'https://www.royalroad.com' + a['href']
        titles = [a.text for a in toc]
        return toc, titles

def get_metadata_rr(toc_html):
    '''given the toc.html file, it returns a info dict on novel name, 
    author and chapter file names'''
    with open(toc_html, 'r', encoding='utf8') as toc:
        soup = BeautifulSoup(toc, 'html.parser')
        author = soup.find(property='author')
        author = author.find('a')
        if author:
            author = author.get_text(strip=True)
        else:
            author = soup.find('span', string=' by ')
            author = soup.next_sibling.next_sibling.text 
            #rr has different layout for single pages, so author 
            #is found in this case (ie if property='author' returns
            #none) by getting next tag after the ' by ', then get 
            #the next one again since the 1st one was whitespace 
    
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

    return chapter, chapter_title

#wuxiaworld.com
def get_toc_ww(file_name_in):
    '''given a toc_html, return a list of a tags (chapters), ie the toc'''
    with open(file_name_in, 'r', encoding='utf8') as raw:
        soup = BeautifulSoup(raw, 'html.parser')
    chapters = soup.find_all(class_="chapter-item")
    toc = [chapter.a for chapter in chapters]
    titles = [chapter.a.text for chapter in chapters]
    for a in toc:
        a['href'] = 'https://www.wuxiaworld.com' + a['href']
    return toc, titles

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

    return chapter, chapter_title

#wordpress
def get_toc_wp(file_name_in):
    '''given a toc_html, return a list of a tags (chapters), ie the toc'''
    with open(file_name_in, 'r', encoding='utf8') as raw:
        soup = BeautifulSoup(raw, 'html.parser')
    chapters = soup.find(class_="entry-content")

    share = chapters.find(id="jp-post-flair")
    if share: #maybe wp authors won't make the post commentable
        share.decompose()
    chapters = chapters.findAll('a')
    titles = [a.text for a in chapters]
    toc = []
    for c in chapters:
    #    if 'wordpress' in c['href']:
        toc.append(c['href'])
    #won't work for wp sites that have bougth a custom domain
    #need to use either "wordpress" or the site name
    return toc, titles

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
    if share: #maybe wp authors won't make the post commentable
        share.decompose()
    #remove "share this post" part

    return chapter, chapter_title

#blogspot
def get_toc_bs(file_name_in):
    '''given a toc_html, return a list of a tags (chapters), ie the toc'''
    with open(file_name_in, 'r', encoding='utf8') as raw:
        soup = BeautifulSoup(raw, 'html.parser')
    chapters = soup.find(class_="entry-content")
    chapters = chapters.findAll('a')
    titles = [a.text for a in chapters]
    toc = []
    for c in chapters:
        toc.append(c['href'])

    return toc, titles

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


#General parser
def get_toc_gp(file_name_in):
    '''given a toc_html, return a list of a tags (chapters), ie the toc'''
    with open(file_name_in, 'r', encoding='utf8') as raw:
        soup = BeautifulSoup(raw, 'html.parser')
    toc = []
    chapters = soup.body.find_all(['div', 'ul', 'ol'])
    a_lists = []
    for lst in chapters:
        a_lists.append(lst.find_all('a', href=True))
    a_lists.sort(key=len)

    a_lists = a_lists[-1]

    chapters = []

    for a_tag in a_lists:
        criteria = len(a_tag.attrs.values()) 
        if criteria < 3:
            chapters.append(a_tag)

    titles = [a.text for a in chapters]
    for c in chapters:
        toc.append(c['href'])

    return toc, titles

def get_metadata_gp(file_name_in):
    with open(file_name_in, 'r', encoding='utf8') as raw:
        soup = BeautifulSoup(raw, 'html.parser')
    title = soup.title.get_text(strip=True) 
    #could make a better job at this, but whatever, it will do
    info = {
    'chapter_file_names': title,
    'novel_name': title,
    'author': '',
    'raw_novel_name': '',
    }
    return info

def find_chapter_content_gp(file_name_in):
    with open(file_name_in, 'r', encoding='utf8') as raw:
        soup = BeautifulSoup(raw, 'html.parser')
    #1.get all tags
    tags = soup.body.find_all()#contents #starting from body 
    tags = [tag for tag in tags if isinstance(tag, bs4.element.Tag)]
    #filter out all elements in tags list that isn't a tag, ie \n and strings

    #2.find one with most text
    #rather than p tags, maybe navstring would be better as it's safer
    #not sure how to use it with find_all() though, maybe find_all(string=re...) 
    #with re set to match anything? Will go for p tags for now to be safe it works first

    #to include blogspot pages in which instead of p tags we have div, maybe make
    #an if on the basis that if the tags_p overall text isn't greater than x words/characters
    #it should redo the step with div tag?
    #otherwise find another way to get a tag containing multiple with same structure tags
    #containing text in their deepest child?
    #or just make a specific parser for blogspot praying it's the only site to have
    #such weird strutcture...

    #make list of all tags' p tags -> tags_p = list of lists of p tags
    tags_p = [tag.find_all('p', recursive=False) for tag in tags]
            #need to limit the find_all() to only search for the direct children 
            #as otherwise it will take the most outward tag containing the
            #chapter content as long as it has even few additional p tags   
    tags_p.sort(key=len)
    #to see which tag has the highest amount of p tags, sort them by lentght
    #of each item in ascending order (basically sorting len(item0), len(item1)...
    #thus the last, [-1] will be the highest p tags containing tags
    #(previously did this with max() and index(), but sorting is... more direct)

    is_chapter = tags_p[-1] #list of p tags of tag with most of them
    #to find the chapter tittle, search for a tag, p or h, which navstring has 
    #a digit, prologue or epilogue or number in words and most importantly that is contained
    #within the <title> tag
    #start searching from first line of chapter content and earlier tags
    #if nothing is found, just use the <title>'s navstring.
    
    #the case of comment being longer than the chapter itself should be 
    #extremely rare, so instead of checking if the is_chapter has too 
    #unwanted tags which isn't reliable enough since there might be 
    #sites/translators who put ads or whatever in the chapter itself, 
    #better to make more phases of which the first should be whether the 
    #2nd tag with most p has at least x% of words of is_chapter, if that's 
    #the case we can proceed to check for unwanted tags for both and with 
    #some ratio choose which one is the real chapter. Criteria should be 
    #very strict as I don't think there even will be cases of comment 
    #lenght > chapter lenght
    chapter = is_chapter
    
    title_tag = soup.title.text
    chapter_title = title_tag

    h_tags = soup.find_all(re.compile(r'h\d+')) 
    #could be more efficient and limit the search range to before the chapter
    #content with find_all_previous(), but for some reasons it won't work, 
    #maybe I can't find if the depth level of the tags is different

    for ht in h_tags:
        htext = ht.text.replace('\xa0', ' ')
        #happened that \xa0 screwed my search for the title in h tags
        if htext in title_tag: 
            chapter_title = htext.strip()

    #should also search for the first string line of chapter content as 
    #sometimes the chapter's title is like that

    for line in chapter[0:10]:
        if line.text != None:
            line_ts = line.text.strip()
            if line_ts != '' and line_ts in chapter_title:
                chapter_title = line_ts
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
    p_s = '\d+|prologue|$' #pattern_s
    #digit OR 'prologue' OR end string ie '', latter is not to get NONE
    chapter_s = re.search(p_s, title_list[0], flags=re.IGNORECASE).group()
    #re.search gets only first occurence and group() will return said occurence
    #re.IGNORECASE makes search case insensitive
    chapter_s = chapter_s.strip()
    p_e = '\d+|epilogue|end.* |$'
    chapter_e = re.search(p_e, title_list[-1], flags=re.IGNORECASE).group()
    chapter_e = chapter_e.strip()
    return chapter_s, chapter_e

def delete_forbidden_c(forbidden_filenames, string_to_check):
    '''delete any forbidden characters in a given string and returns it clean'''
    for c in string_to_check:
        if c in forbidden_filenames:
            string_to_check = string_to_check.replace(c, '')
    return string_to_check
