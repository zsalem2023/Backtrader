from ibapi.contract import Contract

# SPY ETF that tracks the one day return of the S&P 500 index
def spy():
    contract = Contract()
    contract.conId = 756733
    contract.exchange = 'ISLAND'
    return contract, 'SPY'

def euro():
    contract = Contract()
    contract.symbol = 'EUR'
    contract.secType = 'CASH'
    contract.exchange = 'IDEALPRO'
    contract.currency = 'USD'
    return contract