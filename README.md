# img_crawler
HTTP img crawling, merge, save local

## Specification
- python 3.7.2

## Useage
다음과 같은 사전 지식이 필요합니다.
- url parameter, path 에 대한 이해
- CSS selector (query selector)에 대한 이해

```bash
$ python run.py (name) (img selector) (protocol + domain) (path + query) (start param [, end param] || next url element selector)
```

option name | description
-|-
name | 저장될 디렉토리 및 이미지 파일명
img selector | 이미지 파일의 CSS 선택자<br>ex. `.img-wrapper > img`
protocol + domain | 프로토콜과 .com, .org등으로 끝나는곳까지의 홈페이지 주소<br>ex. `https://example.com`
path + query | 크롤링할 페이지 주소의 패스 + 파라미터 (쿼리)<br>- param 사용시 치환될 부분을 `%s`로 표기<br>&nbsp;&nbsp;ex. `/img/view?page=%s`<br><br>- 다음 주소를 특정 element로부터 가져와야할 시 그대로 입력<br>&nbsp;&nbsp;입력한 패스 + 파라미터부터 시작
start param [, end param]<br>\|\| next url element selector | - start param<br>&nbsp;&nbsp;only number, 크롤링이 시작될 파라미터<br>&nbsp;&nbsp;path + query에 입력한 `%s`로 start param에서 1씩 더해가며 값을 치환하여 순환<br>&nbsp;&nbsp;end param is optional, 없으면 더이상 이미지를 가져올 수 없을때까지 반복<br><br>- next url element selector<br>&nbsp;&nbsp;다음 페이지 주소를 element로부터 받아와야되는 경우<br>&nbsp;&nbsp;href속성에 담고 있는 element의 선택자를 입력<br>&nbsp;&nbsp;ex. `a.next-btn`