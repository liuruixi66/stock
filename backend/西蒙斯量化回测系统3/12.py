import pandas as pd
from pyecharts.components import Table
from pyecharts.charts import Page, Line, Bar
from pyecharts import options as opts
from pyecharts.globals import ThemeType

def generate_strategy_report(
    strategy_data_path="策略评价数据/策略评价数据.xlsx",  # Updated path
    account_data_path="全部交易数据/账户数据.xlsx",  # Updated path
    yearly_data_path="年度收益统计/年度收益统计.xlsx",  # Updated path
    output_file="strategy_split_report.html"
):
    """
    生成完整的策略回测报告
    
    参数:
        strategy_data_path: 策略评价数据文件路径
        account_data_path: 账户数据文件路径
        yearly_data_path: 年度收益统计数据文件路径
        output_file: 输出HTML文件路径
        
    返回:
        无，直接生成HTML报告文件
    """
    # 创建页面
    page = create_report_page()
    
    # 添加标题
    page.add(create_title_component())
    
    # 添加策略评价数据表格（表1和表2）
    for table in create_split_tables(strategy_data_path):
        page.add(table)
    
    # 添加收益曲线图（图3）
    page.add(create_profit_chart(account_data_path))
    
    # 添加年收益率分布条形图（图4）
    page.add(create_yearly_return_chart(yearly_data_path))
    
    # 添加年度收益统计表（表4）
    page.add(create_yearly_stats_table(yearly_data_path))
    
    # 渲染页面
    page.render(output_file)
    print(f"HTML报告已生成: {output_file}")

def create_report_page():
    """创建报告页面基础配置"""
    return Page(
        layout=Page.SimplePageLayout,
        page_title="西蒙斯量化3.0回测报告"
    )

def create_title_component():
    """创建标题组件（简化版）"""
    title_table = Table()
    title_table.add(
        headers=["西蒙斯量化3.0回测系统-回测结果报告,作者:西蒙斯量化,微信:xg_quant"],
        rows=[],
    )
    title_table.set_global_opts(
        title_opts=opts.TitleOpts(
            title="西蒙斯量化3.0回测系统",
            subtitle="回测结果报告",
            title_textstyle_opts=opts.TextStyleOpts(
                font_size=20,
                color="#333",
                font_weight="bold"
            ),
            subtitle_textstyle_opts=opts.TextStyleOpts(
                font_size=16,
                color="#666"
            ),
            pos_left="center",
            padding=[10, 0]
        )
    )
    return title_table

def create_split_tables(data_path):
    """切分策略评价数据为多个子表格"""
    df_strategy = pd.read_excel(data_path)
    try:
        del df_strategy['Unnamed: 0']
    except:
        pass
    
    # 格式化数据，保留两位小数
    def format_value(x):
        if isinstance(x, (int, float)):
            return f"{float(x):.2f}"
        return x
    
    df_strategy = df_strategy.applymap(format_value)
    
    cols = df_strategy.columns.tolist()
    data = df_strategy.values.tolist()
    
    # 将列分成2组
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
            title_opts=opts.TitleOpts(
                title=f"表{i+1}：策略评价数据(Part {i+1})",
                subtitle="数据保留两位小数",
                pos_left="center",
                title_textstyle_opts=opts.TextStyleOpts(
                    font_size=16,
                    color="#333",
                    font_weight="bold"
                )
            )
        )
        tables.append(table)
    return tables

def create_profit_chart(data_path):
    """创建账户收益曲线图"""
    df_account = pd.read_excel(data_path)
    df_account['时间'] = pd.to_datetime(df_account['时间'], format='%Y%m%d')
    df_account['收益'] = df_account['收益'].apply(lambda x: round(x, 2))
    
    line = Line(init_opts=opts.InitOpts(
        theme=ThemeType.LIGHT,
        width="100%",
        height="600px",
        chart_id="profit_chart"
    ))
    line.add_xaxis(df_account['时间'].dt.strftime('%Y-%m-%d').tolist())
    line.add_yaxis(
        series_name="累计收益(%)",
        y_axis=df_account['收益'].tolist(),
        is_smooth=True,
        label_opts=opts.LabelOpts(is_show=False),
        linestyle_opts=opts.LineStyleOpts(width=3, color="#5470C6"),
        symbol_size=8,
        itemstyle_opts=opts.ItemStyleOpts(color="#5470C6"),
        markpoint_opts=opts.MarkPointOpts(
            data=[
                opts.MarkPointItem(type_="max", name="最大值"),
                opts.MarkPointItem(type_="min", name="最小值")
            ],
            label_opts=opts.LabelOpts(formatter="{c}%")
        ),
        markline_opts=opts.MarkLineOpts(
            data=[opts.MarkLineItem(type_="average", name="平均值")],
            label_opts=opts.LabelOpts(formatter="{c}%")
        )
    )
    
    line.set_global_opts(
        title_opts=opts.TitleOpts(
            title="策略收益曲线",
            pos_left="center",
            title_textstyle_opts=opts.TextStyleOpts(
                font_size=16,
                color="#333",
                font_weight="bold"
            )
        ),
        tooltip_opts=opts.TooltipOpts(
            trigger="axis",
            formatter="{b}<br/>{a0}: {c0}%",
            axis_pointer_type="cross"
        ),
        legend_opts=opts.LegendOpts(pos_top="8%"),
        xaxis_opts=opts.AxisOpts(
            axislabel_opts=opts.LabelOpts(rotate=45),
            axispointer_opts=opts.AxisPointerOpts(is_show=True)
        ),
        yaxis_opts=opts.AxisOpts(
            axislabel_opts=opts.LabelOpts(formatter="{value}%"),
            splitline_opts=opts.SplitLineOpts(is_show=True)
        ),
        datazoom_opts=[
            opts.DataZoomOpts(
                range_start=0,
                range_end=100,
                pos_bottom="5%"
            ),
            opts.DataZoomOpts(type_="inside")
        ],
        toolbox_opts=opts.ToolboxOpts(
            is_show=True,
            feature={
                "dataZoom": {"yAxisIndex": "none"},
                "restore": {},
                "saveAsImage": {}
            }
        )
    )
    return line

def create_yearly_return_chart(data_path):
    """创建年收益率分布条形图"""
    df_yearly = pd.read_excel(data_path)
    df_yearly['年收益率'] = df_yearly['年收益率'].apply(lambda x: round(x, 2))
    
    bar = Bar(init_opts=opts.InitOpts(
        theme=ThemeType.LIGHT,
        width="100%",
        height="500px",
        chart_id="yearly_chart"
    ))
    bar.add_xaxis(df_yearly['年份'].astype(str).tolist())
    bar.add_yaxis(
        series_name="年收益率(%)",
        y_axis=df_yearly['年收益率'].tolist(),
        label_opts=opts.LabelOpts(
            formatter="{c}%",
            position="top",
            color="#333",
            font_size=12
        ),
        itemstyle_opts=opts.ItemStyleOpts(
            color="#91CC75",
            border_color="#333",
            border_width=0.5
        ),
        markpoint_opts=opts.MarkPointOpts(
            data=[
                opts.MarkPointItem(type_="max", name="最大值"),
                opts.MarkPointItem(type_="min", name="最小值")
            ],
            label_opts=opts.LabelOpts(formatter="{c}%")
        ),
        markline_opts=opts.MarkLineOpts(
            data=[opts.MarkLineItem(type_="average", name="平均值")],
            label_opts=opts.LabelOpts(formatter="{c}%")
        )
    )
    
    bar.set_global_opts(
        title_opts=opts.TitleOpts(
            title="年收益率分布",
            pos_left="center",
            title_textstyle_opts=opts.TextStyleOpts(
                font_size=16,
                color="#333",
                font_weight="bold"
            )
        ),
        tooltip_opts=opts.TooltipOpts(
            trigger="axis",
            formatter="{b}<br/>{a}: {c}%",
            axis_pointer_type="shadow"
        ),
        xaxis_opts=opts.AxisOpts(
            name="年份",
            axislabel_opts=opts.LabelOpts(rotate=0),
            axisline_opts=opts.AxisLineOpts(
                linestyle_opts=opts.LineStyleOpts(width=2)
            )
        ),
        yaxis_opts=opts.AxisOpts(
            name="收益率(%)",
            axislabel_opts=opts.LabelOpts(formatter="{value}%"),
            splitline_opts=opts.SplitLineOpts(is_show=True)
        ),
        toolbox_opts=opts.ToolboxOpts(
            is_show=True,
            feature={
                "saveAsImage": {},
                "dataView": {}
            }
        )
    )
    return bar

def create_yearly_stats_table(data_path):
    """创建年度收益统计表"""
    df_yearly = pd.read_excel(data_path)
    
    # 格式化数据，保留两位小数
    formatted_data = []
    for _, row in df_yearly.iterrows():
        formatted_row = [
            str(int(row['年份'])),
            f"{float(row['年总盈亏']):.2f}",
            f"{float(row['日均盈亏']):.2f}",
            f"{float(row['年最大单日盈亏']):.2f}",
            f"{float(row['年最小单日盈亏']):.2f}",
            str(int(row['交易天数'])),
            f"{float(row['年总盈亏比']):.2f}%",
            f"{float(row['日均盈亏比']):.2f}%",
            f"{float(row['年末累计收益']):.2f}%",
            f"{float(row['年收益率']):.2f}%",
            f"{float(row['年化收益率']):.2f}%"
        ]
        formatted_data.append(formatted_row)
    
    headers = [
        "年份", "年总盈亏", "日均盈亏", "年最大单日盈亏", "年最小单日盈亏",
        "交易天数", "年总盈亏比", "日均盈亏比", "年末累计收益", "年收益率", "年化收益率"
    ]
    
    table = Table()
    table.add(headers, formatted_data)
    table.set_global_opts(
        title_opts=opts.TitleOpts(
            title="表4：年度收益统计",
            subtitle="所有数据保留两位小数",
            pos_left="center",
            title_textstyle_opts=opts.TextStyleOpts(
                font_size=16,
                color="#333",
                font_weight="bold"
            )
        )
    )
    return table

if __name__ == "__main__":
    # 直接运行时会使用默认参数生成报告
    generate_strategy_report()