import requests
import os
import zipfile
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
    
def clean(file_name_in, file_name_out):
    '''takes html file from download function and give as output a cleaned
    version of it'''
    raw = open(file_name_in, 'r', encoding='utf8')
    #open html file created with download function
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
    raw.close()
    #we close the downloaded html file, ie file_name_in and start working
    #file_name_out
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
    #return the title of a html file

def generate(html_files, novelname, author, chapter_s, chapter_e):
    #chapter_s and _e are starting and ending chapters
    epub = zipfile.ZipFile(novelname + '_' + chapter_s + '-' + chapter_e +
        '.epub', 'w')
    #create empty zip archive, as epub are essentially a zip files
    
    epub.writestr('mimetype', 'application/epub+zip')
    #zipfile.writestr('namefile', 'txt') 
    #create in epub a file named 'mimetype' which contain the string
    #application/epub+zip'. This file is the same for all epub files
    
    epub.writestr('META-INF/container.xml', '''<container version="1.0"
        xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
        <rootfiles>
        <rootfile full-path="OEBPS/Content.opf" media-type="application/oebps-package+xml"/>
        </rootfiles>
        </container>''')
    #make file 'container.xml' in folder 'META-INF'. Same for every epub
  
    #content.opf will be like this
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
    #manifest and spine will be filled through a loop, so let's make vars to
    #hold their contents
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
        % {"novelname": novelname + ": " + chapter_s + "-" + chapter_e, 
            "author": author, "series": novelname})
    
    #standard string at end of manafest string
    toc_manifest = ('<item href="toc.xhtml" id="toc" '
        'properties="nav" media-type="application/xhtml+xml"/>')
    
    for i, html in enumerate(html_files):
        #enumerate(list) gives a tuple for each item in a list containing 
        #a number starting from 0 and the corresponding item ie (0, item0)
        basename = os.path.basename(html)
        #os.path.basename(path) return name of last path, ie
        #"python_work\Epub Converter\epub_converter.py" -> "epub_converter.py"
        manifest +=('<item id="file_%s" href="%s" '
            'media-type="application/xhtml+xml"/>' % (i + 1, basename))
        spine += '<itemref idref = "file_%s" />' % (i + 1)
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
        
    #content.opf is finished, now last file: ToC, which we divide into 3 parts
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
    for i, y in enumerate(html_files):
        chapter = find_between(html_files[i])
        chapter = str(chapter)
        toc_mid += '''<li class="toc-Chapter-rw" id="num_%s">
            <a href="%s">%s</a>
            </li>''' % (i, html_files[i], chapter)
    #for each file in the list 'html_files', find the respective title and
    #add to toc_mid the string while substituting the variable values
    
    #now we add the finished Toc flie to the epub/zip archive and close it
    #and delete the downloaded and cleaned html files now unnecessary
    epub.writestr("OEBPS/toc.xhtml", toc_start % {"novelname": novelname,
        "toc_mid": toc_mid, "toc_end": toc_end})
    epub.close()
    for x in html_files:
        os.remove(x)
    
