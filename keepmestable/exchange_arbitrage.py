from time import strftime
from exchanges import binance, theocean

class ExchangeArbitrage(object):

    def __init__(self, tokenpair):
        self.minProfit = 0.00005 # 0.00005  # Vary this based on tokens being traded and personal preferences
        self.tokenpair = tokenpair
        self.tokens = [tokenpair[i:i+3] for i in range(0, len(tokenpair), 3)]
        self.tokenA = 'DAI'
        self.tokenB = 'TUSD'
#        self.tokenA = self.tokens[0]
 #       self.tokenB = self.tokens[1]
#        self.binance = binance.Exchange()
        self.theocean = theocean.Exchange()

    def start_arbitrage(self):
        print(strftime('Date: %b %d %Y  Time: %H:%M:%S'))
        print('Starting Exchange Arbitrage between Binance and The Ocean on',self.tokenA,self.tokenB)
        try:
            if self.check_balance():
                arb_scenario = self.check_orderBook()
                if arb_scenario['scenario']:
                    self.place_order(arb_scenario['scenario'], arb_scenario['ask'], arb_scenario['bid'], arb_scenario['amount'] )
                else:
                    print('Arbitrage Scenario:', arb_scenario['scenario'], '-- No arbitrage opportunities or insufficient funds')
        except Exception as error:
            print(str(error))

    def check_balance(self):
 #       self.binance_balance = [float(self.binance.get_balance(self.tokenA)), float(self.binance.get_balance(self.tokenB))]
        self.theocean_balance = [self.theocean.get_balance(self.tokenA), self.theocean.get_balance(self.tokenB)]
  #      self.binance.balancetokA = self.binance_balance[0]
   #     self.binance.balancetokB = self.binance_balance[1]
        self.theocean.balancetokA = self.theocean_balance[0]
        self.theocean.balancetokB = self.theocean_balance[1]
      #  print('Binance Balance:' + self.tokenA + '=', self.binance_balance[0], '; ' + self.tokenB + '=', self.binance_balance[1])
        print('Ocean Balance:' + self.tokenA + '=', self.theocean_balance[0], ';  ' + self.tokenB + '=', self.theocean_balance[1])
        return True

    def check_orderBook(self):
        # Binance
        # self.binance_orderbook_innermost = self.binance.get_ticker_orderBook_innermost(self.tokenpair)
        # Binance best bid price & amount
       #  binance_bestbid_price = self.binance_orderbook_innermost[0][0]
       #  binance_bestbid_amount = self.binance_orderbook_innermost[0][1]
        # Binance best ask price & amount
       #  binance_bestask_price = self.binance_orderbook_innermost[1][0]
       #  binance_bestask_amount = self.binance_orderbook_innermost[1][1]

        # The Ocean
        self.ocean_orderbook_innermost = self.theocean.get_ticker_orderBook_innermost(self.tokenpair)
        # Ocean best ask price & amount
        ocean_bestbid_price = self.ocean_orderbook_innermost[0][0]
        ocean_bestbid_amount = self.ocean_orderbook_innermost[0][1]
        # Ocean best ask price & amount
        ocean_bestask_price = self.ocean_orderbook_innermost[1][0]
        ocean_bestask_amount = self.ocean_orderbook_innermost[1][1]

        # If Scenario 1 > 0:
        # If the highest bid price at Binance is greater than lowest ask price
        # at Ocean, then buy from Ocean and sell to Binance

#        scenario1 = binance_bestbid_price - ocean_bestask_price
        scenario1 = ocean_bestbid_price - ocean_bestask_price

        # If Scenario 2 > 0:
        # If the highest bid price at Ocean is greater than lowest ask price
        # at Binance, then buy from Binance and sell to Ocean

        scenario2 = ocean_bestbid_price - ocean_bestask_price

        if scenario1 > 0:
            maxAmount = self.get_max_amount(self.binance_orderbook_innermost[0], self.ocean_orderbook_innermost[1], 1)
            print('Max Amount for Scenario 1: {0:10f}'.format(maxAmount))
            fee = self.binance.feeRatio * maxAmount * binance_bestbid_price + self.theocean.feeRatio * maxAmount * ocean_bestask_price
            if abs(scenario1) * maxAmount - fee > self.minProfit:
                print("Binance's Bid Price: {0:10f} is greater than TheOcean's Ask Price:{1}. Will Execute Scenario 1.".format(binance_bestbid_price, ocean_bestask_price))
                return {'scenario': 1, 'ask': ocean_bestask_price, 'bid': binance_bestbid_price, 'amount': maxAmount}
            else:
                return {'scenario': 0}
        elif scenario2 > 0:
            maxAmount = self.get_max_amount(self.ocean_orderbook_innermost[0], self.binance_orderbook_innermost[1], 2)
            print('Max Amount for Scenario 2: {0}'.format(maxAmount))
            fee = self.binance.feeRatio * maxAmount * binance_bestask_price + self.theocean.feeRatio * maxAmount * ocean_bestbid_price
            if abs(scenario2) * maxAmount - fee > self.minProfit:
                print("TheOcean's Bid Price: {0} is greater than Binance's Ask Price:{1}. Will Execute Scenario 2.".format(ocean_bestbid_price, binance_bestask_price))
                return {'scenario': 2, 'ask': binance_bestask_price, 'bid': ocean_bestbid_price, 'amount': maxAmount}
        else:
            return {'scenario': 0}

        # Edge cases and alternate scenarios are a still work in progress.
        # Following are couple of scenarios that need to be implemented

        # Scenario 3:
        # If both scenario1 and scenario2 return positive,
        # unlikely scenario as it will require bestbid to be greater than
        # bestask on the ocean
        if scenario1 > 0 and scenario2 > 0:
            if abs(scenario1) > abs(scenario2):
                pass

            elif abs(scenario1) < abs(scenario2):
                pass

        # Scenario 4:
        # If both scenario1 and scenario2 return negative,
        # there are no arbitrage opportunities
        elif scenario1 < 0 and scenario2 < 0:
            if abs(scenario1) > abs(scenario2):
                pass
            elif abs(scenario1) < abs(scenario2):
                pass

    def get_max_amount(self, bidOrder, askOrder, scenario):
        amount = 0
        # Buy from the Ocean, Sell to Binance
        if  scenario == 1:
            maxamtA = self.theocean.balancetokA / ((1 + self.theocean.feeRatio) * askOrder[0])
            maxamtB = self.binance.balancetokB / ((1 + self.binance.feeRatio) * bidOrder[0])
            amount = min(maxamtA, maxamtB, askOrder[1], bidOrder[1])
        # Buy from Binance, Sell to the Ocean
        elif scenario == 2:
            maxamtA = self.binance.balancetokA / ((1 + self.binance.feeRatio) * askOrder[0])
            maxamtB = self.theocean.balancetokB / ((1 + self.theocean.feeRatio) * bidOrder[0])
            amount = min(maxamtA, maxamtB, askOrder[1], bidOrder[1])
        return amount

    def place_order(self, scenario, ask, bid, amount):
        print(strftime('Placing orders. Date: %b %d %Y  Time: %H:%M:%S'))
        if scenario == 1:
            print('Buying {0} amount of {1} at TheOcean for the price of {2} and Selling to Binance for the price of {3} \n \n'.format(amount, self.tokenA, self.ocean_orderbook_innermost[1][0], self.binance_orderbook_innermost[0][0]))
            self.theocean.place_order(self.tokenpair, 'buy', amount, ask)
            self.binance.place_order(self.tokenpair, 'sell', amount, bid)
        elif scenario == 2:
            print('Buying {0} amount of {1} at Binance for the price of {2} and Selling to TheOcean for the price of {3} \n \n'.format(amount, self.tokenA, self.binance_orderbook_innermost[1][0], self.ocean_orderbook_innermost[0][0]))
            self.binance.place_order(self.tokenpair, 'buy', amount, ask)
            self.theocean.place_order(self.tokenpair, 'sell', amount, bid)

if __name__ == '__main__':
    engine = ExchangeArbitrage('DAIETH')
    engine.start_arbitrage()
