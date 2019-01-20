import os
import sys
import requests
from bs4 import BeautifulSoup
from PIL import Image as PILImage

'''
todo list
- 속도개선
- 인자 받기
- ui 툴로 컨버팅
- requiements.txt 최신화 (urllib 삭제)
'''

#-------- init
name = ''
baseUrl = ''
# fixme baseUrl 끝에 / 있음 자르기
basePath = ''
imgSelector = ''

outputDir = './' + name + '/'
outputImgFileNameBase = outputDir + name + '_img_%d%s'

startParam = 4
endParam = 6

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

# mkdir 
try:
    if not (os.path.isdir(outputDir)):
        print('Directory create "%s"' % outputDir)
        os.makedirs(outputDir)
except OSError as e:
    print('ERROR:: Failed to make directory: ', e)
    # quit()
    sys.exit(1)

pageNum = 0
nowParam = (startParam-1)
selectorEmptyCnt, pageReqErrCnt, imgReqErrIdx = 0, 0, False
while True:
    # break check
    if (imgReqErrIdx != False):
            print('END:: %d page in image name %s request error' % (nowParam, imgReqErrIdx))
            break
    else:
        if (endParam):
            if (nowParam == endParam):
                print('END:: Page loop is end. Done.')
                break
        else:
            if (selectorEmptyCnt > 5):
                print('END:: Selector empty count (%d).' % selectorEmptyCnt)
                break
            elif (pageReqErrCnt > 5):
                print('END:: Page request error count (%d).' % pageReqErrCnt)
                break
    
    pageNum += 1
    nowParam += 1

    print(str(pageNum) + ' page crawling start')

    # HTTP GET request
    url = baseUrl + basePath
    res = reqCheck(url % nowParam)
    if not res:
        print('ERROR:: Page request error. go to next')
        if not (endParam): pageReqErrCnt += 1
        continue

    # html.parsing
    soup = BeautifulSoup(res.text, 'html.parser')

    # loop tempImg
    imgTags = soup.select(imgSelector)
    if not (len(imgTags)):
        print('ERROR::Selector empty result. go to next')
        if not (endParam): selectorEmptyCnt += 1
        continue

    print('found %d image' % len(imgTags))
    ext = None
    tempImgArr = []
    fullWidth, fullHeight = 0, 0
    for imgTag in imgTags:
        src = imgTag.get('src')
        # relative, absoulte root
        imgUrl = src if ('//' in src) else baseUrl + src
        imgName = os.path.basename(imgUrl)
        tempImgFileName = outputDir + imgName

        # extention
        if not ext: ext = getExtension(imgName)

        # get img
        imgRes = reqCheck(imgUrl)
        if not imgRes:
            print('ERROR:: Image request error')
            imgReqErrIdx = imgName
            break

        # append img
        # fixme 파일명 중복시 파일명 뒤에 (1) 붙이기
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

    if (imgReqErrIdx != False): continue

    # merge imgs in page
    canvas = PILImage.new('RGB', (fullWidth, fullHeight), 'white')
    pasteHeightPosition = 0
    for tempImg in tempImgArr:
        width, height = tempImg.size
        canvas.paste(tempImg, (0, pasteHeightPosition))
        pasteHeightPosition += height
    
    # save
    canvas.save(outputImgFileNameBase % (pageNum, ext))

    print(str(pageNum) + ' page saved')
