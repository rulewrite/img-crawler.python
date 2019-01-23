import os
import sys
import requests
from bs4 import BeautifulSoup
from PIL import Image as PILImage

'''
TODO: list
- 속도개선 (이미지 병합 부분, 불필요한 저장부분, PIL 삭제 > requiements.txt 최신화)
- 인자 받기
- ui 툴로 컨버팅
- url parameter로 처리 불가한 웹페이지 (next 버튼)
- 모듈화, 분할
'''

#-------- init
baseUrl = ''
if (baseUrl[-1:] == '/'): baseUrl = baseUrl[:-1]
basePath = ''
if (basePath[0] != '/'): basePath = '/' + basePath
imgSelector = ''

name = ''
outputDir = './' + name + '/'
outputImgFileNameBase = outputDir + name + '_img_%d'

startParam = 3
endParam = 4

#-------- start logic
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

# mkdir
try:
    if not (os.path.isdir(outputDir)):
        print('Directory create "%s"' % outputDir)
        os.makedirs(outputDir)
except OSError as err:
    print('ERROR:: Failed to make directory: ', err)
    # quit()
    sys.exit(1)

# loop start
resultMsg = ''
fileNum = 0
nowParam = (startParam-1)
selectorEmptyCnt, pageReqErrCnt, imgReqErrUrl = 0, 0, False
def breakCheck():
    global resultMsg
    isContinue = True
    if (imgReqErrUrl != False):
        resultMsg = 'BREAK:: %d page(param: %d) in image name "%s" request error' % (fileNum, nowParam, imgReqErrUrl)
        isContinue = False
    else:
        if (endParam):
            if (nowParam >= endParam):
                resultMsg = 'DONE:: Page loop is end. Done.'
                isContinue = False
        else:
            if (selectorEmptyCnt >= 5):
                resultMsg = 'BREAK:: Selector empty count (%d).' % selectorEmptyCnt
                isContinue = False
            elif (pageReqErrCnt >= 5):
                resultMsg = 'BREAK:: Page request error count (%d).' % pageReqErrCnt
                isContinue = False
    return isContinue

while breakCheck():
    print('-'*30)
    fileNum += 1
    nowParam += 1
    outputImgFileName = outputImgFileNameBase % fileNum
    print('%d page crawling' % fileNum)

    # HTTP GET request
    url = baseUrl + basePath
    res = reqCheck(url % nowParam)
    if not res:
        print('|- Page request error. go to next')
        pageReqErrCnt += 1
        continue

    # html.parsing
    imgTags = BeautifulSoup(res.text, 'html.parser').select(imgSelector)
    if not (len(imgTags)):
        print('|- Selector empty result. go to next')
        selectorEmptyCnt += 1
        continue

    # loop tempImg
    print('|- found %d images' % len(imgTags))
    ext = None
    tempImgArr = []
    fullWidth, fullHeight = 0, 0
    for imgTag in imgTags:
        src = imgTag.get('src')
        # relative, absoulte root
        imgUrl = src if ('//' in src) else baseUrl + src

        # set extention
        if not ext: ext = getExtension(os.path.basename(src))

        tempImgFileName = getUniqueFileName(outputImgFileName + '_temp', ext)

        # get img
        imgRes = reqCheck(imgUrl)
        if not imgRes:
            print('|- image request error')
            imgReqErrUrl = imgUrl
            break

        # append img
        with open(tempImgFileName, 'wb') as f:
            # img write
            f.write(requests.get(imgUrl).content)
            
            tempImg = PILImage.open(tempImgFileName)
            width, height = tempImg.size
            tempImgArr.append(tempImg)
            # set outputImg max width
            fullWidth = max(fullWidth, width)
            # stack outputImg height
            fullHeight += height
            
            # img remove
            os.remove(tempImgFileName)

    if (len(tempImgArr)):
        # merge imgs in page
        canvas = PILImage.new('RGB', (fullWidth, fullHeight), 'white')
        pasteHeightPosition = 0
        for tempImg in tempImgArr:
            width, height = tempImg.size
            canvas.paste(tempImg, (0, pasteHeightPosition))
            pasteHeightPosition += height
        
        # save
        canvas.save(getUniqueFileName(outputImgFileName, ext))

        print('|- saved')
    else:
        print('|- empty images. unsaved')

resultMsg += '\nloop total: %d' % fileNum
print('='*30)
print(resultMsg)
print('='*30)