"""
扫描：注册到字典里面
"""
import importlib
import inspect
import pkgutil

from atguigu.task.action.base import Action
# from atguigu.task.action.custom.logistics_tracking import LogisticsTrackingAction
# from atguigu.task.action.custom.lookup_order_status import LookupOrderStatusAction
from atguigu.task.action.registry import ActionRegistry


# 手动注册方式，保留供参考
# def action_register(actionRegistry: ActionRegistry):
#     actionRegistry.register_action(LogisticsTrackingAction())
#     actionRegistry.register_action(LookupOrderStatusAction())


# 通过包扫描注册
def auto_action_register(actionRegistry: ActionRegistry):
    # 导入包
    package = importlib.import_module('atguigu.task.action.custom')

    # 获取包里面下一层所有模块
    for _, module_name, is_package in pkgutil.iter_modules(package.__path__, prefix=f'{package.__name__}.'):
        # 如果是包
        if is_package:
            continue
        # 如果不是包 就是py文件
        # 获取py文件中的内容 需要获取Action的子类。
        module = importlib.import_module(module_name)
        #找出 module 模块里的所有类，然后逐个取出类对象。
        for _, action_class in inspect.getmembers(module, inspect.isclass):
            if not issubclass(action_class, Action) or action_class is Action:
                continue
            if action_class.__module__ != module.__name__:
                continue
            # 完成注册
            actionRegistry.register_action(action_class())

"""
1. package.__path__：去哪里找？

前面已经导入了：

package = importlib.import_module("atguigu.task.action.custom")

package.__path__ 保存这个包的搜索目录。你的项目里对应：

/Users/windqzy/nlp/customer_service/atguigu/task/action/custom

所以它告诉 iter_modules()：去这个目录里找模块。

2. prefix：给找到的名字加前缀

package.__name__
# "atguigu.task.action.custom"

因此：

prefix=f'{package.__name__}.'
# "atguigu.task.action.custom."

找到 logistics_tracking.py 后，得到的模块名就是：

atguigu.task.action.custom.logistics_tracking

末尾的 . 是包名与模块名之间的分隔符；.py 后缀不包含在模块名里。

3. iter_modules()：每次提供三个值

每找到一项，就提供：

(模块查找器, 模块名称, 是否为包)

对应你当前的两个文件，可以理解为：

(查找器对象, "atguigu.task.action.custom.logistics_tracking", False)
(查找器对象, "atguigu.task.action.custom.lookup_order_status", False)

这里都是普通 .py 模块，所以 is_package 为 False。如果发现的是子包，则为 True。

4. for _, module_name, is_package：把三个值分别取出来

变量	接收到的内容
_	模块查找器，这里不需要使用
module_name	完整模块名
is_package	是否为包
_ 也是合法变量名，只是大家习惯用它表示“这个值我不用”。

这行等价于更展开的写法：

modules = pkgutil.iter_modules(
    package.__path__,
    prefix=f'{package.__name__}.'
)

for item in modules:
    module_name = item.name
    is_package = item.ispkg

    # 后面继续处理

于是后续代码就很好理解：

if is_package:
    continue  # 跳过子包

module = importlib.import_module(module_name)  # 真正导入找到的模块

这行负责“发现模块”；后面的 import_module() 负责“导入模块”，再往后的代码才负责“找出 Action 类并注册”。 它只扫描下一层，不会自动递归扫描所有子目录。



① inspect.getmembers()：获取模块中的成员

模块的成员可以是类、函数、变量等。每个成员以一对数据返回：

("成员名称", 成员对象)

② inspect.isclass：只保留类

inspect.getmembers(module, inspect.isclass)

相当于告诉它：

获取模块成员，但只要那些“是类”的成员。

这里传的是判断函数 inspect.isclass，由 getmembers() 对每个成员调用它。

得到的结果包含这些项目：
[
    ("Action", Action),
    ("ActionResult", ActionResult),
    ("LogisticsTrackingAction", LogisticsTrackingAction),
    # 还可能有其他导入的类
]

"""
