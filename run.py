import os
import sys
import time
import requests
from bs4 import BeautifulSoup
from PIL import Image as PILImage

'''
TODO: list
- 속도개선 (이미지 병합 부분, 불필요한 저장부분, PIL 삭제 :: readlines() > requiements.txt 최신화)
- 인자 받기
- ui 툴로 컨버팅
- 모듈화, 분할
- 다음 버튼 엘리먼트의 href 속성이 아닌 click event로 결려 있을 경우
'''

#=============================== set parameter
sameFileNamePass = True
name = ''

urlOrigin = ''
urlPath = ''
imgSelector = ''

startParam = None
endParam = None
nextSelector = ''

#=============================== init
logTxt = ''
loopType = None
if not startParam is None:
    loopType = 'param'
elif not nextSelector is None:
    loopType = 'selector'
else:
    print('ERROR:: Require parameter undefiend')
    # quit()
    sys.exit(1)

if (urlOrigin[-1:] == '/'): urlOrigin = urlOrigin[:-1]
if (urlPath[0] != '/'): urlPath = '/' + urlPath

outputDir = './' + name + '/'
outputImgFileNameBase = outputDir + name + '_img_%d'

#=============================== function declaration
def handleLog(addTxt = None):
    global logTxt
    if (addTxt is None):
        now = time.localtime()
        with open(outputDir + 'log_%02d%02d%02d_%02d%02d%02d.txt' % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec), 'w') as f:
            f.write(logTxt)
    else:
        print(addTxt)
        logTxt += addTxt + '\n'

def getExtension(filename):
    ext = '.'.join(filename.split('.')[1:])
    return '.' + ext if ext else '.jpg'

def reqCheck(url):
    try:
        res = requests.get(url)
        if (200 > res.status_code or res.status_code >= 300):
            handleLog('ERROR:: HTTP status code: %s' % res.status_code)
            res = False
    except:
        handleLog('ERROR:: HTTP request error')
        res = False
    return res

def getUniqueFileName(filename, ext):
    if (os.path.isfile(filename + ext)):
        filename += ' (%d)'
        idx = 1
        while os.path.isfile(filename % idx + ext):
            idx += 1
        filename = filename % idx
    return filename + ext

def getAbsoulteRoute(route):
    return route if '//' in route else urlOrigin + route

def saveImg(imgArr, fullWidth, fullHeight, filename):
    canvas = PILImage.new('RGB', (fullWidth, fullHeight), 'white')
    pasteHeightPosition = 0
    for img in imgArr:
        height = img.size[1]
        canvas.paste(img, (0, pasteHeightPosition))
        pasteHeightPosition += height
    canvas.save(filename)

#=============================== start logic
# mkdir
try:
    if not (os.path.isdir(outputDir)):
        print('Directory create "%s"' % outputDir)
        os.makedirs(outputDir)
except OSError as err:
    print('ERROR:: Failed to make directory: ', err)
    sys.exit(1)

# loop start
fileNum = 0

nowUrl = ''
nowParam = startParam
bs = None
selectorEmptyCnt, pageReqErrCnt, imgReqErrUrl = 0, 0, False

resultMsg = ''
def handleLoop():
    global resultMsg
    isContinue = True
    if (imgReqErrUrl != False):
        resultMsg = 'BREAK:: image url "%s" request error' % imgReqErrUrl
        isContinue = False
    elif (selectorEmptyCnt >= 5):
        resultMsg = 'BREAK:: Img tag empty count (%d).' % selectorEmptyCnt
        isContinue = False
    elif (pageReqErrCnt >= 5):
        resultMsg = 'BREAK:: Page request error count (%d).' % pageReqErrCnt
        isContinue = False
    else:
        global nowUrl
        if (loopType == 'param'):
            global nowParam
            if (not endParam is None and nowParam > endParam):
                resultMsg = 'DONE:: Param loop is done.'
                isContinue = False
            else:
                nowUrl = urlOrigin + urlPath % nowParam
                nowParam += 1
        elif (loopType == 'selector'):
            if bs is None:
                nowUrl = urlOrigin + urlPath
            else:
                nextEls = bs.select(nextSelector)
                if (len(nextEls)):
                    found = False
                    for nextEl in nextEls:
                        nextElHref = nextEl.get('href') # TODO: if href="javascript:alert('is Last.')"
                        if not nextElHref is None:
                            nowUrl = getAbsoulteRoute(nextElHref)
                            found = True
                            break
                    if found is False:
                        resultMsg = 'BREAK:: Cat\'t found attr "href"'
                        isContinue = False
                else:
                    resultMsg = 'DONE:: Next element is empty'
                    isContinue = False
    return isContinue

while handleLoop():
    fileNum += 1
    ext = None
    outputImgFileNameYetExt = outputImgFileNameBase % fileNum
    alreadyFile = False
    handleLog('-'*30 + '\n%d page crawling start' % fileNum)

    # HTTP GET page, html parsing
    handleLog('| %s' % nowUrl)
    res = reqCheck(nowUrl)
    if not res:
        handleLog('| Page request error > continue')
        pageReqErrCnt += 1
        continue
    bs = BeautifulSoup(res.text, 'html.parser')

    # get img
    imgTags = bs.select(imgSelector)
    if not len(imgTags):
        handleLog('| Img tag empty > continue')
        selectorEmptyCnt += 1
        continue
    handleLog('| found %d images' % len(imgTags))

    # loop img
    tempImgArr, fullWidth, fullHeight = [], 0, 0
    for imgTag in imgTags:
        imgSrc = imgTag.get('src')
        imgRoute = getAbsoulteRoute(imgSrc)

        # set extention
        if ext is None: 
            ext = getExtension(os.path.basename(imgSrc))
            # already file pass
            if sameFileNamePass and os.path.isfile(outputImgFileNameYetExt + ext):
                alreadyFile = True
                break

        # HTTP GET img
        imgRes = reqCheck(imgRoute)
        if not imgRes:
            handleLog('| Img request error > break')
            imgReqErrUrl = imgRoute
            break

        # append img
        tempImgFileName = getUniqueFileName(outputImgFileNameYetExt + '_temp_%d' % len(tempImgArr), ext)
        with open(tempImgFileName, 'wb') as f:
            f.write(imgRes.content)

            try:
                img = PILImage.open(tempImgFileName)
                width, height = img.size
                tempImgArr.append(img)

                # stack outputImg height
                fullHeight += height

                # jpg maximum height 65500
                if (fullHeight > 65500):
                    handleLog('| Too long so divide save' % fileNum)
                    fullHeight -= height
                    saveImg(tempImgArr[:-1], fullWidth, fullHeight, getUniqueFileName(outputImgFileNameYetExt, ext))
                    
                    tempImgArr = [img]
                    fullHeight = height
                    fullWidth = 0
                
                # set outputImg wider width
                fullWidth = max(fullWidth, width)

                # img remove
                os.remove(tempImgFileName)
            except:
                handleLog('| ERROR:: Pillow error outputImgFileName: %s, tempImgFileName: %s' % (outputImgFileNameYetExt, tempImgFileName))

    # merge imgs in page
    if (alreadyFile):
        handleLog('CONTINUE:: %d page is already' % fileNum)
        continue
        
    saveImg(tempImgArr, fullWidth, fullHeight, getUniqueFileName(outputImgFileNameYetExt, ext))
    handleLog('| Saved')

handleLog('='*30)
handleLog('loop total: %d' % fileNum)
handleLog(resultMsg)
handleLog('='*30)
handleLog()