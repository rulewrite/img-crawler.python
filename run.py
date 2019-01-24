import os
import sys
import requests
from bs4 import BeautifulSoup
from PIL import Image as PILImage

'''
TODO: list
- 속도개선 (이미지 병합 부분, 불필요한 저장부분, PIL 삭제 :: readlines() > requiements.txt 최신화)
- 인자 받기
- ui 툴로 컨버팅
- url parameter로 처리 불가한 웹페이지 (next 버튼)
- 모듈화, 분할
- err log 텍스트 파일
'''

sameFileNamePass = True
name = ''

urlOrigin = ''
urlPath = ''
imgSelector = ''

startParam = None
endParam = None
nextSelector = ''

#-------- init
loopType = None
if not startParam is None:
    loopType = 'param'
elif not nextSelector is None:
    loopType = 'selector'
else:
    print('ERROR:: Require parameter not defiend')
    # quit()
    sys.exit(1)

if (urlOrigin[-1:] == '/'): urlOrigin = urlOrigin[:-1]
if (urlPath[0] != '/'): urlPath = '/' + urlPath

outputDir = './' + name + '/'
outputImgFileNameBase = outputDir + name + '_img_%d'

#-------- function declaration
def getExtension(filename):
    ext = '.'.join(filename.split('.')[1:])
    return '.' + ext if ext else '.jpg'

def reqCheck(url):
    try:
        res = requests.get(url)
        if (200 > res.status_code or res.status_code >= 300):
            print('ERROR:: HTTP status code: %s' % res.status_code)
            res = False
    except:
        print('ERROR:: HTTP request error.')
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

#-------- start logic
print('=' * 30)

# mkdir
try:
    if not (os.path.isdir(outputDir)):
        print('Directory create "%s"' % outputDir)
        os.makedirs(outputDir)
except OSError as err:
    print('ERROR:: Failed to make directory: ', err)
    sys.exit(1)

# loop start
resultMsg = ''
fileNum = 0
selectorEmptyCnt, pageReqErrCnt, imgReqErrUrl = 0, 0, False

nowUrl = None
nowParam = startParam
nextElements = None
def breakCheck():
    global resultMsg
    isContinue = True
    if (imgReqErrUrl != False):
        resultMsg = 'BREAK:: %d page(param: %d) in image name "%s" request error' % (fileNum, nowParam, imgReqErrUrl)
        isContinue = False
    elif (selectorEmptyCnt >= 5):
        resultMsg = 'BREAK:: Selector empty count (%d).' % selectorEmptyCnt
        isContinue = False
    elif (pageReqErrCnt >= 5):
        resultMsg = 'BREAK:: Page request error count (%d).' % pageReqErrCnt
        isContinue = False
    else:
        global nowUrl
        if (loopType == 'param'):
            if (not endParam is None and nowParam >= endParam):
                resultMsg = 'DONE:: Page loop is end. Done.'
                isContinue = False
            else:
                nowUrl = urlOrigin + urlPath % nowParam
        elif (loopType == 'selector'):
            global nextElements
            # init
            if nextElements is None:
                nowUrl = urlOrigin + urlPath
            else:
                # href를 찾고 nextElements를 False 시킨뒤
                if (nextElements is False or not len(nextElements)):
                    resultMsg = 'DONE:: Next element is empty'
                    isContinue = False
                else:
                    found = False
                    for nextEl in nextElements:
                        nextElHref = nextEl.get('href')
                        if not nextElHref is None:
                            '''
                            FIXME:
                            - if href is not url
                                - javascript:alert('is Last.')
                                - #id
                            - click event
                            '''
                            nowUrl = getAbsoulteRoute(nextElHref)
                            found = True
                            break
                        
                    if found:
                        nextElements = False
                    else:
                        resultMsg = 'BREAK:: cat\'t found attr "href"'
                        isContinue = False
    return isContinue

while breakCheck():
    print('-'*30)
    fileNum += 1
    ext = None
    outputImgFileNameYetExt = outputImgFileNameBase % fileNum
    thisPagePass = False
    print('%d page crawling' % fileNum)

    # HTTP GET request
    res = reqCheck(nowUrl)
    if not res:
        print('|- Page request error. go to next')
        pageReqErrCnt += 1
        continue

    # html.parsing
    bs = BeautifulSoup(res.text, 'html.parser')
    imgTags = bs.select(imgSelector)
    if not len(imgTags):
        print('|- Selector empty result. go to next')
        selectorEmptyCnt += 1
        continue

    # loop tempImg
    print('|- found %d images' % len(imgTags))
    tempImgArr = []
    fullWidth, fullHeight = 0, 0
    for imgTag in imgTags:
        src = imgTag.get('src')
        # relative, absoulte root
        imgUrl = getAbsoulteRoute(src)

        # get img
        imgRes = reqCheck(imgUrl)
        if not imgRes:
            print('|- image request error')
            imgReqErrUrl = imgUrl
            break

        # set extention
        if ext is None: 
            ext = getExtension(os.path.basename(src))
            # already file pass
            if sameFileNamePass and os.path.isfile(outputImgFileNameYetExt + ext):
                thisPagePass = True
                break
        tempImgFileName = getUniqueFileName(outputImgFileNameYetExt + '_temp_%d' % len(tempImgArr), ext)

        # append img
        with open(tempImgFileName, 'wb') as f:
            # img write
            f.write(imgRes.content)

            try:
                tempImg = PILImage.open(tempImgFileName)
                width, height = tempImg.size
                tempImgArr.append(tempImg)

                # stack outputImg height
                fullHeight += height
                if (fullHeight > 65500):
                    print('| %d page is too large so divide save' % fileNum)
                    fullHeight -= height
                    saveImg(tempImgArr[:-1], fullWidth, fullHeight, getUniqueFileName(outputImgFileNameYetExt, ext))
                    tempImgArr = [tempImg]
                    fullHeight = height
                    fullWidth = 0
                
                # set outputImg max width
                fullWidth = max(fullWidth, width)

                # img remove
                os.remove(tempImgFileName)
            except:
                print('ERROR:: Pillow Err outputfileNmae: "%s", tempImgName: "%s"' % (outputImgFileNameYetExt, tempImgFileName))

    if (thisPagePass):
        print('CONTINUE:: %d page is already' % fileNum)
        continue
    
    if (len(tempImgArr)):
        # merge imgs in page
        saveImg(tempImgArr, fullWidth, fullHeight, getUniqueFileName(outputImgFileNameYetExt, ext))
        print('|- saved')
    else:
        print('|- empty images. unsaved')

    # prevent next url
    if (loopType == 'param'):
        nowParam += 1
    elif (loopType == 'selector'):
        nextElements = bs.select(nextSelector)

resultMsg += '\nloop total: %d' % fileNum
print('='*30)
print(resultMsg)
print('='*30)