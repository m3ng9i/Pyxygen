#!/usr/bin/env python3

'''
Passgen

本程序可以用来产生随机字符串，可以自定义要显示的字符范围，自定义字符个数，自定义输出结果数量。

完成日期：2014-09-11

更多 Pyxygen 程序请访问：https://github.com/m3ng9i/Pyxygen'''

import random, sys, getopt

# 显示帮助信息
def usage():
    s = r"""Passgen 密码生成器

调用方式：    
    passgen.py [-t <d|l|u|s>] [-s <chars>] [-e <chars>] [-n <number>] [length]
    passgen.py -h

参数说明：
    -t <d|l|u|s>            定义密码字符集合类型，d、l、u、s分别表示4个不同的集合
       d: 数字              0123456789
       l: 小写字母          abcdefghijklmnopqrstuvwxzy
       u: 大写字母          ABCDEFGHIJKLMNOPQRSTUVWXZY
       s: 符号（不含空格）  ~!@#$%^&*()_+|`{}[]:";'<>?,./
    -s <chars>              定义密码字符集合
    -e <chars>              定义需要排除的字符
    -n <number>             产生的密码个数（大于0的正整数）
    length                  定义密码长度（大于0的正整数）
    -h, --help              显示帮助

默认值：
    -t                  dlu
    -s                  空字符串
    -e                  空字符串
    -n                  1
    length              12

使用举例：
    passgen -t dlus -e 0oO2z5S 15
    passgen -t dlu -s ".-_!@" 10
    passgen -t dlus -s " "
    passgen -t d -n 20 8
    passgen 20"""

    print(s)

# 生成创建密码时需要的字符
def getChars(digit, lower, upper, symbol, chars, exclude):
    '''
    digit       True/False，是否包含数字
    lower       True/False，是否包含小写字母
    upper       True/False，是否包含大写字母
    symbol      True/False，是否包含符号
    chars       自定义字符
    exclude     要排除的字符
    '''

    s = set()

    if digit:
        s = s | set("0123456789")
    if lower:
        s = s | set("abcdefghijklmnopqrstuvwxzy")
    if upper:
        s = s | set("ABCDEFGHIJKLMNOPQRSTUVWXZY")
    if symbol:
        s = s | set(r'''~ !@#$%^&*()_+|`{}[]:";'<>?,./''')
    if len(chars) > 0:
        s = s | set(chars)
    if len(exclude) > 0:
        s = s - set(exclude)
    
    c = ""
    for i in s:
        c = c + i
    return c


# 根据chars生成lengths个随机字符
def randomChars(chars, length):
    if len(chars) == 0:
        return ""

    r = random.SystemRandom()
    n = 0
    s = ""
    while n < length:
        s = s + r.choice(chars)
        n = n + 1
    return s


def main():

    digit = False
    lower = False
    upper = False
    symbol = False
    chars = ""
    exclude = ""
    number = 1
    length = 12

    try:
        opts, args = getopt.getopt(sys.argv[1:], "t:s:e:n:h", ["help"])
        for i, j in opts:
            if i in ["-h", "--help"]:
                usage()
                sys.exit()
            elif i == "-t":
                if "d" in j:
                    digit = True
                if "l" in j:
                    lower = True
                if "u" in j:
                    upper = True
                if "s" in j:
                    symbol = True
            elif i == "-s":
                chars = j
            elif i == "-e":
                exclude = j 
            elif i == "-n":
                err = "-n参数值“{}”错误，密码个数必须为大于0的整数".format(j)
                try:
                    number = int(j)
                except ValueError:
                    sys.exit(err)
                if number <= 0:
                    sys.exit(err)

        if len(args) > 0:
            err = "密码长度“{}”格式错误，密码长度必须为大于0的整数".format(args[0])
            try:
                length = int(args[0])
            except ValueError:
                sys.exit(err)
            if length <=0:
                sys.exit(err)

    except getopt.GetoptError:
        sys.exit("参数输入错误，使用参数-h查看帮助")


    # default value
    if digit == lower == upper == symbol == False and chars == "":
        digit = lower = upper = True
    
    while number > 0:
        chars = getChars(digit, lower, upper, symbol, chars, exclude)
        print(randomChars(chars, length))
        number = number - 1
    
main()
