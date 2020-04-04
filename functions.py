import requests
import os
import zipfile
import re
import sys
from bs4 import BeautifulSoup

forbidden_filenames = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']

#CORE

def download(link, file_name):
    '''get content from provided link to a file, ie download a webpage''' 
    page = requests.get(link).text 
        #get content from linked page and store it as text in var page
    file = open(file_name, "w", encoding = "utf8")
        #create a file in write mode
    file.write(page)
        #write the content of var page onto the just created/opened file
    file.close()
    #get content from provided link to a file, ie download a webpage'
    
def get_link_list(toc_html, link_list, flag, chapter_start, chapter_end, 
    parser):
    '''given a RoyalRoad toc, fill the link_list with its chapters link
    and return chapter_start and chapter_end for later use'''
    if parser == 'www.royalroad.com':
        toc = get_toc_rr(toc_html)
    elif parser == 'www.wuxiaworld.com':
        toc = get_toc_ww(toc_html)
        
    if flag.lower() == 'y':
        chapter_start = input('From which chapter do you want to start? ')
        chapter_end = input('Until which chapter? ')
        chapter_start_end = check_error_number(chapter_start, chapter_end)
        chapter_start = chapter_start_end[0]
        chapter_end = chapter_start_end[1]
        #need to have a list containing the chapter start and end values 
        #instead of directly returning them separatedly because it would 
        #start the check_error_number twice and thus request the input twice
        if (len(toc) - (int(chapter_end)-int(chapter_start)))<1:
            print('Chapters range not available. Retry with another one.')
            sys.exit()
        try:
            for c in range(int(chapter_start)-1, int(chapter_end)):
                link_list.append(toc[c]['href'])
        except:
            print('Chapters range not available. Retry with another one.')
            sys.exit()
    elif flag.lower() == 'n':
        for a in toc:
            link_list.append(a['href'])
    
    os.remove(toc_html)
    
    chapter_start_end = [chapter_start, chapter_end]
    return chapter_start_end
    
def clean(file_name_in, file_name_out, parser, info):
    '''takes html file from download function and give as output a cleaned
    version of it'''
    if parser == 'www.royalroad.com':
        p_list = find_chapter_content_rr(file_name_in, info)[0]
        chapter_title = find_chapter_content_rr(file_name_in, info)[1]
    elif parser == 'www.wuxiaworld.com':
        p_list = find_chapter_content_ww(file_name_in)[0]
        chapter_title = find_chapter_content_ww(file_name_in)[1]  
    
    txt = ''
    for p in p_list:
        t = p.text
        if '-em-' in p.text:
            t = t.replace('-em-', '<em>').replace('-/em-', '</em>')
        elif '-i-' in p.text:
            t = t.replace('-i-', '<i>').replace('-/i-', '</i>')
        elif '-b-' in p.text:
            t = t.replace('-b-', '<b>').replace('-/b-', '</b>')
        elif '-strong-' in p.text:
            t = t.replace('-strong-', '<strong>').replace('-/strong-', 
                '</strong>')
        txt += t + '\n' 

    #as the html chapter doesn't have line break in its code, we can't
    #convert all the chapter-content to text immediately because we would
    #get a wall of text without returns after periods. Thus we first create
    #a variable to hold the text, then, for each p tag that represents a 
    #line of the chapter we convert it to a string which we add to the 
    #text variable with a '\n', ie return to have a properly formatted chpt
    #the if sequence is to keep italic or bold formatting
    txt = txt.replace('Previous Chapter', '').replace('Next Chapter', '')
    #in case there are unnecessary prev and next chapters
    txt = txt.strip()
    #delete any excessive whitespace just to be safe
    txt = txt.replace('\n', '</p>\n<p>')
    #as we have to make an epub and thus use html format, after we've 
    #cleaned the chapter from all the useless stuff and tags, we put each
    #line within <p> tags by replacing each '\n' with a closing and opening
    #<p> tag, this will leave a missing opening tag at the beginning and a
    #closing tag at the end 
   
    #we start working on file_name_out
    file = open(file_name_out, 'w', encoding = 'utf8')
    file.write('<html xmlns="http://www.w3.org/1999/xhtml">')
    #epub files by convetion use the xhtml format
    file.write('\n<head>')
    file.write('\n<title>' + chapter_title + '</title>')
    file.write('\n</head>')
    #after the xhtml attribute statement, we put the title, then the body
    file.write('\n<body>')
    file.write('\n<h4><b>' + chapter_title + '</b></h4>')
    file.write('\n<p>' + txt + '</p>')
    #we then insert the title and the chapter text with additional p tags
    file.write('\n</body>')
    file.write('\n</html>')
    file.close()
    #closed all tags and file, now we delete the file_name_in
    os.remove(file_name_in)
    #takes html file from download function and give as output a cleaned
    #version of it

def find_between(file):
    f = open(file, 'r', encoding='utf8')
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

def generate(cleaned_html_files, novel_name, author, chapter_s, chapter_e):
    #chapter_s and _e are starting and ending chapters
    print('Creating Epub file (0/4)...')
    epub = zipfile.ZipFile(novel_name + ' ' + chapter_s + '-' + chapter_e +
        '.epub', 'w')
    #create empty zip archive, as epub are essentially zip files
    
    epub.writestr('mimetype', 'application/epub+zip')
    #zipfile.writestr('namefile', 'txt') 
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
        
    #we need to fill %(metadata)s, %(manifest)s and %(spine)s
    #manifest and spine will be filled through a loop, so let's make empty 
    #vars to hold their contents
    manifest = ''
    spine = ''
    
    #metadata is the same but with few var data such as novelname and author
    metadata = ('<dc:title xmlns:dc="http://purl.org/dc/elements/1.1/">'
        '%(novelname)s</dc:title>'
        '\n<dc:creator xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'xmlns:ns0="http://www.idpf.org/2007/opf" ns0:role="aut" '
        'ns0:file-as="NaN">%(author)s</dc:creator>'
        '\n<meta xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'name="calibre:series" content="%(series)s"/>'
        % {"novelname": novel_name + ": " + chapter_s + "-" + chapter_e, 
            "author": author, "series": novel_name})
    
    #standard string at end of manafest string
    toc_manifest = ('<item href="toc.xhtml" id="toc" '
        'properties="nav" media-type="application/xhtml+xml"/>')
    
    for n, html in enumerate(cleaned_html_files):
        #enumerate(list) gives a tuple for each item in a list containing 
        #a number starting from 0 and the corresponding item ie (0, item0)
        basename = os.path.basename(html)
        #os.path.basename(path) return name of last path, ie
        #"python_work\Epub Converter\epub_converter.py" -> "epub_converter.py"
        manifest +=('<item id="file_%s" href="%s" '
            'media-type="application/xhtml+xml"/>' % (n + 1, basename))
        spine += '<itemref idref = "file_%s" />' % (n + 1)
        epub.write(html, "OEBPS/" + basename)
        #zipfile.write(file, filename) is different from .writestr(filename,
        #content): the former write an existing file to the zipfile with
        #'filename' as its name, while the latter create a new file
        
        #add cleaned chapter file (html) on the epub file in folder 'OEBPS' 
        #with 'basename' as filename
    
    #now we write the completed content.opf file onto the epub archive
    epub.writestr("OEBPS/Content.opf", index_tpl % {
        "metadata": metadata,
        "manifest": manifest + toc_manifest,
        "spine": spine, })
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
    toc_mid = ""
    toc_end = '''</ol></nav></section></body></html>'''
    for n, f in enumerate(cleaned_html_files):
        chapter = find_between(cleaned_html_files[n])
        chapter = str(chapter)
        toc_mid += '''<li class="toc-Chapter-rw" id="num_%s">
            <a href="%s">%s</a>
            </li>''' % (n, cleaned_html_files[n], chapter)
    #for each file in the list 'html_files', find the respective title tag and
    #add to toc_mid the string while substituting the variable values
    
    #now we add the finished Toc flie to the epub/zip archive and close it
    #and delete the downloaded and cleaned html files now unnecessary
    epub.writestr("OEBPS/toc.xhtml", toc_start % {"novelname": novel_name,
        "toc_mid": toc_mid, "toc_end": toc_end})
    print('Creating Epub file (4/4)...'
        '\ntoc.xhtml created')
    
    epub.close()
    for x in cleaned_html_files:
        os.remove(x)
    print('Epub created'
        '\nFinished')



#PARSER

def parser_choice(toc_link):
    '''Will question a parser and return it'''
    #need to make it automatic by checking the toc_link
    parsers = ['www.wuxiaworld.com', 'www.royalroad.com']
    for site in parsers:
        if site in toc_link:
            parser = site
            break
        if all(site not in toc_link for site in parsers):
            print('Site not yet compatible')
            sys.exit()
    return parser

def get_info(parser, toc_html):
    if parser == 'www.wuxiaworld.com':
        info = get_metadata_ww(toc_html)
    elif parser == 'www.royalroad.com':
        info = get_metadata_rr(toc_html)
    else:
        print('Site not yet compatible.')
        sys.exit()
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
    raw = open(file_name_in, 'r', encoding='utf8')
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
    raw.close()
    return p_list, chapter_title

#wuxiaworld.com
def get_toc_ww(toc_html):
    '''given a toc_html, return a list of a tags (chapters), ie the toc'''
    raw = open(toc_html, 'r', encoding='utf8')
    soup = BeautifulSoup(raw, 'html.parser')
    chapters = soup.find_all(class_="chapter-item")
    toc = [chapter.a for chapter in chapters]
    for a in toc:
        a['href'] = 'https://www.wuxiaworld.com' + a['href']
    return toc

def get_metadata_ww(toc_html):
    raw = open(toc_html, 'r', encoding='utf8')
    soup = BeautifulSoup(raw, 'html.parser')
    metadata = soup.find('div', class_= 'novel-body')
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
    raw = open(file_name_in, 'r', encoding='utf8')
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
  
    return p_list, chapter_title
    

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
        if (str(chapter_start).strip() + str(chapter_end).strip()).isdigit():
            error = False
        else:
            chapter_start = input('Start from? ')
            chapter_end = input('End at? ')
    chapter_start_end = [chapter_start.strip(), chapter_end.strip()]
    return chapter_start_end

def get_chapter_s_e(title_list):
    '''define and return starting chapter and ending chapter of epub'''
    #plan to make it so that instead of the whole toc you can choose from and 
    #to which chapter download for the epub
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
