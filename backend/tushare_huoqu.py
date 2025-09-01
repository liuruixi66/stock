import tushare as ts
import time
import pymysql

# 股票列表
stock_list = ['600519', '000001', '300750', '601318', '002594']

# 需要的字段，按要求排序（带p字段，b1_p到b5_p为买一价到买五价，a1_p到a5_p为卖一价到卖五价）
fields = [
    'date', 'time', 'code', 'name', 'open', 'pre_close', 'price', 'high', 'low', 'bid', 'ask', 'volume', 'amount',
    'bid1', 'bid2', 'bid3', 'bid4', 'bid5', 'ask1', 'ask2', 'ask3', 'ask4', 'ask5',
    'b1_p', 'b2_p', 'b3_p', 'b4_p', 'b5_p', 'a1_p', 'a2_p', 'a3_p', 'a4_p', 'a5_p'
]

# MySQL连接配置
mysql_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',  # 确认这里没有中文或特殊字符
    'database': 'stock',
    'charset': 'utf8mb4'
}

# 建表SQL（只需执行一次，或用Navicat等工具提前建好）
create_table_sql = f'''
CREATE TABLE IF NOT EXISTS quotes (
    date VARCHAR(20),
    time VARCHAR(20),
    code VARCHAR(10),
    name VARCHAR(20),
    open FLOAT,
    pre_close FLOAT,
    price FLOAT,
    high FLOAT,
    low FLOAT,
    bid FLOAT,
    ask FLOAT,
    volume FLOAT,
    amount FLOAT,
    bid1 FLOAT,
    bid2 FLOAT,
    bid3 FLOAT,
    bid4 FLOAT,
    bid5 FLOAT,
    ask1 FLOAT,
    ask2 FLOAT,
    ask3 FLOAT,
    ask4 FLOAT,
    ask5 FLOAT,
    b1_p FLOAT,
    b2_p FLOAT,
    b3_p FLOAT,
    b4_p FLOAT,
    b5_p FLOAT,
    a1_p FLOAT,
    a2_p FLOAT,
    a3_p FLOAT,
    a4_p FLOAT,
    a5_p FLOAT,
    PRIMARY KEY (code, date, time)
)
'''

conn = pymysql.connect(**mysql_config)
cursor = conn.cursor()
cursor.execute(create_table_sql)
conn.commit()

while True:
    df = ts.get_realtime_quotes(stock_list)
    drop_cols = [col for col in df.columns if '_v' in col]
    df = df.drop(columns=drop_cols)
    # tushare原始字段映射：b1_p~b5_p = 'bid1', 'bid2', 'bid3', 'bid4', 'bid5'，a1_p~a5_p = 'ask1', 'ask2', 'ask3', 'ask4', 'ask5'
    df['b1_p'] = df['bid1'] if 'bid1' in df.columns else None
    df['b2_p'] = df['bid2'] if 'bid2' in df.columns else None
    df['b3_p'] = df['bid3'] if 'bid3' in df.columns else None
    df['b4_p'] = df['bid4'] if 'bid4' in df.columns else None
    df['b5_p'] = df['bid5'] if 'bid5' in df.columns else None
    df['a1_p'] = df['ask1'] if 'ask1' in df.columns else None
    df['a2_p'] = df['ask2'] if 'ask2' in df.columns else None
    df['a3_p'] = df['ask3'] if 'ask3' in df.columns else None
    df['a4_p'] = df['ask4'] if 'ask4' in df.columns else None
    df['a5_p'] = df['ask5'] if 'ask5' in df.columns else None
    df = df[[col for col in fields if col in df.columns]]
    print(df)
    print('-' * 40)
    # 覆盖表内容
    cursor.execute("DELETE FROM quotes")
    for i in range(len(df)):
        values = [df.iloc[i][col] if col in df.columns else None for col in fields]
        sql = f"REPLACE INTO quotes ({','.join(fields)}) VALUES ({','.join(['%s']*len(fields))})"
        cursor.execute(sql, values)
    conn.commit()
    time.sleep(3)
