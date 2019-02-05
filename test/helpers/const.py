from web3 import Web3


def get_w3(web3_uri: str = None) -> Web3:
    web3_uri = web3_uri or DEFAULT_PARITY_NODE_URL
    w3_instance = Web3(Web3.HTTPProvider(web3_uri))
    assert w3_instance.isConnected(), 'No Web3 connection for node at "{}".'.format(web3_uri)
    assert not w3_instance.eth.syncing, 'Node still syncing.'
    return w3_instance


ETHER_NAME = 'ether'
DEFAULT_PASSWORD = 'WNr23J4SmfuFzZLSg06zO8Tvd1wvrYVGXk467Puyy1'

DEFAULT_PARITY_NODE_URL = "http://127.0.0.1:8545"

PLASMA_CONTRACT_PATH = 'test/json/contracts/PlasmaContract.json'
ERC20_CONTRACT_PATH = 'test/json/contracts/ERC20DockToken.json'
DOCK_PLASMA_CONTRACT_PATH = 'test/json/contracts/DockPlasmaToken.json'
CHECKS_CONTRACT_PATH = 'test/json/contracts/DoChecks.json'

w3 = get_w3()

COIN_DENOMINATION = w3.toWei(5000, ETHER_NAME)  # denomination of the coin off-chain
DEFAULT_FROM = {'from': w3.eth.accounts[0]}
DEFAULT_BOND = w3.toWei(0.1, ETHER_NAME)
