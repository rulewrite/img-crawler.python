import os
import sys
import time
import re
import requests
from bs4 import BeautifulSoup
from PIL import Image as PILImage

'''
TODO: list
- ui 툴로 컨버팅
- 다음 버튼 엘리먼트의 href 속성이 아닌 click event로 결려 있을 경우
- 속도개선 (이미지 병합 부분, 불필요한 저장부분, PIL 삭제 :: readlines() > requiements.txt 최신화)
- 모듈화, 분할
'''

#=============================== set parameter
name = ''
imgSelector = ''
urlDomain = ''
urlPath = ''

startParam = None
endParam = None
nextSelector = ''

if __name__ == '__main__':
    argvLength = len(sys.argv)
    if (argvLength < 6):
        print('''
        $ python run.py (name) (img selector) (protocol + domain) (path + query) (start param [, end param] || next url element selector)
        
        name 
            저장될 디렉토리 및 이미지 파일명

        img selector
            이미지 파일의 CSS 선택자
            ex. `.img-wrapper > img`

        protocol + domain
            프로토콜과 .com, .org등으로 끝나는곳까지의 홈페이지 주소
            ex. `https://example.com`

        path + query
            크롤링할 페이지 주소의 패스 + 파라미터 (쿼리)
            - param 사용시 치환될 부분을 `%s`로 표기
              ex. `/img/view?page=%s`
              
            - 다음 주소를 특정 element로부터 가져와야할 시 그대로 입력
              입력한 패스 + 파라미터부터 시작

        start param [, end param] || next url element selector
            - start param
              only number, 크롤링이 시작될 파라미터
              path + query에 입력한 `%s`로 start param에서 1씩 더해가며 값을 치환하여 순환
              end param is optional, 없으면 더이상 이미지를 가져올 수 없을때까지 반복

            - next url element selector
              다음 페이지 주소를 element로부터 받아와야되는 경우
              href속성에 담고 있는 element의 선택자를 입력
              ex. `a.next-btn`
        ''')
        # quit()
        sys.exit(1)
    else:
        name = sys.argv[1]
        imgSelector = sys.argv[2]
        urlDomain = sys.argv[3]
        urlPath = sys.argv[4]

        if '%s' in urlPath:
            startParam = sys.argv[5]
            if argvLength > 6:
                endParam = sys.argv[6]
        else:
            nextSelector = sys.argv[5]

#=============================== parameter validation
urlRegex = re.compile(r'[^a-zA-Z0-9&#?_=.:/(%s)]')
def checkValidUrl(url):
    return not urlRegex.search(url)

# TODO: imgSelector, nextSelector 선택자 밸리데이션

if (checkValidUrl(urlDomain)):
    if (urlDomain[-1:] == '/'): urlDomain = urlDomain[:-1]
else:
    print('ERROR:: Invalid domain')
    sys.exit(1)

if (checkValidUrl(urlPath)):
    if (urlPath[0] != '/'): urlPath = '/' + urlPath
else:
    print('ERROR:: Invalid url path')
    sys.exit(1)

if not startParam is None:
    try:
        startParam = int(startParam)
        if not endParam is None:
            endParam = int(endParam)
    except ValueError as err:
        print('ERROR:: %s param is only number' % ('End' if type(startParam) is int else 'Start'))
        sys.exit(1)

#=============================== init
loopType = None
if not startParam is None:
    loopType = 'param'
elif not nextSelector is None:
    loopType = 'selector'

logTxt = ''
sameFileNamePass = True
outputDir = './' + name + '/'
outputImgFileNameBase = outputDir + name + '_img_%d'

# mkdir
if not (os.path.isdir(outputDir)):
    try:
        print('Directory create "%s"' % outputDir)
        os.makedirs(outputDir)
    except OSError as err:
        print('ERROR:: Failed to make directory: ', err)
        sys.exit(1)

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
    return route if '//' in route else urlDomain + route

def saveImg(imgArr, fullWidth, fullHeight, filename):
    canvas = PILImage.new('RGB', (fullWidth, fullHeight), 'white')
    pasteHeightPosition = 0
    for img in imgArr:
        height = img.size[1]
        canvas.paste(img, (0, pasteHeightPosition))
        pasteHeightPosition += height
    canvas.save(filename)

#=============================== start logic
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
                nowUrl = urlDomain + urlPath % nowParam
                nowParam += 1
        elif (loopType == 'selector'):
            if bs is None:
                nowUrl = urlDomain + urlPath
            else:
                nextEls = bs.select(nextSelector)
                if (len(nextEls)):
                    found = False
                    for nextEl in nextEls:
                        nextElHref = nextEl.get('href')
                        if checkValidUrl(nextElHref):
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