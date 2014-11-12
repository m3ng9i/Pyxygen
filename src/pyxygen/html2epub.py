#!/usr/bin/env python3


import zipfile
import os
import os.path
import tempfile
import mimetypes
import hashlib
import time
import shutil
import sys
import getopt
from bs4 import BeautifulSoup
import htmlarticle

''' 本程序依赖第三方模块：
    BeautifulSoup：此模块的安装方法请参考如下地址：http://www.crummy.com/software/BeautifulSoup/bs4/doc/
    htmlarticle：见htmlarticle.py
'''

class CreateEpubError(Exception):
    pass


def mediaType(filename):
    '根据文件名获取文件的mediatype'

    mime = mimetypes.guess_type(os.path.basename(filename))
    if mime[0] is None:
        return "application/octet-stream"
    elif mime[0] == "text/html":
        return "application/xhtml+xml"
    else:
        return mime[0]


def hashfiles(files):
    ''' 计算多个文件的合并了的md5值，files是列表 '''
    h = hashlib.md5()
    for filename in files:
        with open(filename, mode = 'rb') as f:
            while True:
                buf = f.read(8192)
                if not buf:
                    break
                h.update(buf)
    return h.hexdigest()


def getTitle(path):
    ''' 打开html文件，取title标签的值，没有取到时返回空字符串
        可能抛出的异常：IOError
    '''
    html = open(path).read()
    soap = BeautifulSoup(html)
    title = soap.title
    if title is None:
        return ''
    else:
        return title.string


class CreateEpub():
    ''' 根据提供的html、jpg等文件创建epub电子书

        可能抛出的异常：
        IOError	            获取html中的标题是无法打开文件
        ValueError          参数src不是目录；无法将文件写入到目录
        OSError             无法切换到目录
        FileNotFoundError   要添加到epub的文件不存在，或者要添加的是一个目录而不是文件
        shutil.Error        复制文件时出错
        ValueError          要添加到epub的文件名有重复

        构造函数的第一个参数是一个列表，包含文件名，文件名中html文件的顺序决定了在电子书中的排序。
        
        调用举例，下面的代码将会将3个html文件打包为一个epub文件，电子书名称为“测试”：
        CreateEpub(["/tmp/1.htm", "/tmp/3.htm", "/tmp/2.htm"], "/tmp/x.epub", "测试")
    '''

    def __createTmpDir(self):
        ''' 创建epub临时目录

            创建内容包含：
            1. 临时目录
            2. 临时目录/mimetype文件
            3. 临时目录/META-INF目录
            4. 临时目录/META-INF/container.xml文件
            5. 临时目录/OEBPS目录
            6. 临时目录/OEBPS/content目录

            返回值：临时目录对象
        '''
        
        tmp = tempfile.TemporaryDirectory()
        tmpdir = tmp.name
        
        # 生成 mimetype 文件
        with open(os.path.join(tmpdir, "mimetype"), 'wt') as f:
            f.write("application/epub+zip")

        # 生成 META-INF 目录
        d = os.path.join(tmpdir, "META-INF")
        os.makedirs(d, exist_ok = True)

        # 生成 META-INF/container.xml 文件
        container = (r"""<?xml version="1.0"?>"""
            r"""<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">"""
            r"""<rootfiles>"""
            r"""<rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>"""
            r"""</rootfiles>"""
            r"""</container>""")
        with open(os.path.join(d, "container.xml"), 'wt') as f:
            f.write(container)

        # 生成 OEBPS 目录、OEBPS/content 目录，后者用来保存html及相关文件
        d = os.path.join(tmpdir, "OEBPS")
        os.makedirs(os.path.join(d, "content"), exist_ok = True)

        return tmp

    
    def __hasDuplicateFiles(self):
        ''' 检测self.__srcfiles（列表）中是否有重复的项目

            self.__srcfiles是一个元素均为字符串的列表

            返回值：
            True    有重复的项目
            False   没有重复的项目
        '''
        l = self.__srcfiles[:]
        l.sort()
        last = None
        for i in l:
            if i == last:
                return True
            last = i
        return False 


    def __createBookId(self):
        ''' 生成bookid，格式：html2epub_{md5值} '''
        filepaths = []
        for i in self.__srcfiles:
            filepaths.append(os.path.join(self.__tmpdir, "OEBPS", "content", i))
        return "html2epub_{}".format(hashfiles(filepaths))

    
    def __createFileContentOpf(self):
        ''' 生成OEPBS/content.opf文件 '''

        # 生成metadata节点
        metadata = (r"""<metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">"""
            r"""<dc:title>{}</dc:title><dc:creator>pyxygen:html2epub</dc:creator>"""
            r"""<dc:date opf:event="publication">{}</dc:date><dc:identifier id="BookID">{}</dc:identifier>"""
            r"""<dc:language>zh-cn</dc:language></metadata>""").format(self.__name, time.strftime("%Y-%m-%d"), self.__bookid)

        # 生成manifest节点，此节点包含所有应添加到epub中的文件，再加上toc.ncx
        # TODO 将toc.ncx的media-type修改为 text/xml看生成的epub能否使用
        item = []
        item.append(r"""<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>""")
        for i in self.__srcfiles:
            item.append(r"""<item id="{}" href="content/{}" media-type="{}"/>""".format(i, i, mediaType(i)))
        manifest = r"""<manifest>{}</manifest>""".format("".join(item))

        # 生成spine节点，此节点设置了所有html页面的顺序
        # spine的toc属性的值对应manifest中第一个item的id
        # spine节点的子节点itemref包含idref属性，这个属性的值对应manifest的子节点item的id
        item = []
        for i in self.__srcfiles:
            if mediaType(i) == "application/xhtml+xml":
                item.append(r"""<itemref idref="{}"/>""".format(i))
        spine = r"""<spine toc="ncx">{}</spine>""".format("".join(item))

        # 生成这个content.opf文件的内容
        content = (r"""<?xml version="1.0" encoding="UTF-8" ?>"""
            r"""<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="{}" version="2.0">"""
            r"""{}{}{}</package>""").format(self.__bookid, metadata, manifest, spine)

        # 将文件内容写入content.opf
        with open(os.path.join(self.__tmpdir, "OEBPS", "content.opf"), 'wt') as f:
            f.write(content)


    def __createFileTocNcx(self):
        ''' 生成OEBPS/toc.ncx文件 '''

        # 生成head节点
        head = (r"""<head><meta name="dtb:uid" content="{}"/><meta name="dtb:depth" content="1"/>"""
            r"""<meta name="dtb:totalPageCount" content="0"/><meta name="dtb:maxPageNumber" content="0"/>"""
            r"""</head>""").format(self.__bookid)

        # 生成docTitle节点
        docTitle = r"<docTitle><text>{}</text></docTitle>".format(self.__name)
        
        # 生成navMap节点
        navPoint = []
        n = 1
        for i in self.__srcfiles:
            if mediaType(i) == "application/xhtml+xml":
                src = os.path.join("content", i)
                title = getTitle(os.path.abspath(os.path.join(self.__tmpdir, "OEBPS", src)))
                if title.strip() == "":
                    title = "无标题"

                s = (r"""<navPoint id="{}" playOrder="{}"><navLabel><text>{}</text></navLabel>"""
                    r"""<content src="{}"/></navPoint>""").format(i, n, title, src)

                navPoint.append(s)
                n += 1
        navMap = r"<navMap>{}</navMap>".format(''.join(navPoint))
        
        # 生成整个toc.ncx字符串
        tocNcx = (r"""<?xml version="1.0" encoding="utf-8"?>"""
            r"""<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN" "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">"""
            r"""<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1" xml:lang="zh-CN">"""
            r"""{}{}{}</ncx>""").format(head, docTitle, navMap)

        # 写入toc.ncx文件
        with open(os.path.join(self.__tmpdir, "OEBPS", "toc.ncx"), 'wt') as f:
            f.write(tocNcx)
        

    def __createZip(self):
        ''' 创建zip压缩文件

            可能会抛出的异常：
            ValueError  参数src不是目录；无法将文件写入到目录
            OSError     无法切换到目录
        '''

        src = os.path.abspath(self.__tmpdir)

        if os.path.isdir(src) == False:
            raise ValueError("{} 不是目录".format(src))

        dest = os.path.abspath(self.__destfile)

        if os.path.isdir(dest):
            raise ValueError("无法将文件写入到目录：{}".format(dest))

        # 为了向zip压缩文件添加文件时，对添加的文件路径进行进一步处理，需要把上述src、dest转换为绝对路径

        # 可能会抛出OSError
        os.chdir(src)
        
        # 遍历src文件夹，将其中所有文件（点开头的文件或目录除外）添加到压缩文件中
        pos = len(src) + 1
        with zipfile.ZipFile(dest, 'w', zipfile.ZIP_DEFLATED) as z:

            # mimetype文件必须为epub中的第一个文件，且不能压缩
            z.write("mimetype", compress_type = zipfile.ZIP_STORED)

            for curdir, _, files in os.walk(src):
                # 在向zip文件中添加文件时，需要将路径名称转换为相对路径
                curdir = curdir[pos:]
                # 略过点开头的目录
                if curdir.startswith('.'):
                    continue

                for f in files:
                    # TODO del: if f.startswith('.') or f == "mimetype":
                    # 略过点开头的文件
                    if f.startswith('.'):
                        continue
                    # 略过mimetype文件（因为之前已经添加过了）
                    if curdir + f == "mimetype":
                        continue
                        
                    z.write(os.path.join(curdir, f))


    def __init__(self, srcfiles, destfile, name = ""):
        ''' 参数说明：
            srcfiles    要添加到epub中的文件名称（列表），文件顺序决定了在epub中的顺序
                        所有文件的文件名(basename)不能相同
            destfile    生成的电子书路径及文件名        
            name        epub电子书名称，如果为空字符串，则自动生成电子书名

            可能会抛出的异常：
            FileNotFoundError   要添加到epub的文件不存在，或者要添加的是一个目录而不是文件
            shutil.Error        复制文件时出错
            ValueError          要添加到epub的文件名有重复
        '''
        self.__srcfiles = [] # 在临时目录/OEBPS/content目录中的文件的文件名
        self.__destfile = destfile
        self.__name = name

        if len(srcfiles) == 0:
            raise ValueError("参数srcfiles值为空")

        self.__tmp = self.__createTmpDir()    # 创建临时目录
        self.__tmpdir = self.__tmp.name       # 临时目录路径
        
        # 将srcfiles指向的文件复制到:临时目录/OEBPS/content目录
        for f in srcfiles:
            # 可能会抛出FileNotFoundError或shutil.Error异常
            shutil.copy(f, os.path.join(self.__tmpdir, "OEBPS", "content"))
            self.__srcfiles.append(os.path.basename(f))

        # 检测文件名是否有相同的
        if self.__hasDuplicateFiles():
            raise ValueError("srcfiles中存在文件名重复的条目")

        # 自动生成电子书名，同时检测是否缺少html文件
        hasHtml = False
        if self.__name.strip() == "":
            for src in self.__srcfiles:
                path = os.path.join(self.__tmpdir, "OEBPS", "content", src)
                if mediaType(path) == "application/xhtml+xml":
                    hasHtml = True
                    self.__name = getTitle(path)
        if hasHtml is False:
            raise ValueError("srcfiles中并为提供html文件")

        # 生成bookid
        self.__bookid = self.__createBookId()
        # 由于getTitle()可能仍然返回空字符串，所以这里还需要判断一下
        if self.__name.strip() == "":
            self.__name = "epub电子书 {}".format(self.__bookid[:5])
            
        # 生成OEBPS/content.opf文件
        self.__createFileContentOpf()

        # 生成toc.ncx文件
        self.__createFileTocNcx()

        # 打包为epub
        self.__createZip()


def usage():
    s = r'''HTML to EPUB - 将指定的URL或HTML文件转换为EPUB电子书

本程序创建EPUB电子书的3种方式：
1. 将本机某个目录中的所有文件转换为EPUB，目录中需要有HTML文件（使用-p参数）
2. 提供若干个URL，抓取页面，转换为EPUB（使用-u参数）
3. 将本机若干个文件转换为EPUB，文件中至少要有一个HTML文件（使用-f参数）

调用方式：
    html2epub.py -o <filename> [-n <name>] [--ua <useragent>] -p <path> 
    html2epub.py -o <filename> [-n <name>] [--ua <useragent>] -u <url> [url2 ...] 
    html2epub.py -o <filename> [-n <name>] [--ua <useragent>] -f <file> [file2 ...] 
    html2epub.py -h
    
参数说明：
    -o, --output <filename>         设置epub输出路径和文件名
    -n, --name <name>               设置电子书名，如果不提供，则以第一个html文件中的title为电子书名，
        --ua <useragent>            设置抓取网页时的useragent                                    
    -p, --path <path>               设置包含html及相关代码的目录
    -u, --url <url> [url2 ...]      指定一个或多个url
    -f, --file <file> [file2 ...]   指定一个或多个本地文件
    -h, --help                      显示帮助

注意：
    -p、-u、-f参数不能同时使用
    
举例：
    将/tmp/htmlfiles目录中的文件创建为电子书
    html2epub.py -o /tmp/book.epub -n 电子书名称 -p /tmp/htmlfiles

    将两个网页作为内容创建为电子书
    html2epub.py -o /tmp/book.epub -n 电子书名称 -u http://example.com/1 http://example.com/1

    将两个html文件作为内容创建为电子书，电子书名称为与第一个html文件中的title字段相同
    html2epub.py -o /tmp/book.epub -f /tmp/1.html /tmp/2.html'''

    print(s)


def fetchFiles(src, srctype, useragent):
    ''' 获取要添加到epub中的文件

        参数说明：
        src         具体含义根据srctype不同而不同
        srctype     值可以为path、file或url，类型为字符串或列表
                    path：表示src为一个本地目录，将此目录中所有的文件添加到epub
                    file：表示src为一个或多个要添加到epub中的文件路径
                    url：表示src为一个或多个要添加到epub中的url
        useragent   user agent                    

        可能抛出的异常
        TypeError               参数src类型不对
        ValueError              参数srctype值不对；网址格式不对
        urllib.error.URLError   抓取网页时出错
        IOError                 写临时文件时出错

        返回值：(a, b)
        a   列表，包含要添加到epub文件中的所有文件的路径
        b   临时目录对象，如果不返回这个值，函数返回后，临时目录会被自动销毁
    '''
    result = []

    if srctype == "path":
        if isinstance(src, str):
            pass
        elif isinstance(src, list):
            src = src[0]
        else:
            raise TypeError("当srctype为path时，src只能为字符串或列表。")

        for curdir, _, files in os.walk(src):
            for filename in files:
                path = os.path.abspath(os.path.join(curdir, filename))
                result.append(path)

    elif srctype == "file":

        # 可能有的文件不存在
        if isinstance(src, str):
            result.append(src)
        elif isinstance(src, list):
            for s in src:
                result.append(s)
        else:
            raise TypeError("当srctype为file时，src只能为字符串或列表。")

    elif srctype == "url":
        if isinstance(src, str):
            src = [src]
        elif isinstance(src, list):
            pass
        else:
            raise TypeError("当srctype为url时，src只能为字符串或列表。")


        tmp = tempfile.TemporaryDirectory()
        n = 1 # html文件计数

        # 遍历src列表，抓取所有的html页面，图片已内置到网页中
        # 可能发生的异常：urllib.error.URLError、ValueError、IOError
        for s in src:
            article = htmlarticle.Article(url = s, useragent = useragent)
            article.fetchPage()
            article.preprocess()
            html = article.article()

            path = os.path.join(tmp.name, "{}.html".format(n))
            with open(path, 'wt') as f:
                f.write(html)
                result.append(path)
            n += 1                
    else:
        raise ValueError("参数srctype只能为path、file或url")

    # 必须把tmp传出去，否则临时目录在函数返回后就自动销毁了
    return (result, tmp)


if __name__ == '__main__':

    srctype = ""
    src = []
    output = ""
    name = ""
    useragent = htmlarticle.mobileUseragent

    try:
        opts, args = getopt.getopt(sys.argv[1:], "n:po:ufh", ["name=", "ua=", "path", "output=", "url", "file", "help"]) 

        n = 0 # 记录p、u、f参数出现的次数
        for i, j in opts:
            if i in ['-h', '--help']:
                usage()
                sys.exit()

            if i in ['-n', '--name']:
                name = j
            elif i == "--ua":
                useragent = j
            elif i in ['-p', '--path']:
                srctype = "path"
                n += 1
            elif i in ['-o', '--output']:
                output = j
            elif i in ['-u', '--url']:
                srctype = "url"
                n += 1
            elif i in ['-f', '--file']:
                srctype = "file"
                n += 1
            src = args

        if len(src) == 0:
            sys.exit("参数输入错误。使用-h查看帮助。")
        if n != 1:
            sys.exit("参数输入错误：必须给出-p、-u或-f参数，且只能给出一个。使用-h查看帮助。")
        if output == "":
            sys.exit("参数输入错误：缺少-o参数。使用-h查看帮助。")

    except getopt.GetoptError:
        sys.exit("参数输入错误，使用参数-h查看帮助")

    try:
        srcfiles, _ = fetchFiles(src, srctype, useragent)
        CreateEpub(srcfiles, output, name)
    except KeyboardInterrupt:
        sys.exit()
    except Exception as e:
        sys.exit("创建epub文件时出错：{}".format(e))

    print("成功生成epub：{}".format(os.path.abspath(output)))
                    


