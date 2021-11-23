# web_to_epub
Just a new-newbie personal project to read offline webnovels done with online tutorials.

<strong>Just get the .exe file or the .py (execute them on your IDE or with the CMD using Python, ie writing "python epub_converter.py") files (need both epub_converter.py AND functions.py)</strong> and it should prompt a CMD window from which you should be able to download and make epubs of online novels by following instructions (just copy paste ToC/Chapter link and choose whether you want it all downloaded or if you prefer a specific range of chapters).

If you make use of the py files, you will need to install the necessary modules though. You can also do that with the CMD: "pip install [module name]" (You will be notified of the lacking modules by the script itself). Naturally, you need the "functions.py" file in the same directory as "epub_converter.py" for it to work properly.

As of now, you should only be able to safely(?) download novels from RoyalRoad and WuxiaWorld.

It works most of times, but during my tests I found that several times the program failed because it took too much time downloading the files. In that case, I can only suggest to retry, maybe closing some background apps will help. I made few tests, and downloading around 1300 chapters of Overgeared took around 20 minutes, so yeah. Please be patient.

If you find bugs, errors or simply have suggestions or even requests, do not hesitate to tell me so. I'm very unexperienced with Github and programming in general and of course I'm very busy with real life, so sorry if I will not reply or address issues soon. I mean, I'm really doing this just to make it easier for me to read stuff offline to be honest. Though it's interesting and funny to try to make it workable for other people as well.

# How to setup Python script
## Make sure you have the following already installed:
* git
* python v3.x (including the python modules listed below)

On Windows you can use [scoop](https://scoop.sh) or [winget](https://docs.microsoft.com/en-us/windows/package-manager/winget/) to install these rather easily.
On Linux use your system's package manager.

### Python Prereqs
The python code requires the following modules:
* [BeautifulSoup4](https://pypi.org/project/beautifulsoup4/)
* [requests](https://pypi.org/project/requests/)
* [cloudscraper](https://pypi.org/project/cloudscraper/)
* [natsort](https://pypi.org/project/natsort/)

Run the following to have those installed:
```
pip install BeautifulSoup4 requests cloudscraper natsort
```

## Clone the repo
Run the following:
```
git clone https://github.com/izanaginookami10/web_to_epub
```

## Run the script
```
cd web_to_epub
mkdir tmp
cd tmp
python python ../epub_converter.py
```
It is recommended you create a sub-directory, and run the script from that subdir, this way cleanup afterwards is easier - just delete the subdir and start over.

# Using the script
After running the script, you will be presented with a prompt, choose the method of choice:
```
One link/chapter or multiple chapters?
1. One link
2. Multiple
```
You will then be prompted for the URL
```
Link?
```
After providing the link, if you chose `2` notepad will open with a text file full of URLs for you to edit:
```
Link? https://....
Please check link list and edit it if necessary.
Edit list in txt editor and press any  button to continue. Press "R" and then ENTER if you need to reverse the list order.
```
* In Notepad:
  * Cleanup this list to only include what you want in the final EPUB file.
  * Save the file
  * Close notepad
* Back at the script's prompt:
  * Hit Enter or 'R' per the prompt

At this point the script will start scraping the web pages, saving each page in
to an xhtml file locally (you might want to cleanup the current folder from
these files) and afterwards composing the EPUB file

```
Chapter 1/n ("<page 1 title>") processed...
.
.
.
Chapter n/n ("<page n title>") processed...
Creating Epub file (0/4)...
Creating Epub file (1/4)...
-mimetype created
Creating Epub file (2/4)...
-container.xml created
-creating content.opf...
Creating Epub file (3/4)...
-content.opf created
Creating Epub file (4/4)...
toc.xhtml created
Epub created
Finished
Time taken to finish: sss.mmm seconds (around mm.m minutes)
```
When done, you will be prompted with a question, where you can repeat the process for a new URL or quit.
```
Want to download another epub? y/n n
Quitting program...
```

# Known issues
* If the page has special characters in it's name (examples: `\`,`/`,`:`,`*`,`?` ) the script currently breaks. [Issue #2](https://github.com/izanaginookami10/web_to_epub/issues/2)
