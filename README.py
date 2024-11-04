#Базовая настройка
from __future__ import (absolute_import, division,print_function, unicode_literals)
import backtrader as bt
import yfinance as yf

# Создаем класс стратегии
class TestStrategies3(bt.Strategy):

    # Метод для логгирования сообщений (вывода текста с датой)
    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)  # Получаем текущую дату
        print('%s, %s' % (dt.isoformat(), txt))    # Выводим дату и текст

    # Инициализация стратегии
    def __init__(self):
        self.dataclose = self.datas[0].close  # Получаем данные о цене закрытия

        # Переменные для отслеживания состояния ордера
        self.order = None
        self.buyprice = None
        self.buycomm = None

    # Уведомление о статусе ордера
    def notify_order(self, order):
        # Проверяем статус ордера
        if order.status in [order.Submitted, order.Accepted]:  # Если ордер подан или принят, ничего не делаем
            return

        # Если ордер выполнен
        if order.status in [order.Completed]:
            if order.isbuy():  # Если ордер был на покупку
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm: %.2f' % 
                    (order.executed.price,  # Цена исполнения
                     order.executed.value,  # Стоимость сделки
                     order.executed.comm))  # Комиссия
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Если ордер был на продажу
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            # Запоминаем бар, на котором был выполнен ордер
            self.bar_executed = len(self)

        # Если ордер был отменен, маржинальный или отклонен
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Сбрасываем переменную ордера
        self.order = None

    # Уведомление о закрытии сделки
    def notify_trade(self, trade):
        if not trade.isclosed:  # Если сделка не закрыта, ничего не делаем
            return

        # Логгируем прибыль и чистую прибыль
        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    # Метод, который вызывается на каждом баре данных
    def next(self):
        # Логгируем текущую цену закрытия
        self.log('Close, %.2f' % self.dataclose[0])

        # Проверяем, есть ли уже ордер; если есть, не отправляем новый
        if self.order:
            return

        # Проверяем, есть ли у нас открытая позиция
        if not self.position:

            # Если позиции нет, проверяем условия для покупки
            if self.dataclose[0] < self.dataclose[-1]:  # текущая цена закрытия меньше предыдущей

                if self.dataclose[-1] < self.dataclose[-2]:  # предыдущая цена закрытия меньше цены до нее

                    # Создаем ордер на покупку
                    self.log('BUY CREATE, %.2f' % self.dataclose[0])
                    self.order = self.buy()  # Отправляем ордер на покупку

        else:
            # Если позиция уже открыта, проверяем условия для продажи
            if len(self) >= (self.bar_executed + 5):  # Держим позицию 5 баров после покупки
                # Создаем ордер на продажу
                self.log('SELL CREATE, %.2f' % self.dataclose[0])
                self.order = self.sell()  # Отправляем ордер на продажу

# Основная функция для запуска бэктеста
def f8():
    if __name__ == '__main__':
        cerebro = bt.Cerebro()  # Создаем объект для управления бэктестом
        cerebro.addstrategy(TestStrategies3)  # Добавляем стратегию в Cerebro

        # Загружаем данные с Yahoo Finance
        data = bt.feeds.PandasData(dataname=yf.download('ORCL', '2022-04-04','2024-03-03', auto_adjust=True))

        cerebro.adddata(data)  # Добавляем данные в Cerebro

        cerebro.broker.setcash(100000.0)  # Устанавливаем начальный капитал

        cerebro.broker.setcommission(commission=0.001)  # Устанавливаем комиссию

        # Выводим начальное значение портфеля
        print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

        # Запускаем бэктест
        cerebro.run()

        # Выводим конечное значение портфеля
        print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

f8()  # Запуск функции
