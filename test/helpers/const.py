from collections import OrderedDict

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

ETHER_ALLOC = 5_000_000
TOKEN_ALLOC = 10

W3 = get_w3()

COIN_DENOMINATION = W3.toWei(5_000, ETHER_NAME)  # denomination of the coin off-chain
DEFAULT_FROM = {'from': W3.eth.accounts[0]}

BOND_AMOUNT = 0.1
MATURITY_PERIOD = 2
CHALLENGE_WINDOW = 1
DEFAULT_BOND = W3.toWei(BOND_AMOUNT, ETHER_NAME)
CHALLENGE_PARAMS = OrderedDict([('bond-to-wei',  DEFAULT_BOND),
                                ('maturity-period', MATURITY_PERIOD),
                                ('challenge-window', CHALLENGE_WINDOW),
                                ('bond-amount', BOND_AMOUNT),
                                ])

BGS_LIMIT = 8_000_000
