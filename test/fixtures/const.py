from web3 import Web3

DEFAULT_PASSWORD = 'WNr23J4SmfuFzZLSg06zO8Tvd1wvrYVGXk467Puyy1'
ETHER_NAME = 'ether'

PARITY_NODE_URL = "http://127.0.0.1:8545"
w3 = Web3(Web3.HTTPProvider(PARITY_NODE_URL))

# denomination of the coin off-chain
COIN_DENOMINATION = w3.toWei(5000, ETHER_NAME)
