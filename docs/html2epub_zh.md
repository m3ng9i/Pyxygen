HTML to EPUB - 将指定的URL或HTML文件转换为EPUB电子书
====================================================

程序文件名：[html2epub.py](../src/pyxygen/html2epub.py)

本程序可以将网页转换为epub2格式的电子书，生成的epub文件可以在手机软件“多看阅读”上打开，其他的软件没有测试过，有可能无法正常显示。

本程序依赖 [htmlarticle.py](htmlarticle_zh.md) 和 [BeautifulSoup](http://www.crummy.com/software/BeautifulSoup/bs4/doc/)

## 创建EPUB电子书的3种方式

1. 将本机某个目录中的所有文件转换为EPUB，目录中需要有HTML文件（使用-p参数）
2. 提供若干个URL，抓取页面，转换为EPUB（使用-u参数）
3. 将本机若干个文件转换为EPUB，文件中至少要有一个HTML文件（使用-f参数）

## 程序运行方法

1. 确保已安装了 [BeautifulSoup](https://pypi.python.org/pypi/beautifulsoup4)
2. 将文件 [html2epub.py](../src/pyxygen/html2epub.py) 、 [htmlarticle.py](../src/pyxygen/htmlarticle.py) 放到任意目录，例如 `~/bin` ，确保文件有执行权限，如果没有，请用 `chmod u+x <filename>` 添加执行权限
3. 确保文件所在目录位于环境变量 `PATH` 中
4. 运行 `html2epub.py -h` 查看帮助信息

## 调用方式

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
    
## 举例

将/tmp/htmlfiles目录中的文件创建为电子书

```shell
html2epub.py -o /tmp/book.epub -n 电子书名称 -p /tmp/htmlfiles
```

将两个网页作为内容创建为电子书

```shell
html2epub.py -o /tmp/book.epub -n 电子书名称 -u http://example.com/1 http://example.com/1
```

将两个html文件作为内容创建为电子书，电子书名称与第一个html文件中的title字段相同

```shell
html2epub.py -o /tmp/book.epub -f /tmp/1.html /tmp/2.html
```

## 参考资料

- [使用 EPUB 制作数字图书](https://www.ibm.com/developerworks/cn/xml/tutorials/x-epubtut/)
- [EPUB文件格式校验](http://validator.idpf.org/)

[[返回目录]](../readme.md)
