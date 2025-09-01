import pandas as pd
from pyecharts.components import Table
from pyecharts.charts import Page, Line, Bar
from pyecharts import options as opts
from pyecharts.globals import ThemeType
def get_user_trader_report():
    '''
    生成交易报告
    '''
    df_strategy = pd.read_excel("策略评价数据.xlsx")
    try:
        del df_strategy['Unnamed: 0']
    except:
        pass
    cols = df_strategy.columns.tolist()
    data = df_strategy.values.tolist()
    
    # 将列分成4组（根据你的实际列数调整）
    col_groups = [
        cols[:12],   # 前12列
        cols[12:],   # 剩余列
    ]
    
    tables = []
    for i, group in enumerate(col_groups):
        # 获取当前组的列索引
        col_indices = [cols.index(c) for c in group]
        
        # 提取对应的数据
        table_data = [[row[j] for j in col_indices] for row in data]
        
        # 创建子表格
        table = Table()
        table.add(group, table_data)
        table.set_global_opts(
            title_opts=opts.TitleOpts(title=f"表{i+1}：策略评价数据(Part {i+1})")
        )
        tables.append(table)
    #############
    df_account = pd.read_excel("账户数据.xlsx")
    df_account['时间'] = pd.to_datetime(df_account['时间'], format='%Y%m%d')
    
    line = Line(init_opts=opts.InitOpts(theme=ThemeType.LIGHT))
    line.add_xaxis(df_account['时间'].dt.strftime('%Y-%m-%d').tolist())
    line.add_yaxis(
        series_name="累计收益(%)",
        y_axis=df_account['收益'].tolist(),
        is_smooth=True,
        label_opts=opts.LabelOpts(is_show=False),
        linestyle_opts=opts.LineStyleOpts(width=3),
        symbol_size=8,
    )
    
    line.set_global_opts(
        title_opts=opts.TitleOpts(title="图3：策略收益曲线"),
        tooltip_opts=opts.TooltipOpts(trigger="axis"),
        xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=45)),
        yaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(formatter="{value}%")),
        datazoom_opts=[opts.DataZoomOpts(), opts.DataZoomOpts(type_="inside")]
    )
    ##########
    df_yearly = pd.read_excel("年度收益统计.xlsx")
    
    bar = Bar(init_opts=opts.InitOpts(theme=ThemeType.LIGHT))
    bar.add_xaxis(df_yearly['年份'].astype(str).tolist())
    bar.add_yaxis(
        series_name="年收益率(%)",
        y_axis=df_yearly['年收益率'].tolist(),
        label_opts=opts.LabelOpts(formatter="{c}%", position="top"),
        itemstyle_opts=opts.ItemStyleOpts(color="#5793f3")
    )
    
    bar.set_global_opts(
        title_opts=opts.TitleOpts(title="图4：年收益率分布"),
        tooltip_opts=opts.TooltipOpts(trigger="axis", formatter="{b}<br/>{a}: {c}%"),
        xaxis_opts=opts.AxisOpts(name="年份"),
        yaxis_opts=opts.AxisOpts(
            name="收益率(%)",
            axislabel_opts=opts.LabelOpts(formatter="{value}%")
        ),
    )
    #df_yearly = pd.read_excel("年度收益统计.xlsx")
    
    # 格式化数据，保留两位小数
    formatted_data = []
    for _, row in df_yearly.iterrows():
        formatted_row = [
            str(int(row['年份'])),
            f"{row['年总盈亏']:.2f}",
            f"{row['日均盈亏']:.2f}",
            f"{row['年最大单日盈亏']:.2f}",
            f"{row['年最小单日盈亏']:.2f}",
            str(int(row['交易天数'])),
            f"{row['年总盈亏比']:.2f}%",
            f"{row['日均盈亏比']:.2f}%",
            f"{row['年末累计收益']:.2f}%",
            f"{row['年收益率']:.2f}%",
            f"{row['年化收益率']:.2f}%"
        ]
        formatted_data.append(formatted_row)
    
    headers = [
        "年份", "年总盈亏", "日均盈亏", "年最大单日盈亏", "年最小单日盈亏",
        "交易天数", "年总盈亏比", "日均盈亏比", "年末累计收益", "年收益率", "年化收益率"
    ]
    
    table = Table()
    table.add(headers, formatted_data)
    table.set_global_opts(
        title_opts=opts.TitleOpts(title="表4：年度收益统计")
    )

    #创建页面
    page = Page(layout=Page.SimplePageLayout)

    # 添加标题表格
    title_table = Table()
    title_table.add(
        headers=["西蒙斯量化3.0回测系统 - 回测结果报告"],
        rows=[],
    )
    title_table.set_global_opts(title_opts=None)
    page.add(title_table)

    # 添加策略评价数据表格（表1和表2）
    for table in create_split_tables():
        page.add(table)

    # 添加收益曲线图（图3）
    page.add(create_profit_chart())

    # 添加年收益率分布条形图（图4）
    page.add(create_yearly_return_chart())

    # 添加年度收益统计表（表4）
    page.add(create_yearly_stats_table())

    # 渲染页面
    page.render("strategy_split_report.html")
    print("HTML报告已生成: strategy_split_report.html")
