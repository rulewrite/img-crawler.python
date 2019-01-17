import os
import requests
from bs4 import BeautifulSoup
import urllib.request
from PIL import Image as PILImage

# init
# todo 인자받기
name = ''
baseUrl = ''
# todo baseUrl 끝에 / 있음 자르기
basePath = ''
imgSelector = ''

outputDir = './' + name + '/'
outputImgFileNameBase = outputDir + name + '_img_%d%s'

startParam = 3
endParam = 6 # 안썻을때 req status보고 200 !== 시 정지, 셀릭터 10회 이상 비면 정지
endParam += 1

# start logic

def getExtension(filename):
    ext = '.'.join(filename.split('.')[1:])
    return '.' + ext if ext else '.jpg'

# todo mkdir

pageNum = 1
for i in range (startParam, endParam):
    print(str(pageNum) + '화 저장중...')

    ext = None
    tempImgArr = []
    fullWidth, fullHeight = 0, 0

    # HTTP GET request
    url = baseUrl + basePath
    req = requests.get(url % startParam) # todo !== 200 에러
    # get HTML soruce
    html = req.text

    # html.parsing
    soup = BeautifulSoup(html, 'html.parser')

    # loop tempImg
    for imgTag in soup.select(imgSelector):
        src = imgTag.get('src')
        imgUrl = src if ('//' in src) else baseUrl + src
        imgName = os.path.basename(imgUrl)
        tempImgFileName = outputDir + imgName

        # extention
        if not ext:
            ext = getExtension(imgName)

        # img save
        urllib.request.urlretrieve(imgUrl, tempImgFileName)
        # todo 파일명 중복시?
        # 엑박 이미지일 경우?

        tempImg = PILImage.open(tempImgFileName)
        width , height = tempImg.size
        tempImgArr.append(tempImg)
        # set outputImg max width
        fullWidth = max(fullWidth, width)
        # stack outputImg height
        fullHeight += height
        # img remove
        os.remove(tempImgFileName)

    # merge now page in img
    canvas = PILImage.new('RGB', (fullWidth, fullHeight), 'white')
    pasteHeightPosition = 0
    for tempImg in tempImgArr:
        width, height = tempImg.size
        canvas.paste(tempImg, (0, pasteHeightPosition))
        pasteHeightPosition += height
    
    # save
    canvas.save(outputImgFileNameBase % (pageNum, 'jpg'))

    print(str(pageNum) + '화 저장완료')
    pageNum += 1