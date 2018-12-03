#### 终端颜色输出
>* 安装颜色库
```
# pytho2/3 均支持
pip install termcolor colorama
```
>* 使用示例
```
from termcolor import colored,cprint
import colorama

# 初始化
colorama.init()
# 两种方式
example1 = colored("some text","red",attrs=["bold"])
print(example1)

# example2
cprint("some text","red","on_white",attrs=["bold"])
```
>* 参考

https://pypi.org/project/termcolor/
