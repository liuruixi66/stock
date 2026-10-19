from django.test import SimpleTestCase

from research.fractional_results import chinese_result


class FractionalResultLanguageTests(SimpleTestCase):
    def test_translates_nested_fields_without_changing_weights_or_values(self):
        result = {
            'models': {
                '600001.SH:de_prado': {
                    'method': 'de_prado', 'training_device': 'cuda:0',
                    'model': {'output.weight': [[0.125]], 'output.bias': [0.5]},
                },
            },
            'backtests': {'de_prado': {'total_return': 0.1, 'trades': [
                {'side': 'BUY', 'instrument': '600001.SH', 'date': '2025-01-01'},
            ]}},
            'forecasts': {'log_return': [
                {'date': '2025-01-01', 'instrument': '600001.SH', 'predicted_return': 0.02},
            ]},
        }
        translated = chinese_result(result)
        model = translated['模型结果']['600001.SH:de_prado']
        self.assertEqual(model['方法'], '分数差分LSTM')
        self.assertEqual(model['训练设备'], 'cuda:0')
        self.assertEqual(model['模型权重'], result['models']['600001.SH:de_prado']['model'])
        backtest = translated['回测结果']['分数差分LSTM']
        self.assertEqual(backtest['累计收益率'], 0.1)
        self.assertEqual(backtest['成交记录'][0]['买卖方向'], '买入')
        self.assertEqual(translated['逐日预测']['普通收益率LSTM'][0]['预测收益率'], 0.02)
        self.assertIn('models', result)
