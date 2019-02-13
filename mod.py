import os  # dir, file handling
import re  # regex
import time
import requests
from PIL import Image as PILImage  # img merge

if __name__ != '__main__':
    logTxt = ''

    def handleLog(addTxt=None, outputDir='./'):
        global logTxt
        if (addTxt is None):
            now = time.localtime()
            with open(outputDir + 'log_%02d%02d%02d_%02d%02d%02d.txt' % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec), 'w') as f:
                f.write(logTxt)
        else:
            print(addTxt)
            logTxt += addTxt + '\n'

    def saveImg(imgArr, fullWidth, fullHeight, filename):
        canvas = PILImage.new('RGB', (fullWidth, fullHeight), 'white')
        pasteHeightPosition = 0
        for img in imgArr:
            height = img.size[1]
            canvas.paste(img, (0, pasteHeightPosition))
            pasteHeightPosition += height
        canvas.save(filename)

    urlRegex = re.compile(r'[^a-zA-Z0-9&#?_=.:/%]')

    class VALID():
        @staticmethod
        def url(url):
            return not urlRegex.search(url)

        @staticmethod
        def req(url):
            try:
                res = requests.get(url)
                if (200 > res.status_code or res.status_code >= 300):
                    handleLog(
                        '| ERROR:: HTTP status code: %s' %
                        res.status_code)
                    res = False
            except BaseException:
                handleLog('| ERROR:: HTTP request error')
                res = False
            return res

    class GET():
        @staticmethod
        def extension(filename):
            ext = '.'.join(filename.split('.')[1:])
            return '.' + ext if ext else '.jpg'

        @staticmethod
        def uniqueFileName(filename, ext):
            if (os.path.isfile(filename + ext)):
                filename += ' (%d)'
                idx = 1
                while os.path.isfile(filename % idx + ext):
                    idx += 1
                filename = filename % idx
            return filename + ext

        @staticmethod
        def uniqueDirName(dirName):
            if (os.path.isdir(dirName)):
                dirName += ' (%d)'
                idx = 1
                while os.path.isdir(dirName % idx):
                    idx += 1
                dirName = dirName % idx
            return dirName

        @staticmethod
        def absoluteRoute(urlDomain, route):
            return route if '//' in route else urlDomain + route
