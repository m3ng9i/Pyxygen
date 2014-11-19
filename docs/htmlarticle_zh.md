Html Article - 网页正文提取工具
=================================

程序文件名：[htmlarticle.py](../src/pyxygen/htmlarticle.py)

本程序通过分析网页中的 html 代码，通过统计字符个数判断正文位置并提取正文。输出内容仍然为html代码。

本程序依赖第三方模块 *BeautifulSoup* ，此模块的安装方法请参考 [BeautifulSoup文档](http://www.crummy.com/software/BeautifulSoup/bs4/doc/)

## 程序运行方法

1. 确保已安装了 [BeautifulSoup](https://pypi.python.org/pypi/beautifulsoup4)
2. 将 [htmlarticle.py](../src/pyxygen/htmlarticle.py) 放到任意目录，例如 `~/bin` ，确保文件有执行权限，如果没有，请用 `chmod u+x htmlarticle.py` 添加执行权限
3. 确保文件所在目录位于环境变量 `PATH` 中
4. 调用方法举例： `htmlarticle.py http://www.example.com/12345.html`
5. 运行 `htmlarticle.py -h` 查看帮助信息

### 调用方式

	htmlarticle.py [选项]... <url>
	htmlarticle.py -h
	cat example.htm | htmlarticle.py [选项]...

### 参数说明

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

### 例子

提取网页中的正文，输出到stdout：

```shell
htmlarticle.py http://example.com/12345.html
```

提取网页中的正文，输出到文件：

```shell
htmlarticle.py http://example.com/12345.html > out.html
```

提取网页中的正文，输出到文件，另一种方法：

```shell
htmlarticle.py -o out.html http://example.com/12345.html
```

提取网页中的正文，输出到文件，文件名根据网页标题生成：

```shell
htmlarticle.py -a http://example.com/12345.html
```

模拟移动设备访问网页，提取正文，抓取网页中的图片，转换为base64编码内嵌到网页中：

```shell
htmlarticle.py -mi http://example.com/12345.html
```

抓取网页中的正文，在输出中增加标题、原文地址：

```shell
htmlarticle.py -ts http://example.com/12345.html
```

提取html文件中的正文，自定义rows和chars变量：

```shell
cat example.html | htmlarticle.py --rows 5 --chars 50
```

[[返回目录]](../readme.md)
