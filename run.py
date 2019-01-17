import os
import requests
from bs4 import BeautifulSoup

# init
name = ''
baseUrl = ''
# todo baseUrl 끝에 / 있음 자르기
basePath = ''

startParam = '3'
endParam = '189'

imgSelector = ''

outputDir = '~/' + name
outputImgFileNameBase = name + '_img_'


# todo 반복시작

# HTTP GET request
url = baseUrl + basePath
req = requests.get(url % startParam)

# get HTML soruce
html = req.text

# html.parsing
soup = BeautifulSoup(html, 'html.parser')

# select
imgs = soup.select(imgSelector)

for img in imgs:
    src = img.get('src')
    getSrc = src if ('//' in src) else baseUrl + src
    # todo 이미지 다운, 병합, 저장
    print(getSrc)