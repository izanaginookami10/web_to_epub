from bs4 import BeautifulSoup
import os
import zipfile
import re
import functions as f
import requests
import cloudscraper
import sys
import time
from natsort import natsorted #else chapters will be ordered lexicographically

#THINGS TO DO
#check for duplicate chapter links when getting the links list and erase
#them (check if combination of url and navstring is same as another one?)

#refactor this shit, especially, minimize the epub_converter.py file to
#be higher leveled and more understandable -> make more functions

#fucking settings

#make the parser detection execute at EVERY link of toc, as there might
#be outsourced translations
#to do that, I will have to first implement a way to get the toc link
#first? This would introduce the need to make a GENERAL PARSER for sites
#which haven't a specific parser. Like getting the chapter content by
#finding the div tag with most text, excluding it if it has too many links
#as that would be most likely the comment section.
#Alternatively, I could insert a second parser detection within each
#get_chapter_content()?

#this is strictly related to the above point
#if in middle of execution, make unparsable links not stop the program
#but just print a warning msg that said link/page wasn't downloaded for
#parsing reasons

#the img implementation works for now, but it would be more optimal to
#have each img be in their separated xhtml page. The logic is already
#done: basically split each chapter at every img tag occurence and then
#write them in the epub in that order. The issue would be changing how 
#it works now, as the clean() function would output multiple files, for 
#this writing the part (and adding it to the manifest as well as spine)
#can't be in the same loop based on link_list items, but must be based
#on the cleaned_html_files list. Such list also cannot be made after the
#clean() function finished, as listdir would append the file in an order
#different from the intended one, meaning I would need to append each part
#to the list as soon as they've cleaned and before the next part is cleaned
#a workaround might be tweaking with the spine? or maybe make the
#epub generation happen with the generation of cleaned html files
#like before? This would need to somehow either take out from
#clean() the partition of chapter in parts if there is an image,
#or somehow link this creation with the epub generation, maybe
#using the filenames huh...

#also NEED to find a way to erase empty html pages made with
#get_imgs()

#make clean() take the cleaned files list as arg and then append
#each item there directly as soon as the file is "cleaned"

#enchant the way nav elements such as next prev chapter are deleted,
#by adding a search for a tags in the chapter content with related
#string, checking line by line the html raw, deleting maybe everything
#on the related line

'''
to add to clean(), after the img tag replacements -img- to <img
    parts = re.split('(<img.+>)', chapter.strip())
    og_filename_out = file_name_out
    og_chapter_title = chapter_title
    counter = 1
    img_counter = 1
    for part in parts:
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
        
        write_xhtml(file_name_out, chapter_title, chapter)
        
        if '<img' in part:
            img_counter += 1
        else:
            counter += 1
else:
'''


#with the link edit feature, make it a possibility to download multiple
#epubs at once by splitting the link list by some separator, like 
#'--volume-end' or something, maybe --volume-break is better, as it will
#be the separator, ie the split argument, meaning it can't be put at the
#utmost end of a links block lest it starts making an epub on an empty 
#list

#there is a function I quite dislike which I need to refactor better,
#the get_link_list one, but since it works for now, it's low priority

while True: #to continue converting after doing one epub
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

    parser, url = f.parser_choice(toc_link)
    toc_html = 'toc.html'

    f.download(toc_link, toc_html)

    info = f.get_info(parser, toc_html)

    imgs = []

    chapter_start = ''
    chapter_end = ''

    if toc:
        #if the request is just one link, skip all link list creation
        '''
        finished_flag = False
        if flag.lower() == 'n':
            a = input('Is the novel finished? Chapters range won\'t be shown in'
                ' filename if it\'s a finished series. y/n\n')
            a = f.check_error_yn(a)
            if a.lower() == 'y':
                finished_flag = True
            else:
                print('Series unfinished, got it. Continuing...')
        '''
        #the finished flag part is a waste of time for my tests
        #if anyone want it just take away the opening and closing "'''" 
        
        link_list = f.get_link_list(toc_html, parser, url)
        #make/fill link_list
        
        link_list = f.edit_link_list(parser, link_list)
        #fix link_list, due to editing here the chapters selection is off
        #as it's too redundant right now
    '''
        #print chapters and ask whether it's okay or if a range is needed
        flag = input('\nDo you want to choose a specific range of chapters? y/n'
    '\nIf "n" is chosen (written), then the whole available Toc will be '
    'downloaded and converted to Epub.'
    '\nIf "y" is chosen, a list of available chapters with their indexes/chapter numbers will be shown.\n')
        flag = f.check_error_yn(flag)
    if one:
        link_list.append(toc_link)
        #finished_flag = False
      '''  
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
        file_name = (info['chapter_file_names'].replace(' ', '-') +
            '-' + str(name_counter))
        file_name = f.delete_forbidden_c(f.forbidden_filenames, file_name)
        #spaces and forbidden charas aren't allowed in links, and the chapter 
        #name will be the href link in the content.opf part of the epub file
        if not os.path.exists('clean-' + file_name + 
            str(name_counter) + ".xhtml"):
            f.download(link_list[x], 'raw-' + file_name + '.html')
            #download all files from link_list
            chapter_title = f.clean('raw-' + file_name + '.html', 'clean-' 
                + file_name + '.xhtml', parser, info, imgs)
            #clean all downloaded flies
            
        print(f'Chapter {str(x+1)}/{str(len(link_list))} ("{chapter_title}")'
            ' processed...')
        name_counter += 1

    #due to f.clean() making multiple xhtml files if there are imgs, can't
    #include the append in the loop as it's based on the link_list length
    files = os.listdir() #make list of all files and paths in working folder
    cleaned_html_files = [i for i in files if i.startswith('clean') and 
        i.endswith('.xhtml')]
        
    #the cleaned_html_files list will be ordered lexicographically, this
    #means that chapter_1 will be followed by chapter_11, chapter_12, etc
    #instead of chapter_2, a workaround would be including the appending
    #in the previous loop, but it wouldn't allow to include images as per
    #previous comment, thus the need to sort the list with natsort (could
    #have done it with some sort(), lambda, re shenaningans probably tho
    cleaned_html_files = natsorted(cleaned_html_files)
    
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

    '''
    if finished_flag:
        epub_name = novel_name + '.epub'
    else:
    '''
    latter = '-' + chapter_e
    if one:
        latter = ''
    epub_name = novel_name + ' ' + chapter_s + latter + '.epub'

    f.generate(cleaned_html_files, info["novel_name"], info["author"], 
        epub_name, imgs, info)
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
