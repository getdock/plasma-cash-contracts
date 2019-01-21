from helpers.web3Provider import w3

DEFAULT_PASSWORD = 'passw0rd'
ETHER_NAME = 'ether'

# denomination of the coin off-chain
COIN_DENOMINATION = w3.toWei(5000, ETHER_NAME)
