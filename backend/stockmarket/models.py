from django.db import models

class StockAttention(models.Model):
    """我的关注"""
    datetime = models.DateTimeField('日期')
    code = models.CharField('代码', max_length=6)

    class Meta:
        db_table = 'cn_stock_attention'
        verbose_name = '我的关注'
        verbose_name_plural = verbose_name
        unique_together = ('datetime', 'code')

class EtfSpot(models.Model):
    """每日ETF数据"""
    date = models.DateField('日期')
    code = models.CharField('代码', max_length=6)
    name = models.CharField('名称', max_length=20)
    new_price = models.FloatField('最新价')
    change_rate = models.FloatField('涨跌幅')
    ups_downs = models.FloatField('涨跌额')
    volume = models.BigIntegerField('成交量')
    deal_amount = models.BigIntegerField('成交额')
    open_price = models.FloatField('开盘价')
    high_price = models.FloatField('最高价')
    low_price = models.FloatField('最低价')
    pre_close_price = models.FloatField('昨收')
    turnoverrate = models.FloatField('换手率')
    total_market_cap = models.BigIntegerField('总市值')
    free_cap = models.BigIntegerField('流通市值')

    class Meta:
        db_table = 'cn_etf_spot'
        verbose_name = '每日ETF数据'
        verbose_name_plural = verbose_name
        unique_together = ('date', 'code')

class StockSpot(models.Model):
    """每日股票数据"""
    id = models.AutoField(primary_key=True)
    date = models.DateField('日期')
    code = models.CharField('代码', max_length=6)
    name = models.CharField('名称', max_length=20)
    new_price = models.FloatField('最新价')
    change_rate = models.FloatField('涨跌幅')
    ups_downs = models.FloatField('涨跌额')
    volume = models.BigIntegerField('成交量')
    deal_amount = models.BigIntegerField('成交额')
    amplitude = models.FloatField('振幅')
    turnoverrate = models.FloatField('换手率')
    volume_ratio = models.FloatField('量比')
    open_price = models.FloatField('今开')
    high_price = models.FloatField('最高')
    low_price = models.FloatField('最低')
    pre_close_price = models.FloatField('昨收')
    speed_increase = models.FloatField('涨速')
    speed_increase_5 = models.FloatField('5分钟涨跌')
    speed_increase_60 = models.FloatField('60日涨跌幅')
    speed_increase_all = models.FloatField('年初至今涨跌幅')
    dtsyl = models.FloatField('市盈率动')
    pe9 = models.FloatField('市盈率TTM')
    pe = models.FloatField('市盈率静')
    pbnewmrq = models.FloatField('市净率')
    basic_eps = models.FloatField('每股收益')
    bvps = models.FloatField('每股净资产')
    per_capital_reserve = models.FloatField('每股公积金')
    per_unassign_profit = models.FloatField('每股未分配利润')
    roe_weight = models.FloatField('加权净资产收益率')
    sale_gpr = models.FloatField('毛利率')
    debt_asset_ratio = models.FloatField('资产负债率')
    total_operate_income = models.BigIntegerField('营业收入')
    toi_yoy_ratio = models.FloatField('营业收入同比增长')
    parent_netprofit = models.BigIntegerField('归属净利润')
    netprofit_yoy_ratio = models.FloatField('归属净利润同比增长')
    report_date = models.DateField('报告期')
    total_shares = models.BigIntegerField('总股本')
    free_shares = models.BigIntegerField('已流通股份')
    total_market_cap = models.BigIntegerField('总市值')
    free_cap = models.BigIntegerField('流通市值')
    industry = models.CharField('所处行业', max_length=20)
    listing_date = models.DateField('上市时间')

    class Meta:
        db_table = 'cn_stock_spot'
        verbose_name = '每日股票数据'
        verbose_name_plural = verbose_name
        unique_together = ('date', 'code')

class StockSpotBuy(models.Model):
    """基本面选股"""
    # 继承StockSpot的所有字段
    date = models.DateField('日期')
    code = models.CharField('代码', max_length=6)
    name = models.CharField('名称', max_length=20)
    new_price = models.FloatField('最新价')
    change_rate = models.FloatField('涨跌幅')
    ups_downs = models.FloatField('涨跌额')
    volume = models.BigIntegerField('成交量')
    deal_amount = models.BigIntegerField('成交额')
    amplitude = models.FloatField('振幅')
    turnoverrate = models.FloatField('换手率')
    volume_ratio = models.FloatField('量比')
    open_price = models.FloatField('今开')
    high_price = models.FloatField('最高')
    low_price = models.FloatField('最低')
    pre_close_price = models.FloatField('昨收')
    speed_increase = models.FloatField('涨速')
    speed_increase_5 = models.FloatField('5分钟涨跌')
    speed_increase_60 = models.FloatField('60日涨跌幅')
    speed_increase_all = models.FloatField('年初至今涨跌幅')
    dtsyl = models.FloatField('市盈率动')
    pe9 = models.FloatField('市盈率TTM')
    pe = models.FloatField('市盈率静')
    pbnewmrq = models.FloatField('市净率')
    basic_eps = models.FloatField('每股收益')
    bvps = models.FloatField('每股净资产')
    per_capital_reserve = models.FloatField('每股公积金')
    per_unassign_profit = models.FloatField('每股未分配利润')
    roe_weight = models.FloatField('加权净资产收益率')
    sale_gpr = models.FloatField('毛利率')
    debt_asset_ratio = models.FloatField('资产负债率')
    total_operate_income = models.BigIntegerField('营业收入')
    toi_yoy_ratio = models.FloatField('营业收入同比增长')
    parent_netprofit = models.BigIntegerField('归属净利润')
    netprofit_yoy_ratio = models.FloatField('归属净利润同比增长')
    report_date = models.DateField('报告期')
    total_shares = models.BigIntegerField('总股本')
    free_shares = models.BigIntegerField('已流通股份')
    total_market_cap = models.BigIntegerField('总市值')
    free_cap = models.BigIntegerField('流通市值')
    industry = models.CharField('所处行业', max_length=20)
    listing_date = models.DateField('上市时间')

    class Meta:
        db_table = 'cn_stock_spot_buy'
        verbose_name = '基本面选股'
        verbose_name_plural = verbose_name

class StockFundFlow(models.Model):
    """股票资金流向"""
    date = models.DateField('日期')
    code = models.CharField('代码', max_length=6)
    name = models.CharField('名称', max_length=20)
    new_price = models.FloatField('最新价')
    change_rate = models.FloatField('今日涨跌幅')
    fund_amount = models.BigIntegerField('今日主力净流入-净额')
    fund_rate = models.FloatField('今日主力净流入-净占比')
    fund_amount_super = models.BigIntegerField('今日超大单净流入-净额')
    fund_rate_super = models.FloatField('今日超大单净流入-净占比')
    fund_amount_large = models.BigIntegerField('今日大单净流入-净额')
    fund_rate_large = models.FloatField('今日大单净流入-净占比')
    fund_amount_medium = models.BigIntegerField('今日中单净流入-净额')
    fund_rate_medium = models.FloatField('今日中单净流入-净占比')
    fund_amount_small = models.BigIntegerField('今日小单净流入-净额')
    fund_rate_small = models.FloatField('今日小单净流入-净占比')
    change_rate_3 = models.FloatField('3日涨跌幅')
    fund_amount_3 = models.BigIntegerField('3日主力净流入-净额')
    fund_rate_3 = models.FloatField('3日主力净流入-净占比')
    fund_amount_super_3 = models.BigIntegerField('3日超大单净流入-净额')
    fund_rate_super_3 = models.FloatField('3日超大单净流入-净占比')
    fund_amount_large_3 = models.BigIntegerField('3日大单净流入-净额')
    fund_rate_large_3 = models.FloatField('3日大单净流入-净占比')
    fund_amount_medium_3 = models.BigIntegerField('3日中单净流入-净额')
    fund_rate_medium_3 = models.FloatField('3日中单净流入-净占比')
    fund_amount_small_3 = models.BigIntegerField('3日小单净流入-净额')
    fund_rate_small_3 = models.FloatField('3日小单净流入-净占比')
    change_rate_5 = models.FloatField('5日涨跌幅')
    fund_amount_5 = models.BigIntegerField('5日主力净流入-净额')
    fund_rate_5 = models.FloatField('5日主力净流入-净占比')
    fund_amount_super_5 = models.BigIntegerField('5日超大单净流入-净额')
    fund_rate_super_5 = models.FloatField('5日超大单净流入-净占比')
    fund_amount_large_5 = models.BigIntegerField('5日大单净流入-净额')
    fund_rate_large_5 = models.FloatField('5日大单净流入-净占比')
    fund_amount_medium_5 = models.BigIntegerField('5日中单净流入-净额')
    fund_rate_medium_5 = models.FloatField('5日中单净流入-净占比')
    fund_amount_small_5 = models.BigIntegerField('5日小单净流入-净额')
    fund_rate_small_5 = models.FloatField('5日小单净流入-净占比')
    change_rate_10 = models.FloatField('10日涨跌幅')
    fund_amount_10 = models.BigIntegerField('10日主力净流入-净额')
    fund_rate_10 = models.FloatField('10日主力净流入-净占比')
    fund_amount_super_10 = models.BigIntegerField('10日超大单净流入-净额')
    fund_rate_super_10 = models.FloatField('10日超大单净流入-净占比')
    fund_amount_large_10 = models.BigIntegerField('10日大单净流入-净额')
    fund_rate_large_10 = models.FloatField('10日大单净流入-净占比')
    fund_amount_medium_10 = models.BigIntegerField('10日中单净流入-净额')
    fund_rate_medium_10 = models.FloatField('10日中单净流入-净占比')
    fund_amount_small_10 = models.BigIntegerField('10日小单净流入-净额')
    fund_rate_small_10 = models.FloatField('10日小单净流入-净占比')

    class Meta:
        db_table = 'cn_stock_fund_flow'
        verbose_name = '股票资金流向'
        verbose_name_plural = verbose_name
        unique_together = ('date', 'code')

class StockFundFlowIndustry(models.Model):
    """行业资金流向"""
    date = models.DateField('日期')
    name = models.CharField('名称', max_length=30)
    change_rate = models.FloatField('今日涨跌幅')
    fund_amount = models.BigIntegerField('今日主力净流入-净额')
    fund_rate = models.FloatField('今日主力净流入-净占比')
    fund_amount_super = models.BigIntegerField('今日超大单净流入-净额')
    fund_rate_super = models.FloatField('今日超大单净流入-净占比')
    fund_amount_large = models.BigIntegerField('今日大单净流入-净额')
    fund_rate_large = models.FloatField('今日大单净流入-净占比')
    fund_amount_medium = models.BigIntegerField('今日中单净流入-净额')
    fund_rate_medium = models.FloatField('今日中单净流入-净占比')
    fund_amount_small = models.BigIntegerField('今日小单净流入-净额')
    fund_rate_small = models.FloatField('今日小单净流入-净占比')
    stock_name = models.CharField('今日主力净流入最大股', max_length=20)
    change_rate_5 = models.FloatField('5日涨跌幅')
    fund_amount_5 = models.BigIntegerField('5日主力净流入-净额')
    fund_rate_5 = models.FloatField('5日主力净流入-净占比')
    fund_amount_super_5 = models.BigIntegerField('5日超大单净流入-净额')
    fund_rate_super_5 = models.FloatField('5日超大单净流入-净占比')
    fund_amount_large_5 = models.BigIntegerField('5日大单净流入-净额')
    fund_rate_large_5 = models.FloatField('5日大单净流入-净占比')
    fund_amount_medium_5 = models.BigIntegerField('5日中单净流入-净额')
    fund_rate_medium_5 = models.FloatField('5日中单净流入-净占比')
    fund_amount_small_5 = models.BigIntegerField('5日小单净流入-净额')
    fund_rate_small_5 = models.FloatField('5日小单净流入-净占比')
    stock_name_5 = models.CharField('5日主力净流入最大股', max_length=20)
    change_rate_10 = models.FloatField('10日涨跌幅')
    fund_amount_10 = models.BigIntegerField('10日主力净流入-净额')
    fund_rate_10 = models.FloatField('10日主力净流入-净占比')
    fund_amount_super_10 = models.BigIntegerField('10日超大单净流入-净额')
    fund_rate_super_10 = models.FloatField('10日超大单净流入-净占比')
    fund_amount_large_10 = models.BigIntegerField('10日大单净流入-净额')
    fund_rate_large_10 = models.FloatField('10日大单净流入-净占比')
    fund_amount_medium_10 = models.BigIntegerField('10日中单净流入-净额')
    fund_rate_medium_10 = models.FloatField('10日中单净流入-净占比')
    fund_amount_small_10 = models.BigIntegerField('10日小单净流入-净额')
    fund_rate_small_10 = models.FloatField('10日小单净流入-净占比')
    stock_name_10 = models.CharField('10日主力净流入最大股', max_length=20)

    class Meta:
        db_table = 'cn_stock_fund_flow_industry'
        verbose_name = '行业资金流向'
        verbose_name_plural = verbose_name
        unique_together = ('date', 'name')

class StockFundFlowConcept(models.Model):
    """概念资金流向"""
    # 与行业资金流向表结构相同
    date = models.DateField('日期')
    name = models.CharField('名称', max_length=30)
    change_rate = models.FloatField('今日涨跌幅')
    fund_amount = models.BigIntegerField('今日主力净流入-净额')
    fund_rate = models.FloatField('今日主力净流入-净占比')
    fund_amount_super = models.BigIntegerField('今日超大单净流入-净额')
    fund_rate_super = models.FloatField('今日超大单净流入-净占比')
    fund_amount_large = models.BigIntegerField('今日大单净流入-净额')
    fund_rate_large = models.FloatField('今日大单净流入-净占比')
    fund_amount_medium = models.BigIntegerField('今日中单净流入-净额')
    fund_rate_medium = models.FloatField('今日中单净流入-净占比')
    fund_amount_small = models.BigIntegerField('今日小单净流入-净额')
    fund_rate_small = models.FloatField('今日小单净流入-净占比')
    stock_name = models.CharField('今日主力净流入最大股', max_length=20)
    change_rate_5 = models.FloatField('5日涨跌幅')
    fund_amount_5 = models.BigIntegerField('5日主力净流入-净额')
    fund_rate_5 = models.FloatField('5日主力净流入-净占比')
    fund_amount_super_5 = models.BigIntegerField('5日超大单净流入-净额')
    fund_rate_super_5 = models.FloatField('5日超大单净流入-净占比')
    fund_amount_large_5 = models.BigIntegerField('5日大单净流入-净额')
    fund_rate_large_5 = models.FloatField('5日大单净流入-净占比')
    fund_amount_medium_5 = models.BigIntegerField('5日中单净流入-净额')
    fund_rate_medium_5 = models.FloatField('5日中单净流入-净占比')
    fund_amount_small_5 = models.BigIntegerField('5日小单净流入-净额')
    fund_rate_small_5 = models.FloatField('5日小单净流入-净占比')
    stock_name_5 = models.CharField('5日主力净流入最大股', max_length=20)
    change_rate_10 = models.FloatField('10日涨跌幅')
    fund_amount_10 = models.BigIntegerField('10日主力净流入-净额')
    fund_rate_10 = models.FloatField('10日主力净流入-净占比')
    fund_amount_super_10 = models.BigIntegerField('10日超大单净流入-净额')
    fund_rate_super_10 = models.FloatField('10日超大单净流入-净占比')
    fund_amount_large_10 = models.BigIntegerField('10日大单净流入-净额')
    fund_rate_large_10 = models.FloatField('10日大单净流入-净占比')
    fund_amount_medium_10 = models.BigIntegerField('10日中单净流入-净额')
    fund_rate_medium_10 = models.FloatField('10日中单净流入-净占比')
    fund_amount_small_10 = models.BigIntegerField('10日小单净流入-净额')
    fund_rate_small_10 = models.FloatField('10日小单净流入-净占比')
    stock_name_10 = models.CharField('10日主力净流入最大股', max_length=20)

    class Meta:
        db_table = 'cn_stock_fund_flow_concept'
        verbose_name = '概念资金流向'
        verbose_name_plural = verbose_name
        unique_together = ('date', 'name')

class StockBonus(models.Model):
    """股票分红配送"""
    date = models.DateField('日期')
    code = models.CharField('代码', max_length=6)
    name = models.CharField('名称', max_length=20)
    convertible_total_rate = models.FloatField('送转股份-送转总比例')
    convertible_rate = models.FloatField('送转股份-送转比例')
    convertible_transfer_rate = models.FloatField('送转股份-转股比例')
    bonusaward_rate = models.FloatField('现金分红-现金分红比例')
    bonusaward_yield = models.FloatField('现金分红-股息率')
    basic_eps = models.FloatField('每股收益')
    bvps = models.FloatField('每股净资产')
    per_capital_reserve = models.FloatField('每股公积金')
    per_unassign_profit = models.FloatField('每股未分配利润')
    netprofit_yoy_ratio = models.FloatField('净利润同比增长')
    total_shares = models.BigIntegerField('总股本')
    plan_date = models.DateField('预案公告日')
    record_date = models.DateField('股权登记日')
    ex_dividend_date = models.DateField('除权除息日')
    progress = models.CharField('方案进度', max_length=50)
    report_date = models.DateField('最新公告日期')

    class Meta:
        db_table = 'cn_stock_bonus'
        verbose_name = '股票分红配送'
        verbose_name_plural = verbose_name
        unique_together = ('date', 'code')

class StockTop(models.Model):
    """股票龙虎榜"""
    date = models.DateField('日期')
    code = models.CharField('代码', max_length=6)
    name = models.CharField('名称', max_length=20)
    ranking_times = models.FloatField('上榜次数')
    sum_buy = models.FloatField('累积购买额')
    sum_sell = models.FloatField('累积卖出额')
    net_amount = models.FloatField('净额')
    buy_seat = models.FloatField('买入席位数')
    sell_seat = models.FloatField('卖出席位数')

    class Meta:
        db_table = 'cn_stock_top'
        verbose_name = '股票龙虎榜'
        verbose_name_plural = verbose_name
        unique_together = ('date', 'code')

class StockBlocktrade(models.Model):
    """股票大宗交易"""
    date = models.DateField('日期')
    code = models.CharField('代码', max_length=6)
    name = models.CharField('名称', max_length=20)
    new_price = models.FloatField('收盘价')
    change_rate = models.FloatField('涨跌幅')
    average_price = models.FloatField('成交均价')
    overflow_rate = models.FloatField('折溢率')
    trade_number = models.FloatField('成交笔数')
    sum_volume = models.FloatField('成交总量')
    sum_turnover = models.FloatField('成交总额')
    turnover_market_rate = models.FloatField('成交占比流通市值')

    class Meta:
        db_table = 'cn_stock_blocktrade'
        verbose_name = '股票大宗交易'
        verbose_name_plural = verbose_name
        unique_together = ('date', 'code')

class StockChipRaceOpen(models.Model):
    """早盘抢筹数据"""
    date = models.DateField('日期')
    code = models.CharField('代码', max_length=6)
    name = models.CharField('名称', max_length=20)
    new_price = models.FloatField('最新价')
    change_rate = models.FloatField('涨跌幅')
    pre_close_price = models.FloatField('昨收')
    open_price = models.FloatField('今开')
    deal_amount = models.BigIntegerField('开盘金额')
    bid_rate = models.FloatField('抢筹幅度')
    bid_trust_amount = models.BigIntegerField('抢筹委托金额')
    bid_deal_amount = models.BigIntegerField('抢筹成交金额')
    bid_ratio = models.FloatField('抢筹占比')

    class Meta:
        db_table = 'cn_stock_chip_race_open'
        verbose_name = '早盘抢筹数据'
        verbose_name_plural = verbose_name
        unique_together = ('date', 'code')

class StockChipRaceEnd(models.Model):
    """尾盘抢筹数据"""
    date = models.DateField('日期')
    code = models.CharField('代码', max_length=6)
    name = models.CharField('名称', max_length=20)
    new_price = models.FloatField('最新价')
    change_rate = models.FloatField('涨跌幅')
    pre_close_price = models.FloatField('昨收')
    open_price = models.FloatField('今开')
    deal_amount = models.BigIntegerField('收盘金额')
    bid_rate = models.FloatField('抢筹幅度')
    bid_trust_amount = models.BigIntegerField('抢筹委托金额')
    bid_deal_amount = models.BigIntegerField('抢筹成交金额')
    bid_ratio = models.FloatField('抢筹占比')

    class Meta:
        db_table = 'cn_stock_chip_race_end'
        verbose_name = '尾盘抢筹数据'
        verbose_name_plural = verbose_name
        unique_together = ('date', 'code')

class StockLimitupReason(models.Model):
    """涨停原因揭密"""
    date = models.DateField('日期')
    code = models.CharField('代码', max_length=6)
    name = models.CharField('名称', max_length=20)
    title = models.CharField('原因', max_length=255)
    reason = models.CharField('详因', max_length=2000)
    new_price = models.FloatField('最新价')
    change_rate = models.FloatField('涨跌幅')
    ups_downs = models.FloatField('涨跌额')
    turnoverrate = models.FloatField('换手率')
    volume = models.BigIntegerField('成交量')
    deal_amount = models.BigIntegerField('成交额')
    dde = models.BigIntegerField('DDE')

    class Meta:
        db_table = 'cn_stock_limitup_reason'
        verbose_name = '涨停原因揭密'
        verbose_name_plural = verbose_name
        unique_together = ('date', 'code')

class Stock(models.Model):
    code = models.CharField(max_length=10, verbose_name="股票代码")
    name = models.CharField(max_length=50, verbose_name="股票名称")

    class Meta:
        db_table = 'stock'
        verbose_name = '股票'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.code} - {self.name}"

class StockDailyData(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, verbose_name="股票")
    date = models.DateField(verbose_name="日期")
    open = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="开盘价")
    high = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="最高价")
    low = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="最低价")
    close = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="收盘价")
    pre_close = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="前收盘价")
    change = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="涨跌额")
    change_rate = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="涨跌幅(%)")
    volume = models.BigIntegerField(verbose_name="成交量")
    amount = models.DecimalField(max_digits=20, decimal_places=2, verbose_name="成交额")
    turnover_rate = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="换手率(%)")
    amplitude = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="振幅(%)")

    class Meta:
        db_table = 'stock_daily_data'
        unique_together = ('stock', 'date')
        ordering = ['-date']
        verbose_name = '股票日线数据'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.stock.code} - {self.date}"


class StockHistoryData(models.Model):
    """股票历史数据"""
    datetime = models.DateTimeField('时间')
    date = models.DateField('日期')
    symbol = models.CharField('股票代码', max_length=10)
    open = models.FloatField('开盘价')
    close = models.FloatField('收盘价')
    high = models.FloatField('最高价')
    low = models.FloatField('最低价')
    volume = models.BigIntegerField('成交量')
    turnover = models.BigIntegerField('成交额')
    amplitude = models.FloatField('振幅')
    pct_change = models.FloatField('涨跌幅')
    change = models.FloatField('涨跌额')
    turnover_rate = models.FloatField('换手率')

    class Meta:
        db_table = 'stock_history_data'
        verbose_name = '股票历史数据'
        verbose_name_plural = verbose_name
        unique_together = ('date', 'symbol')
        ordering = ['-date']

    def __str__(self):
        return f"{self.symbol} - {self.date}"
