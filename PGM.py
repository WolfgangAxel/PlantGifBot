#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  PGM.py
#  
#  Copyright 2017 Keaton Brown <linux.keaton@gmail.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  

########################################################################
#   PLANT GIF MAKER                                                    #
########################################################################
# 
# Archiving Jeff's growth through hourly screenshots! Updating on
# Imgur every day, week, and month, automatically!
# 

# Do not include '/u/' or '/r/' in any of these
MY_REDDIT_USER = "Omnipotence_is_bliss"

from secret import *

DAY_AL = "rGyhH"
WEK_AL = "3bCHO"
MTH_AL = "aKTcv"

screenshotURL = "https://video.nest.com/api/get_image?uuid=2b5dc4d1a6974df9a44f0bb9bad13216&amp;width=560&quot;"
subreddit = "takecareofmyplant"

## also imports praw, imgurpython, os
from PIL import Image, ImageDraw
from requests import get
from io import BytesIO
from sys import argv
import time
import re
import os

# PGM.py is the filename on the RPi                                     #
# it is also the filename of the testing file on my laptop              # 
# PGM.pi.py is the version I push to my Pi when I make updates          # This is stupid, but it works and switching
if __file__.replace("PGM.py","") != __file__:                           # to using os.path would require more effort
    filepath = __file__.replace("PGM.py","")                            # than it's worth, seeing as how this works.
elif __file__.replace("PGM.pi.py","") != __file__:                      #
    filepath = __file__.replace("PGM.pi.py","")                         #
# If it's named anything other than those two, just get the information
# from the filepath from the python command.
else:
    filepath = re.search(r"[a-zA-Z0-9. ]*(.*)",__file__[::-1]).group(1)[::-1]

Logbook = [time.strftime("%c %Z")]

def getImage():
    Logbook.append("\n#Still\n")
    # Try 10x to get a good image,
    # if not, wait 1 minute and
    # try again. Do that 14x.
    ot = 0
    # ot = overall tries
    while ot < 14:
        t = 0
        # t = try
        while t < 10:
            try:
                Logbook.append(" * Attempt \#"+str(ot)+", try \#"+str(t))
                # Download image
                r = get(screenshotURL)
                # Open it as a PIL Image
                i = Image.open(BytesIO(r.content))
                # Force it to be normal size
                if i.width != 400:
                    i = i.resize((400,224),Image.ANTIALIAS)
                # Get moisture level (thanks, /u/thisguyeric!)
                mg = str(get("http://www.pleasetakecareofmyplant.com/moisture_data.txt").content,"utf-8")
                # pull in the last number from the file
                try:
                    moisture = re.search(r"[0-9]{10},\(\[.*\],([0-9]+)\),$",mg[-136:]).group(1)
                except:
                    # something funky happened
                    moisture = "ukn"
                # Initiate drawing
                d = ImageDraw.Draw(i)
                # Add a black box
                d.rectangle((0,0,36,244),(0,0,0))
                # Create the bar
                d.rectangle((3,86,33,211),(128,128,128))
                # Fill the bar (so long as nothing funky happened)
                if moisture != "ukn":
                    d.rectangle((3, 211-(int(moisture)-150)/300*133,33,211),(50,100,255)) 
                # Make the label on the bar
                d.rectangle((7,142,27,150),(0,0,0))
                d.text((3,141)," "*(4-len(moisture))+moisture)
                # Add date/other text
                d.text((3,0),time.strftime("%Y-\n%m-%d\n%H:%M\n=====\nMoist\n 450",time.gmtime()))
                d.text((3,213)," 150")
                # Save it
                i.save(filepath+"dailies/"+time.strftime("%y-%m-%d-%H-%M",time.gmtime())+".png")
                # Exit the loops
                return None
            except Exception as e:
                Logbook.append(e)
                t+=1
        time.sleep(60)
        ot += 1

def newOrd(n):
    # Thanks, /u/TylerJayWood
    if 4<=n%100<=20:
        return str(n)+"th"
    else:
        return str(n)+{1:"st",2:"nd",3:"rd"}.get(n%10,"th")

def compressSave(first,gifpath,ia):
    first.save(gifPath,save_all=True,append_images=[first]+ia,duration=int(10000/(len(ia)+1)),loop=0)
    _ = os.system("{}convert ".format("sudo " if "/pi/" in filepath else "")+gifPath+" -coalesce -layers OptimizeFrame "+gifPath)

def imgurUp(gifPath,config):
    while t<30:
        try:
            uploaded = Im.upload_from_path(gifPath,config=config,anon=False)
            return uploaded
        except:
            t+=1
            time.sleep(2)
    return False

def makeDailyGif(R,Im):
    Logbook.append("\n#DPG\n")
    now = time.time()
    ia = []
    images = [f for f in sorted(os.listdir(filepath+"dailies/")) if f[-3:] == "png"]
    for filename in images:
        try:
            I = Image.open(filepath+"dailies/"+filename)
            ia.append(I)
        except:
            continue
    first = ia[0]
    Logbook.append(" * Images assembled. Saving...")
    gifPath = filepath+"dailies/"+time.strftime("%y-%m-%d",time.gmtime(now))+".gif"
    compressSave(first,gifpath,ia)
    Logbook.append(" * Images saved. Getting previous result.")
    #Get result from previous day
    prevPost = [post for post in R.redditor('takecareofmyplant').submissions.new(limit=2)][1]
    fancyDay = newOrd(int(time.strftime("%-d",time.gmtime(now-24*60*60))))
    if time.strftime("%A, %B ",time.gmtime(now-24*60*60))+fancyDay in prevPost.title:
        match = re.search(r"Yes \| No\n---\|--\n([0-9]+) \| ([0-9]+)",prevPost.selftext)
        yes = int(match.group(1))
        no = int(match.group(2))
        if yes > no:
            description = "Jeff was watered during this gif."
        else:
            description = "Jeff was not watered during this gif."
    else:
        description = "Failed to find watering result for this day."
    Logbook.append(" * Result was: "+description+". Uploading to Imgur...")
    # Upload to imgur
    config = {"album":DAY_AL,"title":time.strftime("%y-%m-%d",time.gmtime(now-24*60*60)),"description":description}
    t=0
    uploaded = imgurUp(gifPath,config)
    if uploaded:
        Logbook.append(" * Almost there. Making post...")
        rPost = R.subreddit(subreddit).submit("[DPG] Daily Plant Gif for "+time.strftime("%A, %B ",time.gmtime(now-24*60*60))+fancyDay,url=uploaded['link']+"v")
        rPost.reply(description+"\n\n[Click here for more daily plant gifs](https://www.reddit.com/r/"+subreddit+"/search?q=%5BDPG%5D&restrict_sr=on&sort=relevance&t=all)"
                      " or [click here to see them all at once](http://imgur.com/a/"+DAY_AL+")")
        Logbook.append(" * Post made. Go me!")
    else:
        Logbook.append(' * The gif did not upload to imgur and it failed.')
    if "--force" not in args:
        import shutil
        saved = [ time.strftime("%y-%m-%d-%H",time.gmtime(now - i*24/3*60*60)) for i in [0,1,2] ]
        forMonth = None
        for date in saved:
            for img in images:
                if date in img:
                    if not forMonth:
                        forMonth = img
                    shutil.copy2(filepath+"dailies/"+img,filepath+"weeklies/"+img)
                    break
        try:
            shutil.copy2(filepath+"dailies/"+forMonth,filepath+"monthlies/"+forMonth)
        except:
            Logbook.append(' * Moving the daily image to the monthly folder failed')
        for f in images:
            os.remove(filepath+"dailies/"+f)
    else:
        Logbook.append(" * No cleanup done. Manually move/delete images.")
    Logbook.append(" * Cleanup sucessful.")

    
def makeWeeklyGif(R,Im):
    Logbook.append("\n#WPG\n")
    now = time.time()
    ia = []
    images = [f for f in sorted(os.listdir(filepath+"weeklies/")) if f[-3:] == "png"]
    Logbook.append(" * Images found. Assembling")
    for filename in images:
        try:
            I = Image.open(filepath+"weeklies/"+filename)
            ia.append(I)
        except:
            continue
    Logbook.append(" * Assembled. Saving gif")
    first = ia[0]
    gifpath = filepath+"weeklies/"+time.strftime("%y-%W",time.gmtime(now))+".gif"
    compressSave(first,gifPath,ia)
    Logbook.append(" * Saved. Starting imgur upload process")
    description = "Stills taken from "+time.strftime("%y-%m-%d",time.gmtime(now-6*24*60*60))+" through "+time.strftime("%y-%m-%d",time.gmtime(now))
    Logbook.append(" * description made")
    config = {"album":WEK_AL,"title":time.strftime("Week ending: %y-%m-%d",time.gmtime(now)),"description":description}
    Logbook.append(" * Config made. uploading now")
    uploaded = imgurUp(gifPath,config)
    if uploaded:
        Logbook.append(" * Uploaded. Making post")
        rPost = R.subreddit(subreddit).submit("[WPG] Weekly Plant Gif for "+time.strftime("%y-%m-%d",time.gmtime(now-6*24*60*60))+" through "+time.strftime("%y-%m-%d",time.gmtime(now)),url=uploaded['link']+"v")
        rPost.reply("[Click here for more weekly plant gifs](https://www.reddit.com/r/"+subreddit+"/search?q=%5BWPG%5D&restrict_sr=on&sort=relevance&t=all)"
                      " or [click here to see them all at once](http://imgur.com/a/"+WEK_AL+")")
        Logbook.append(" * Post made. Go me! Cleaning up")
    else:
        Logbook.append(" * Gif not uploaded to imgur.")
    for f in images:
        os.remove(filepath+"weeklies/"+f)
    Logbook.append(" * Cleanup successful. Weekly gif over")


def makeMonthlyGif(R,Im):
    Logbook.append("\n#MPG\n")
    now = time.time()
    ia = []
    images = [f for f in sorted(os.listdir(filepath+"monthlies/")) if f[-3:] == "png"]
    Logbook.append(" * Images found. Assembling")
    for filename in images:
        try:
            I = Image.open(filepath+"monthlies/"+filename)
            ia.append(I)
        except:
            continue
    first = ia[0]
    gifPath = filepath+"monthlies/"+time.strftime("%y-%m",time.gmtime(now-24*60*60))+".gif"
    Logbook.append(" * Images assembled. Saving...")
    compressSave(first,gifPath,ia)
    Logbook.append(" * Saved. Uploading to Imgur")
    description = "Stills taken every day in "+time.strftime("%B",time.gmtime(now-15*24*60*60))
    config = {"album":MTH_AL,"title":time.strftime("%B %Y",time.gmtime(now-15*24*60*60)),"description":description}
    uploaded = imgurUp(gifPath,config)
    if uploaded:
        Logbook.append(" * Upload successful. Making post.")
        rPost = R.subreddit(subreddit).submit("[MPG] Monthly Plant Gif for "+time.strftime("%B %Y",time.gmtime(now-15*24*60*60)),url=uploaded['link']+"v")
        rPost.reply("[Click here for more monthly plant gifs](https://www.reddit.com/r/"+subreddit+"/search?q=%5BMPG%5D&restrict_sr=on&sort=relevance&t=all)"
                      " or [click here to see them all at once](http://imgur.com/a/"+MTH_AL+")")
        Logbook.append(" * Post made.")
    else:
        Logbook.append(" * Gif not uploaded to imgur.")
    for f in images:
        os.remove(filepath+"monthlies/"+f)
    Logbook.append(" * Cleanup successful")

args = [arg for arg in argv]



if __name__ == "__main__":
    start = time.gmtime()
    if "--force" not in args:
        getImage()
    if (int(time.strftime("%H",start)) == 19 and int(time.strftime("%M",start)) < 15 ) or '--force' in args:
        import praw
        from imgurpython import ImgurClient
        R = praw.Reddit(client_id=R_CLID,
                        client_secret=R_SCRT,
                        password=R_PASS,
                        user_agent="Making gifs of Jeff the plant for /r/"+subreddit+" by /u/"+MY_REDDIT_USER,
                        username=R_USER)
        Im = ImgurClient(I_CLID,I_SCRT,I_AXSS,I_REFR)
        if int(time.strftime("%d",start)) == 1:
            try:
                makeMonthlyGif(R,Im)
            except Exception as e:
                Logbook.append(e)
        try:
            makeDailyGif(R,Im)
        except Exception as e:
            Logbook.append(e)
        if int(time.strftime("%w",start)) == 1:
            try:
                makeWeeklyGif(R,Im)
            except Exception as e:
                Logbook.append(e)
    if "--force" not in args and "--test" not in args:
        try:
            R.redditor(MY_REDDIT_USER).message("Gif Logbook","\n".join(Logbook))
        except:
            pass
    else:
        print("\n".join(Logbook))
