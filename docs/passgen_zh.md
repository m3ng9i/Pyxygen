Passgen - 密码生成器
====================

程序文件名：[passgen.py](../src/pyxygen/passgen.py)

Passgen 可以根据使用者要求，输出包含英文字母、数字或符号的随机字符串。字符范围及字符个数都可以自定义。

程序运行方法
------------

1. 将 [passgen.py](../src/pyxygen/passgen.py) 放到任意目录，例如 `~/bin` ，确保文件有执行权限，如果没有，请用 `chmod u+x passgen.py` 添加执行权限
2. 确保文件所在目录位于环境变量 `PATH` 中
3. 运行 `passgen.py -h` 查看帮助信息

### 调用方式

    passgen [-t <d|l|u|s>] [-s <chars>] [-e <chars>] [-n <number>] [length]
    passgen -h

### 参数说明

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

### 默认值

    -t                  dlu
    -s                  空字符串
    -e                  空字符串
    -n                  1
    length              12

### 使用举例

    passgen -t dlus -e 0oO2z5S 15
    passgen -t dlu -s ".-_!@" 10
    passgen -t dlus -s " "
    passgen -t d -n 20 8
    passgen 20

[[返回目录]](../readme.md)
