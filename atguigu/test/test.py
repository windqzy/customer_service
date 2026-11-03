"""

eval 里面有三个参数
1.表达式 ‘slots.get('product_id')’
2.eval中可以调用python中的哪些内置函数
一般设置为空字典，标识调用所有python内置函数
3.具体数据
"""
if __name__ == '__main__':
    # 创建字典，放数据
    data = {
        'slots': {
            'product_id': 'kkkk'
        }
    }
    result = bool(
        eval("slots.get('product_id')",
             {},
             data)
    )
    print(result)
