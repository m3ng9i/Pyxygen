#!/usr/bin/env python3

'''Html Article - 网页正文提取程序

   本程序通过分析网页中的html代码，通过统计字符个数判断正文位置并提取正文。输出内容仍然为html代码。
   
   本程序依赖第三方模块BeautifulSoup，此模块的安装方法请参考如下地址：
   http://www.crummy.com/software/BeautifulSoup/bs4/doc/

   程序运行方法：
   1、将此文件放到任意目录，例如~/bin，确保文件有执行权限，如果没有，请用 chmod u+x htmlarticle.py 添加执行权限
   2、确保文件所在目录位于环境变量PATH中
   3、调用方法举例：htmlarticle.py http://www.example.com/12345.html
   4、运行htmlarticle.py -h查看更多帮助信息'''

import re
import sys
import os.path
import getopt
import html
import base64
import mimetypes
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup


def removeHtmlComments(htm):
    '将html中的注释去除'
    return re.sub("<!--.*?-->", "", htm, flags = re.DOTALL)


def removeEmptyHtmlTags(soap):
    ''' 去除没有内容html标签
        例如<div id="a"></div>就是一个没有内容的标签

        参数soap是一个BeautifulSoup对象，返回值同样为一个BeautifulSoup对象
    '''
    remove = []
    for i in soap.descendants:
        if len(i) == 0 and i.name not in ['br', 'img']:
            remove.append(i)
    for i in remove:
        i.decompose()
    return soap


def pre2p(s):
    '将pre标签内容转换为p标签，pre里面的html实体标签进行一下转换，其他内容保持不变'
    def repl(match):
        ''' 将pre标签内部字符串，先去掉头尾多余的换行符和空格，然后将html中的尖括号等符号转码
            然后将换行符修改为<br />，然后再在头尾包裹上p标签
        '''
        return "<p>" + "<br />".join(html.escape(match.group(1).strip()).splitlines()) + "</p>"
    return re.sub(r"<pre[^>]*>(.*?)</pre>", repl, s, flags = re.IGNORECASE | re.DOTALL)


def removeHtmlAttributes(soap, attrs = []):
    ''' 去掉无用的属性，例如 style、class、id等
        参数soap是BeautifulSoup()的返回值
        参数attrs是包含属性名称的列表
    '''
    if len(attrs) == 0:
        return soap

    for item in soap.find_all():
        for a in attrs:
            del(item[a])

    return soap


def guessImageType(imgurl):
    '根据图片的完整url猜测其mimetype类型，如果未获取到，则认为其为jpg格式'

    path = urllib.parse.urlparse(imgurl).path
    mime = mimetypes.guess_type(os.path.basename(path))
    if mime[0] is None:
        return "image/jpeg"
    else:
        return mime[0]


def usage():

    s = '''Html Article - 网页正文提取程序
分析网页中的html代码，通过统计字符个数判断正文位置并提取正文。输出内容仍然为html代码。

调用方式：
    htmlarticle.py [选项]... <url>
    htmlarticle.py -h
    cat example.htm | htmlarticle.py [选项]...

参数说明：
    -u, --useragent <ua>    设置 user agent（不可与-m参数同时使用）
    -m, --mobile            模拟移动设备访问网页（不可与-u参数同时使用）
    -c, --cookie <cookie>   设置 cookie
        --rows <n>          设置统计字数的行数，默认为10，表示统计当前行及上下10行，共计21行的字数
        --chars <n>         设置统计字数阈值，默认为60，表示当字数大于等于60时，判断为正文
    -i, --inline            将网页中的图片使用base64编码转换为inline image嵌入到html中
    -t, --title             在正文顶部添加文章标题
    -s, --source            在正文顶部添加原文地址（对于从stdin读取的html无效）
    -n                      不使用统计字数的方式确定正文位置
    -p, --prettify          将输出的html代码进行格式化以方便阅读代码
    -o, --output <filename> 输出到文件，而不是stdout，不可与-a参数同时使用
    -a, --autonaming        输出文件到当前目录，文件名根据网页title进行设置，不可与-o参数同时使用
    -h, --help              显示帮助

可以直接抓取网页，或通过stdin读取html：
    htmlarticle.py http://www.example.com/12345.html
    cat example.html | htmlarticle.py'''

    print(s)


def createFilename(title):
    '根据title生成文件名'

    # 去除特殊符号
    signs = r'''!@#$%^&*+=|<>?"':;[]{}'''+'\r\n'
    title = title.translate(''.maketrans(signs, ' '*len(signs)))

    # 空格、正反斜杠、制表符修改为下划线
    title = title.translate(''.maketrans(' /\\\t', '_'*4))

    # 2个以上的下划线合并为1个
    title = re.sub('_{2,}', '_', title)

    # 去除开头结尾的下划线、点
    title = title.strip('_.')

    if title == "":
        title = "未命名"

    basename = "{}.html".format(title)

    # 检测当前目录下是否存在同名文件，如果有，则进行修改
    n = 0
    while True:
        if os.path.exists(basename):
            n += 1
            basename = "{}{}.html".format(title, n)
        else:
            break

    return basename


class Article:

    def __init__(self, *, html = "", url = "", rows = 0, chars = 0, useragent = "", cookie = "", 
            iimage = True, noCharsStat = False, withTitle = True, withSource = True, prettify = False):
        ''' 因为参数较多，未避免输入出错，因此全部参数均为keyword argument

            参数说明：

                html        文章的html代码，如果为空，可以通过fetchPage函数抓取并设置html代码
                url         文章所在的url，如果从stdin读取html，可以将此参数设置为空字符串
                rows        默认10，表示计算正文位置时，统计上下10行（共20行，再加上当前行，共21行）的数据
                chars       默认60，表示统计上述21行数据时，当大于等于60个字符时，即表示当前行进入正文
                useragent   进行http请求时使用的useragent
                cookie      进行http请求时使用的cookie（字符串）
                iimage      是否将图片转换为inline image
                noCharsStat 如果为True表示不使用字符数统计方式确定正文 
                withTitle   是否在输出的正文中添加标题
                withSource  是否在输出的正文中添加原文地址
                prettify    是否将输出的html代码进行格式化以方便阅读代码

            调用方式举例：

                例1，创建Article实例时给出url：
                article = Article(url = "http://www.example.com/12345.html")
                article.fetchPage()
                article.preprocess()
                print(article.article())

                例2，创建Article实例时不给出url：
                article = Article()
                article.fetchPage("http://www.example.com/12345.html")
                article.preprocess()
                print(article.article())


                例3，创建Article实例时给出html，此时不用进行fetchPage，适用于通过stdin读取html的情况
                html = "<html><body>...</body></html>"
                article = Article(html = html)
                article.preprocess()
                print(article.article())

            注意，fetchPage一定要在preprocess之前，article一定要在preprocess之后。
        '''

        if rows <= 0:
            rows = 10
        if chars <= 0:
            chars = 60 

        self.__html         = html
        self.__url          = url
        self.__rows         = rows
        self.__chars        = chars
        self.__useragent    = useragent
        self.__cookie       = cookie
        self.__iimage       = iimage
        self.__noCharsStat  = noCharsStat
        self.__withTitle    = withTitle
        self.__withSource   = withSource
        self.__prettify     = prettify
        self.__soap         = None  # BeautifulSoup对象
        self.__base         = ""    # 保存html base字段
        self.__title        = ""    # 保存网页标题
        self.__body         = ""    # 保存网页body标签中的内容，不含body标签本身


    def __fetch(self, url, image = False, referer = ""):
        ''' 抓取网页的html代码或图片的base64编码

            参数说明：

                url         要抓取的网页或图片的url
                image       False表示抓取网页，True表示抓取是图片。抓取图片时，将图片编码为base64字符串返回。
                referer     进行抓取时使用的referer，如果为空字符串，默认将url设置为referer
        '''

        headers = dict()

        if self.__useragent != "":
            headers['User-Agent'] = self.__useragent
        if self.__cookie != "":
            headers['Cookie'] = self.__cookie
        if referer != "":
            headers['Referer'] = referer
        else:
            headers['Referer'] = url

        # 可能会抛出ValueError异常：unknown url type
        req = urllib.request.Request(url, headers = headers)

        # 可能会抛出urllib.error.HTTPError异常
        content = urllib.request.urlopen(req).readall()

        if image: 
            content = base64.b64encode(content)

        try:
            content = content.decode('utf-8')
        except UnicodeDecodeError:
            content = content.decode('gbk')

        return content


    def __image2inline(self, htm):
        ''' 解析html中的img字段，提取出图片地址(url)，替换为base64编码

            参数说明：
                htm     要处理的html代码
        '''

        def repl(match):
            base = self.__url
            if self.__base != "":
                base = self.__base
                
            imgurl = urllib.parse.urljoin(base, match.group(2))
            mime = guessImageType(imgurl)

            try:
                imgb64 = self.__fetch(imgurl, image = True, referer = imgurl)

                b64 = "data:{};base64,{}".format(mime, imgb64)
            # 如果出现异常，例如http请求错误，请求超时等，返回空字符串
            except:
                b64 = ""

            return '''<img{} src="{}"{}>'''.format(match.group(1), b64, match.group(3))

        return re.sub(r"""<img([^>]*?) src=['"]([^>'"]+)['"]([^>]*)>""", repl, htm, flags = re.IGNORECASE | re.DOTALL)


    def fetchPage(self, url = ""):
        ''' 抓取self.__url页面，如果给了url参数，则将self.__url设置为url，然后再抓取页面'''

        if url != "":
            self.__url = url
        if self.__url == "":
            raise ValueError("url为空")
        self.__html = self.__fetch(self.__url)

    
    def preprocess(self):
        ''' 对self.__html进行预处理，生成self.__soap，self.__title，self.__body
            在调用此方法前，需要确保self.__html不为空，如果self.__html为空，可以使用fetchPage抓取网页
        '''
        if self.__html == "":
            raise ValueError("网页内容为空")

        # 生成 self.__soap (BeautifulSoup对象)
        self.__soap = BeautifulSoup(self.__html, "html.parser")

        # 生成 self.__title
        try:
            self.__title = self.__soap.title.string
        except AttributeError:
            self.__title = ""

        # 生成 self.__base
        try:
            for item in self.__soap.head.find_all("base"):
                href = item.get('href')
                if href is not None:
                    self.__base = href
                    break
        except AttributeError:
            pass
        # 如果原网页中没有base字段，仍然生成此字段，href为url，这么做可以保持正文中的相对连接为可用状态
        if self.__base == "" and self.__url != "":
            self.__base = self.__url

        # 生成 self.__body

        # 从html中提取body标签中的所有内容（不含body标签本身），如果没有获取到，将其设置为self.__html的内容
        match = re.search("<body[^>]*>(.*)</body>", self.__html, flags = re.IGNORECASE | re.DOTALL)
        if match is not None:
            body = match.group(1)
        else:
            body = self.__html

        body = BeautifulSoup(body, "html.parser")

        # 删除body中位于最外层的标签及标签中的内容
        for i in body.find_all(['nav', 'footer', 'header'], recursive = False):
            i.decompose()

        # 删除无用的html标签及标签中的内容
        for i in body.find_all(['head', 'script', 'style', 'link', 'meta', 'iframe', 'input', 'textarea']):
            i.decompose()

        # unwarp部分标签
        for i in body.find_all(['noscript']):
            i.unwrap()

        # 去除内容为空的html标签
        body = removeEmptyHtmlTags(body)

        # 去除无用的属性
        body = removeHtmlAttributes(body, ["style", "class", "id", "target"])

        # 去除html注释
        body = removeHtmlComments(str(body))

        # pre标签转换为p标签
        body = pre2p(body)

        self.__body = body


    def getTitle(self):
        return self.__title


    def article(self, *, iimage = None, noCharsStat = None, withTitle = None, withSource = None, prettify = None):
        ''' 生成正文内容，返回html代码
            
            参数说明（所有参数均为keyword argument）：

                iimage          是否将图片转换为inline image
                noCharsStat     如果为True表示不使用字符数统计方式确定正文
                withTitle       输出中插入文章标题
                withSource      输出中插入文章url
        '''

        body = self.__body
        if body == "":
            raise ValueError("网页body部分为空")

        if iimage is None:
            iimage = self.__iimage
        if noCharsStat is None:
            noCharsStat = self.__noCharsStat
        if withTitle is None:
            withTitle = self.__withTitle
        if withSource is None:
            withSource = self.__withSource
        if prettify is None:
            prettify = self.__prettify

        # 进行字数统计
        if noCharsStat is False:
            bodylines = body.splitlines()

            # 遍历body中的每一行，去掉html，去掉前后的空格，计算每一行中的字符个数，保存到linechars
            linechars = []
            for line in bodylines:
                linechars.append(len(BeautifulSoup(line, "html.parser").get_text().strip()))

            # 遍历每一行，统计当前行+上rows行+下rows行中，所有的字符个数，保存到linestat
            # linestat中大于chars的单元的序号，就是属于正文的内容对应在bodylines的序号
            linestat = []
            htmlstring = [] # 保存属于正文部分的html
            n = 0 # 当前所在行数
            for line in linechars:
                r1 = n - self.__rows - 1 # list开始位置
                r2 = n + self.__rows     # list结束位置
                if r1 < 0 :
                    r1 = 0
                    r2 = 1 + 2 * self.__rows
                linestat.append(sum(linechars[r1:r2]))

                if sum(linechars[r1:r2]) >= self.__chars:
                    htmlstring.append(bodylines[n])

                n = n + 1
            htmlstring = ''.join(htmlstring)
        # 不进行字数统计
        else:
            htmlstring = body

        # 完成body部分html代码的获取，下面开始将img处理为inline模式
        if iimage:
            htmlstring = self.__image2inline(htmlstring)

        soap = removeEmptyHtmlTags(BeautifulSoup(htmlstring, "html.parser"))

        if prettify:
            htmlstring = soap.prettify()
        else:
            htmlstring = str(soap)

        title = self.__title
        if title == "":
            title = "无标题"

        # 在正文顶部添加标题和链接

        head = ""
        if withTitle:
            head = "<h1>{}</h1>".format(title)
        if withSource and len(self.__url) > 0:
            #head = head + "<p>原文地址：<a href='{}'>{}</a></p>".format(args[0], args[0])
            head = head + "<p>原文地址：<a href='{}'>{}</a></p>".format(self.__url, self.__url)

        base = ""
        if self.__base != "":            
            base = r"""<base href="{}"/>""".format(self.__base)

        htmlstring = (r"""<!DOCTYPE html><html><head>{}<meta charset="utf-8" />"""
            r"""<title>{}</title></head><body>{}{}</body></html>""").format(base, title, head, htmlstring)

        return htmlstring


# 默认的user agent
defaultUseragent = "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36"
# 移动设备的user agent
mobileUseragent = "Opera/9.80 (Android; Opera Mini/7.6.35766/35.4970; U; zh) Presto/2.8.119 Version/11.10"

if __name__ == '__main__':

    useragent = ""
    cookie = ""
    rows = 0
    chars = 0
    inline = False
    withTitle = False
    withSource = False
    noCharsStat = False
    prettify = False
    output = None
    autonaming = False
    htmlstring = ""
    url = ""

    try:
        opts, args = getopt.getopt(sys.argv[1:], "u:c:o:mitsnpah", 
                [   "useragent=", "cookie=", "mobile", "rows=", "chars=", "inline", "title", 
                    "source", "prettify", "output=", "autonaming", "help"])

        for i, j in opts:
            if i in ["-h", "--help"]:
                usage()
                sys.exit()

            if i in ["-u", "--useragent"]:
                useragent = j
            elif i in ["-c", "--cookie"]:
                cookie = j
            elif i in ["-m", "--mobile"]:
                useragent = mobileUseragent
            elif i == "--rows":
                errstr = "--rows参数值只能为正整数"
                try:
                    rows = int(rows)
                except ValueError:
                    sys.exit(errstr)
                if rows <= 0:
                    sys.exit(errstr)
            elif i == "--chars":
                errstr = "--chars参数值只能为正整数"
                try:
                    chars = int(j)
                except ValueError:
                    sys.exit(errstr)
                if chars <= 0:
                    sys.exit(errstr)
            elif i in ["-i", "--inline"]:
                inline = True
            elif i in ["-t", "--title"]:
                withTitle = True
            elif i in ["-s", "--source"]:
                withSource = True
            elif i == "-n":
                noCharsStat = True
            elif i in ["-p", "--prettify"]:
                prettify = True
            elif i in ["-o", "--output"]:
                output = j
            elif i in ["-a", "--autonaming"]:
                autonaming = True

        if autonaming is True and output is not None:
            sys.exit("-o/--output参数与-a/--autonaming参数不能同时使用")
        
        if output is not None:
            if os.path.isdir(output):
                sys.exit("无法将输出对象设置为目录：{}".format(output))

        if useragent == "":
            useragent = defaultUseragent

        if len(args) > 0:
            url = args[0]
        else:
            try:
                htmlstring = sys.stdin.read()
            except UnicodeDecodeError:
                enc = sys.getdefaultencoding()
                sys.exit("stdin输入的字符编码方式并不是 {}，请转为 {} 编码方式后再运行程序".format(enc, enc))

        article = Article(html = htmlstring, url = url, rows = rows, chars = chars, 
                useragent = useragent, cookie = cookie, iimage = inline, noCharsStat = noCharsStat, 
                withTitle = withTitle, withSource = withSource, prettify = prettify)
        
        # 从参数读取url，抓取网页
        if len(args) > 0:
            errstr = "抓取网页时出错："
            try:
                article.fetchPage()
            except urllib.error.URLError as e:
                sys.exit("{}{}".format(errstr, e.reason))
            except ValueError as e:
                sys.exit("{}{}".format(errstr, e))

        article.preprocess()
        outputHtml = article.article()

        # 如果有-a参数，输出到文件（当前目录），文件名根据网页title生成
        if autonaming:
            output = createFilename(article.getTitle())

        if output is not None:
            try:
                with open(output, mode='wt') as f:
                    f.write(outputHtml)
                print("生成文件：{}".format(output))
            except IOError as e:
                sys.exit("{}: {}".format(e.strerror, e.filename))
        else:
            print(outputHtml)

    except getopt.GetoptError:
        sys.exit("参数输入错误，使用参数-h查看帮助")
    except KeyboardInterrupt:
        sys.exit()
