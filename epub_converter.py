import requests
import os
import zipfile
from bs4 import BeautifulSoup
import functions as f 
    
starting_chapter = input('From which chapter start the download? ')
ending_chapter = input('Until which chapter? ')
#to get triggers for starting and ending the download loop

link_list = [] #will store chapters link that will undergo a loop 

#for Wuxiaworld and many websites, chapters link are the toc base link +
#the chapter number, thus the example follows a wuxiaworld site


base_link = ('https://www.wuxiaworld.com/novel/the-second-coming-of-gluttony/scog-chapter-')
chapters = 'scog-chapter-'
novel = "Second Coming of GLuttony"
author = "Ro Yu-jin"

info = {
    'base_link': base_link, #base link from which download all chapters
    'chapters': chapters, #base xhtml file name for each chapter of the epub
    'novel_name': novel, #name of epub file
    'author': author, #name of author, meta data
    }

for s in range(int(starting_chapter), int(ending_chapter) + 1):
#range(x,y) includes x but not y, thus the +1 at the end
    link_list.append(info['base_link'] + str(s))
#add to the link list a link made up from toc base link + chapter number
name_counter = int(starting_chapter)

file_list = []

for x in range(len(link_list)):
    f.download(link_list[x], str(x) + '.html')
    f.clean(str(x) + '.html', info['chapters'] + str(name_counter) + '.xhtml')
    file_list.append(info["chapters"] + str(name_counter) + ".xhtml")
    name_counter += 1
    #for each item in the list, starting from the first to the last, download
    #the associated webpage to a html file named with the chapter number only
    #ie 'x.html', such file will then be used in clean(), which will delete the
    #old file 'x.html' and make a new ver 'scog-chapter-number.xhtml'
    
f.generate(file_list, info["novel_name"], info["author"], starting_chapter, 
    ending_chapter)

print('finished')
'''

raw = open('1.html', encoding = 'utf8')
soup = BeautifulSoup(raw, 'html.parser')
soup = soup.find(id = 'chapter-content')
text = soup.text
print(text)
'''
