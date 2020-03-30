import requests
import os
import zipfile
import re
import sys
from bs4 import BeautifulSoup

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
            print('Please only input numbers for starting and ending chapters')
            chapter_start = input('Start from? ')
            chapter_end = input('End at? ')
    return chapter_start.strip(), chapter_end.strip()

def get_chapter_start_end(link_list, soup):
    chapter_start = input('From which chapter do you want to start? ')
    chapter_end = input('Until which chapter? ')
    chapter_start = check_error_number(chapter_start, chapter_end)[0]
    chapter_end = check_error_number(chapter_start, chapter_end)[1]
    if (len(link_list) - (int(chapter_end)-int(chapter_start)))<1:
        print('Chapters range not available. Retry with another one.')
        sys.exit()
    try:
        for c in range(int(chapter_start)-1, int(chapter_end)):
            link_list.append(soup[c])
    except:
        print('Chapters range not available. Retry with another one.')
        sys.exit()
    return chapter_start, chapter_end

def parser_choice():
    parser = ''
    sites = '''
    1.WuxiaWorld
    2.RoyalRoad
    '''
    parser_choice = input('Which site? Input a digit.'
        '\n' + sites + '\nMore sites might be added in the future.\n')
    error = True
    while error or len(parser_choice.strip())>1:
        if (str(parser_choice)).isdigit():
            error = False
        else:
            parser_choice = input('Please only input a digit corresponding'
                ' the site.' + sites + '\n')
    if int(parser_choice) == 1:
        parser = 'WuxiaWorld'
    elif int(parser_choice) == 2:
        parser = 'RoyalRoad'
    if parser == '':
        print('Input an available digit.')
        sys.exit()
    return parser
    
def find_toc_rr(toc_html):
    with open(toc_html, 'r', encoding = 'utf8') as raw:
        soup = BeautifulSoup(raw, 'html.parser')
        soup = soup.find(id = 'chapters')
        soup = soup.find_all(href=re.compile('chapter'))
        #soup is now a list of a tags
        for a in soup:
            a['href'] = 'https://www.royalroad.com' + a['href']
        return soup

def get_link_list(toc_html, link_list, flag, chapter_start, chapter_end, 
    parser):
    '''given a RoyalRoad toc_link, fill the link_list with its chapters link
    and return chapter_start and chapter_end for later use'''
    if parser == 'RoyalRoad':
        soup = find_toc_rr(toc_html)
        
    if flag.lower() == 'y':
        chapter_start = input('From which chapter do you want to start? ')
        chapter_end = input('Until which chapter? ')
        chapter_start = check_error_number(chapter_start, chapter_end)[0]
        chapter_end = check_error_number(chapter_start, chapter_end)[1]
        if (len(soup) - (int(chapter_end)-int(chapter_start)))<1:
            print('Chapters range not available. Retry with another one.')
            sys.exit()
        try:
            for c in range(int(chapter_start)-1, int(chapter_end)):
                link_list.append(soup[c])
        except:
            print('Chapters range not available. Retry with another one.')
            sys.exit()
    elif flag.lower() == 'n':
        
        for a in soup:
            link_list.append(a['href'])
    
    os.remove(toc_html)
    
    chapter_start_end = [chapter_start, chapter_end]
    return chapter_start_end
    

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
        
        chapter_file_names = novel_name.lower().replace(' ', '-') + '-chapter-'

    info = {
    'chapter_file_names': chapter_file_names, #base xhtml file name for each chapter of the epub
    'novel_name': novel_name, #name of epub file
    'author': author, #name of author, meta data
    }
    return info

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

def find_chapter_content_ww(file_name_in):
    '''given a raw wuxiaworld html file, returns soup of its chapter content
    and its title'''
    raw = open(file_name_in, 'r', encoding='utf8')
    soup = BeautifulSoup(raw, 'html.parser')
    #create bs obj based on raw html in order to use the bs functions
    #manually search for where in the html is the chapter text contained
    #for tscog it is in <div id="chapter-content" class="fr-view">
    chapter_title = soup.find('title')
    chapter_title = chapter_title.text.split('-')[1].lstrip().rstrip()
    #we store chapter title in the var. the title is in the title tag, we
    #take out the SCOG and Wuxiaworld text after converting the tag to txt
    soup = soup.find(id='chapter-content')
    #now our soup, ie html editable obj through bs4, is only the tag with
    #'chapter-content' and its children, I think
    raw.close()
    return soup, chapter_title
    
def find_chapter_content_rr(file_name_in):
    '''given a raw royalroad html file, returns soup of its chapter content 
    and its title'''
    raw = open(file_name_in, 'r', encoding='utf8')
    soup = BeautifulSoup(raw, 'html.parser')
    soup = soup.find(class_='chapter-content')
    if soup.br == None:
        chapter_title = soup.find('p').get_text()
    else:
        chapter_title = soup.br.replace_with(' - ')
        chapter_title = soup.find('p').get_text()
    soup.find('p').replace_with('')
    raw.close()
    return soup, chapter_title
    
def clean(file_name_in, file_name_out, parser):
    '''takes html file from download function and give as output a cleaned
    version of it'''
    if parser == 'RoyalRoad':
        soup = find_chapter_content_rr(file_name_in)[0]
        chapter_title = find_chapter_content_rr(file_name_in)[1]
    elif parser == 'WuxiaWorld':
        soup = find_chapter_content_ww(file_name_in)[0]
        chapter_title = find_chapter_content_ww(file_name_in)[1]  
    txt = ''
    for p in soup.find_all('p'):
        txt += p.text + '\n'
    #as the html chapter doesn't have line break in its code, we can't
    #convert all the chapter-content to text immediately because we would
    #get a wall of text without returns after periods. Thus we first create
    #a variable to hold the text, then, for each p tag that represents a 
    #line of the chapter we convert it to a string which we add to the 
    #text variable with a '\n', ie return to have a properly formatted chpt
    txt = txt.replace('Previous Chapter', '').replace('Next Chapter', '')
    #now only unnecessary words remain like prev and next chapters, 
    #which can be replaced with ''
    txt = txt.lstrip().rstrip()
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
    return soup.title
    #return the title tag of a html file

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
    toc_start = '''
        <?xml version='1.0' encoding='utf-8'?>
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
                        %(toc_end)s'''
    toc_mid = ""
    toc_end = '''</ol></nav></section></body></html>'''
    for i, y in enumerate(cleaned_html_files):
        chapter = find_between(cleaned_html_files[i])
        chapter = str(chapter)
        toc_mid += '''<li class="toc-Chapter-rw" id="num_%s">
            <a href="%s">%s</a>
            </li>''' % (i, cleaned_html_files[i], chapter)
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
