# 股票字段比较函数
def compare_low(df, value):
    """比较最低价"""
    return df['LOW'] > value

def compare_high(df, value):
    """比较最高价"""
    return df['HIGH'] > value

def compare_open(df, value):
    """比较开盘价"""
    return df['OPEN'] > value

def compare_close(df, value):
    """比较收盘价"""
    return df['CLOSE'] > value
# 常用比较运算符函数
def greater(a, b):
    return a > b

def less(a, b):
    return a < b

def greater_equal(a, b):
    return a >= b

def less_equal(a, b):
    return a <= b

def equal(a, b):
    return a == b
"""
compare.py
提供基本的比较大小功能
"""

def compare(a, b):
    """
    比较两个值的大小
    返回: 1 如果 a > b, -1 如果 a < b, 0 如果相等
    """
    if a > b:
        return 1
    elif a < b:
        return -1
    else:
        return 0

def compare_list(list1, list2):
    """
    比较两个列表的每个元素大小
    返回: [compare(x, y) for x, y in zip(list1, list2)]
    """
    return [compare(x, y) for x, y in zip(list1, list2)]
