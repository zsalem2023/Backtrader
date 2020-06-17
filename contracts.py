from ibapi.contract import Contract

# Use the IB contract database to find the contract ID for the security you are looking for
# https://misc.interactivebrokers.com/cstools/contract_info/v3.10/index.php?site=IB&action=Top+Search&symbol=&description=

# SPY ETF that tracks the one day return of the S&P 500 index
def spy():
    contract = Contract()
    contract.conId = 756733
    contract.exchange = 'ISLAND'
    return contract, 'SPY'

# SPX Index
def spx():
    contract = Contract()
    contract.conId = 332931480
    contract.exchange = 'ISLAND'
    return contract, 'SPX'

# Euro to Dollar
def euro():
    contract = Contract()
    contract.symbol = 'EUR'
    contract.secType = 'CASH'
    contract.exchange = 'IDEALPRO'
    contract.currency = 'USD'
    return contract, 'EUROUSD'