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
#make the parser detection execute at EVERY link of toc, as there might
#be outsourced translations

#if in middle of execution, make unparsable links not stop the program
#but just print a warning msg that said link/page wasn't downloaded for
#parsing reasons

#with the link edit feature, make it a possibility to download multiple
#epubs at once by splitting the link list by some separator, like 
#'--volume-end' or something, maybe --volume-break is better, as it will
#be the separator, ie the split argument, meaning it can't be put at the
#utmost end of a links block lest it starts making an epub on an empty 
#list

#there is a function I quite dislike which I need to refactor better,
#the get_link_list one, but since it works for now, it's low priority

while True:
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

    imgs = []
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
        if parser != 'wordpress' and parser != 'blogspot':
            edit = input('Do you want to edit the link list? y/n ')
            edit = f.check_error_yn(edit)
        else:
            print('Please check link list and edit it if necessary.')
        if parser == 'wordpress' or parser == 'blogspot' or edit.lower() == 'y' :
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
            os.remove('temp.txt')
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
                str(name_counter) + '.xhtml', parser, info, imgs)
            #clean all downloaded flies
            
        print(f'Chapter {str(name_counter)} ({str(x+1)} of '
            f'{str(len(link_list))}) processed...')
        name_counter += 1

    #due to f.clean() making multiple xhtml files if there are imgs, can't
    #include the append in the loop as it's based on the link_list length
    files = os.listdir() #make list of all files and paths in working folder
    cleaned_html_files = [i for i in files if i.startswith('clean') and 
        i.endswith('.xhtml')]
    #narrow files list to only the cleaned chapters

    title_list = f.get_title_list(cleaned_html_files)
    #get chapters individual titles
    if one:
        title_list = [title_list[0]] 
        #when there is an image, multiple title are outputted even though
        #it's just one page, so this is to correct it
        
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
        latter = '-' + chapter_e
        if one:
            latter = ''
        epub_name = novel_name + ' ' + chapter_s + latter + '.epub'

    f.generate(cleaned_html_files, info["novel_name"], info["author"], 
        epub_name, imgs)
        #generate epub using cleaned files and making the necessary files

    elapsed_time = time.time() - start_time
    print('Time taken to finish: ' + str(elapsed_time) + ' seconds (around '
        + str(elapsed_time//60) + ' minutes)')
    flag = input('\nWant to download another epub? y/n ')
    flag = f.check_error_yn(flag)
    if flag.lower() == 'y':
        continue
    elif flag.lower() == 'n':
        print('Quitting program...')
        sys.exit()
