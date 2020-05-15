import re
import shutil
import threading
import zipfile
from bs4 import BeautifulSoup
import urllib.request
import csv
import os
import datetime

url = "https://patchstorage.com/platform/zoia/page/{}/"

## Do Not Change
savePath = os.path.join("downloaded", str(datetime.datetime.now()).split(".")[0])
zoiaFriendly = os.path.join(savePath, "ZOIA_SD")
raw_downloads = os.path.join(savePath, "raw_downloads")

patches = []
title = []
author = []
tags = []
description = []
dlLink = []
category = []
platform = []
workstatus = []
patchLicense = []
revision = []
views = []

csvdest = "downloaded"
# threads = list()
Que = 0


def download_url(url, save_path, chunk_size=8):
    with urllib.request.urlopen(url) as response, open(save_path, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)


def extractZip(zipFile, dest):
    with zipfile.ZipFile(zipFile) as zf:
        zf.extractall(dest)


def getNewBinName(fileName):
    if fileName.lower().startswith("zoia"):
        return "063_" + str(fileName)
    else:
        return fileName.replace(re.match(re.compile("[0-9]{3}"), fileName)[0], "063")


def downloadHelper(url):
    print("Downloading", url)

    zipExtention = ["zip", "rar", "tar", "7z"]
    if str(url).lower().split(".")[-1:] in zipExtention:
        file = os.path.basename(url)
        # Download to raw downloads
        download_url(url, os.path.join(raw_downloads, file))

        # uncompress to zoia folder
        os.makedirs(os.path.join(zoiaFriendly, file))
        extractZip(os.path.join(raw_downloads, file), os.path.join(zoiaFriendly, file))

        extractedPath = os.path.join(zoiaFriendly, file)
        extractedLst = os.listdir(extractedPath)

        # for i in extractedLst/:
        #     if i.endswith("bin"):
        #         os.rename(os.path.join(extractedPath, i), os.path.join(extractedPath, getNewBinName(i)))

    elif str(url).lower().endswith("bin"):

        file = os.path.basename(url)
        download_url(url, os.path.join(raw_downloads, file))

        patchName = str(file).split("_")[-1:][0]
        # print(patchName)
        patchFolder = os.path.join(zoiaFriendly, file)
        # print(patchFolder)
        os.makedirs(patchFolder)
        shutil.copyfile(os.path.join(raw_downloads, file), os.path.join(patchFolder, file))
        os.rename(os.path.join(patchFolder, file), os.path.join(patchFolder, getNewBinName(file)))


    else:
        # Other formats Just download to raw Downloads
        file = os.path.basename(url)
        download_url(url, os.path.join(raw_downloads, file))

        # Extract Zip


def get_url(url):
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
    # Other available agents
    USER_AGENTS = [
        ('Mozilla/5.0 (X11; Linux x86_64) '
         'AppleWebKit/537.36 (KHTML, like Gecko) '
         'Chrome/57.0.2987.110 '
         'Safari/537.36'),  # chrome
        ('Mozilla/5.0 (X11; Linux x86_64) '
         'AppleWebKit/537.36 (KHTML, like Gecko) '
         'Chrome/61.0.3163.79 '
         'Safari/537.36'),  # chrome
        ('Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:55.0) '
         'Gecko/20100101 '
         'Firefox/55.0'),  # firefox
        ('Mozilla/5.0 (X11; Linux x86_64) '
         'AppleWebKit/537.36 (KHTML, like Gecko) '
         'Chrome/61.0.3163.91 '
         'Safari/537.36'),  # chrome
        ('Mozilla/5.0 (X11; Linux x86_64) '
         'AppleWebKit/537.36 (KHTML, like Gecko) '
         'Chrome/62.0.3202.89 '
         'Safari/537.36'),  # chrome
        ('Mozilla/5.0 (X11; Linux x86_64) '
         'AppleWebKit/537.36 (KHTML, like Gecko) '
         'Chrome/63.0.3239.108 '
         'Safari/537.36'),  # chrome
    ]
    # headers = {'User-Agent': USER_AGENTS[0], }
    headers = {'User-Agent': user_agent, }
    request = urllib.request.Request(url, None, headers)  # The assembled request
    return urllib.request.urlopen(request)


threads = list()


def getPatchLinks():
    # Getting all possible patches
    page = 1
    # Scrap from all available pages
    while get_url(url.format(page)).getcode() == 200:
    # Scrap only from page 1 through 10
    # for page in range(1,10):
        print("Getting Page " + str(page) + " patches.......")
        data = get_url(url.format(page)).read()  # The data u need
        soup = BeautifulSoup(data, "html.parser")
        cards = soup.findAll("div", {"class": "card"})
        for i in cards:
            patchLinks = i.find("a", {"class": "hover-gradient"}, href=True)
            try:
                if patchLinks['href']:
                    patches.append(patchLinks['href'])
                    dlLink = i.find('a', {"class", "btn btn-secondary btn-xs"}, href=True)['href']

                    x = threading.Thread(target=addToCSV, args=(patchLinks['href'],))
                    threads.append(x)
                    x.start()
                    downloadHelper(dlLink)
            except:
                pass
        page += 1
    print("========================== PatchStorage Page Bottom ==========================")


# def isDownloaded(checkTitle, patchVersion):
#     # Check if downloaded before or any new updates.
#     for t in range(0, len(csvTitleHistory)):
#         if csvTitleHistory[t] == checkTitle:
#             if patchVersion > csvRevisionHistory[t]:
#                 return False  # New Version Needs re-download
#             else:
#                 return True
#     # No records found
#     return False


def addToCSV(p):
    if get_url(p).getcode() == 200:
        patchPage = get_url(p).read()
        soup = BeautifulSoup(patchPage, "html.parser")

        # Get Download Link
        l = soup.find("a", {"class", "btn btn-danger btn-block m-b-10 text-white"}, href=True)
        dlLink.append(l['href'])

        # Get title
        patchTitle = soup.find("h2", {"class": "blog-post text-break"}, text=True)
        title.append(patchTitle.getText())

        # Get Author
        patchAuthorDiv = soup.find("div", {"class": "h4 no-m color-white author-link"}, text=True)
        authorABlock = patchAuthorDiv.find("a", text=True)
        author.append(authorABlock.getText())

        # Get Description
        patchDesDiv = soup.find("div", {"class", "single-content"})
        # print(patchDesDiv.getText())

        # Get Tags
        tagsas = soup.find("span", {"class", "tags-in grid-tags"}).findAll("a")
        tagsBuilder = ""
        for t in tagsas:
            tagsBuilder += t.getText() + " "
        tags.append(tagsBuilder)

        # Append Patch Description to CSV file
        with open(csvdest, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(
                [patchTitle.getText(), p, authorABlock.getText(), l['href'], patchDesDiv.getText(), tagsBuilder])

        # Get infos not properly parsed yet
        # patchInfoUL = soup.find("ul", {"class", "list-group list-group-flush"})
        # infolis = patchInfoUL.findAll("li")
        # for lis in range(0, 7):
        #     # try:
        #     currli = infolis[lis]
        #     if lis == 1:
        #         try:
        #             currli.find("span", {"class", "text-primary"})
        #             workstatus.append(currli.getText().split(":")[1][1:])
        #         except:
        #             workstatus.append("Done")
        #     if lis == 2:
        #         print(k)
        #         platform.append(currli.findAll("a")[0].getText())
        #     if lis == 3: category.append(currli.getText().split(":")[1][1:])
        #     if lis == 4:
        #         t = currli.findAll("span")
        #         if len(t) > 1:
        #             # print(t[1].getText())
        #             revision.append(t[1].getText())
        #     if lis == 5: patchLicense.append(currli.getText().split(":")[1][1:])
        #     if lis == 6: views.append(currli.getText().split(":")[1][1:])
        # except:
        #     print("parsingError")


if __name__ == '__main__':
    try:
        os.makedirs(savePath)
        os.makedirs(zoiaFriendly)
        os.makedirs(raw_downloads)

        csvdest = os.path.join(savePath, "downloadLog.csv")
        if not os.path.exists(csvdest):
            with open(csvdest, 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Title", "Patch Link", "Author", "Download Link", "Descriptions", "Tags"])

    except OSError:
        print("Creation of the directory %s failed" % savePath)

    getPatchLinks()
