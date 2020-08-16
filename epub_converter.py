from bs4 import BeautifulSoup
import os
import zipfile
import re
import functions as f
import requests
import cloudscraper
import sys
import time


#THINGS TO DO
#MAKE LINK LIST EDITABLE AFTER GETTING IT
#ADD IMAGES
#BETTER FORMAT IT

#wrote it in more details in functions "get_list()", but I need to add either
#fallback in case someone choose a range that start from 0 and the ability to 
#do so by not writing the chapter_start part, and thus getting all chapters
#from the first available. Same for the chapter_end: not writing>get chapters
#to the latest available. Thus, I can tell users "0 not accepted, to start from
#the beginning leave empty chapter_start" or something

one = False
toc = False

q = input('One link/chapter or multiple chapters?\n1. One link\n2. Multiple\n')
if q == '1':
    one = True
elif q == '2':
    toc = True
else:
    print('Input not accepted. Retry. Closing program...')
    sys.exit()
    
toc_link = input('Link? ')

parser = f.parser_choice(toc_link)
toc_html = 'toc.html'

f.download(toc_link, toc_html)

info = f.get_info(parser, toc_html)

link_list = []
chapter_start = ''
chapter_end = ''

if toc:
    #if the request is just one link, skip all link list creation
    flag = input('\nDo you want to choose a specific range of chapters? y/n'
        '\nIf "n" is chosen (written), then the whole available Toc will be '
        'downloaded and converted to Epub \n')
    flag = f.check_error_yn(flag)

    finished_flag = False
    if flag.lower() == 'n':
        a = input('Is the novel finished? Chapters range won\'t be shown in'
            ' filename if it\'s a finished series. y/n\n')
        a = f.check_error_yn(a)
        if a.lower() == 'y':
            finished_flag = True
        else:
            print('Series unfinished, got it. Continuing...')
    chapter_start, chapter_end = f.get_link_list(toc_html, link_list, flag, 
        chapter_start, chapter_end, parser)
    #fill link_list and get chapter_start and chapter_end
    #I'm truly disliking this function that does too many things confusingly
    #I'm going to soon fix it, probably separating them?
    if parser != 'wordpress':
        edit = input('Do you want to edit the link list? y/n ')
        edit = f.check_error_yn(edit)
    else:
        print('Please check link list and edit it if necessary.')
    if parser == 'wordpress' or edit.lower() == 'y' :
        with open('temp.txt', 'w', encoding='utf8') as t:
            for link in link_list:
                t.write(link)
                t.write('\n')
            os.startfile('temp.txt')
        input('Edit list in txt editor and press any button to continue ' +
            'after having closed the editor. ')
        with open('temp.txt', 'r', encoding='utf8') as t:
            links = t.read()
            links = links.strip()
            links = links.split('\n')
            links = [link for link in links if link != '']
            link_list = []
            for link in links:
                link_list.append(link.strip())
if one:
    link_list.append(toc_link)
    finished_flag = False
    
os.remove(toc_html)
start_time = time.time()

if chapter_start != '':
    name_counter = int(chapter_start)
    #if chapter start was given (ie not ''), name_counter will start from that
elif chapter_start == '':
    name_counter = 1
    
cleaned_html_files = []

for x in range(len(link_list)):
    #for each link in link_list, check if the downloaded and cleaned file 
    #already exist (maybe from previous interrupted run) and if not continue
    #by downloading and cleaning all chapters from the links
    if not os.path.exists('clean-' + info["chapter_file_names"] + 
        str(name_counter) + ".xhtml"):
        f.download(link_list[x], 'raw-' + info['chapter_file_names'] + 
            str(name_counter) + '.html')
        #download all files from link_list
        f.clean('raw-' + info['chapter_file_names'] + str(name_counter) 
            + '.html', 'clean-' + info['chapter_file_names'] + 
            str(name_counter) + '.xhtml', parser, info)
        #clean all downloaded flies
    cleaned_html_files.append('clean-' + info["chapter_file_names"] + 
        str(name_counter) + ".xhtml")
    #add them to cleaned_html_files list
    print('Chapter ' + str(name_counter) + ' processed...')
    name_counter += 1
    
title_list = f.get_title_list(cleaned_html_files)
#get chapters individual titles

if chapter_start != '':
    chapter_s = chapter_start
    chapter_e = chapter_end
#^this makes even 'prologue', 'epilogue', 'afterwords' chapters into numbers
#when naming the epub (not in the epub itself), need to integrate the 
#mechanics of get_chapter_s_e() with the above code
elif chapter_start == '':
    chapter_s, chapter_e = f.get_chapter_s_e(title_list)


novel_name = info['novel_name']
if finished_flag:
    epub_name = novel_name + '.epub'
else:
    epub_name = novel_name + ' ' + chapter_s + '-' + chapter_e + '.epub'

f.generate(cleaned_html_files, info["novel_name"], info["author"], epub_name)
    #generate epub using cleaned files and making the necessary files

elapsed_time = time.time() - start_time
print('Time taken to finish: ' + str(elapsed_time) + ' seconds (around '
    + str(elapsed_time//60) + ' minutes)')
