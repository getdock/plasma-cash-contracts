from web3 import Web3

DEFAULT_PASSWORD = 'WNr23J4SmfuFzZLSg06zO8Tvd1wvrYVGXk467Puyy1'
ETHER_NAME = 'ether'

PARITY_NODE_URL = "http://127.0.0.1:8545"
w3 = Web3(Web3.HTTPProvider(PARITY_NODE_URL))

# denomination of the coin off-chain
COIN_DENOMINATION = w3.toWei(5000, ETHER_NAME)

PLASMA_CONTRACT_PATH = 'test/json/contracts/PlasmaContract.json'
ERC20_CONTRACT_PATH = 'test/json/contracts/ERC20DockToken.json'
DOCK_PLASMA_CONTRACT_PATH = 'test/json/contracts/DockPlasmaToken.json'
CHECKS_CONTRACT_PATH = 'test/json/contracts/DoChecks.json'

DEFAULT_FROM = {'from': w3.eth.accounts[0]}
DEFAULT_BOND = w3.toWei(0.1, ETHER_NAME)
