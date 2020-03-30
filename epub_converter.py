from bs4 import BeautifulSoup
import os
import zipfile
import re
import functions as f
import requests
import sys
import time

start_time = time.time()

toc_link = input('Toc link? ')

parser = f.parser_choice()

toc_html = 'toc.html'
f.download(toc_link, toc_html)
info = f.get_metadata_rr(toc_html)

flag = input('Do you want to choose a specific range of chapters? y/n'
    '\nIf "n" is chosen (written), then the whole available Toc will be '
    'downloaded and converted to Epub \n')

flag = f.check_error_yn(flag)

link_list = []

chapter_start = ''
chapter_end = ''

chapter_start_end = f.get_link_list(toc_html, link_list, flag, 
    chapter_start, chapter_end, parser)
#fill link_list and get chapter_start and chapter_end


chapter_start = chapter_start_end[0]
chapter_end = chapter_start_end[1]
name_counter = 1
cleaned_html_files = []

for x in range(len(link_list)):
    f.download(link_list[x], str(x) + '.html')
    #download all files from link_list
    f.clean(str(x) + '.html', 'clean-' + info['chapter_file_names'] + 
        str(name_counter) + '.xhtml', parser)
    #clean all downloaded flies
    cleaned_html_files.append('clean-' + info["chapter_file_names"] + 
        str(name_counter) + ".xhtml")
    #add them to cleaned_html_files list
    print('Chapter ' + str(name_counter) + ' processed...')
    name_counter += 1

title_list = f.get_title_list(cleaned_html_files)

if chapter_start != '':
    chapter_s = chapter_start
    chapter_e = chapter_end
elif chapter_start == '':
    chapter_s = f.get_chapter_s_e(title_list)[0]
    chapter_e = f.get_chapter_s_e(title_list)[1]

    
f.generate(cleaned_html_files, info["novel_name"], info["author"], chapter_s, 
    chapter_e)
    #generate epub using cleaned files and making the necessary files

elapsed_time = time.time() - start_time
print('It took ' + str(elapsed_time) + 'seconds.')
