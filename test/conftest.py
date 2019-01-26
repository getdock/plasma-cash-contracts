from typing import Tuple, List

import pytest

from fixtures.const import ETHER_NAME, COIN_DENOMINATION, w3
from helpers import parity, deployer, erc20, participate, instances


@pytest.fixture(scope='module')
def accounts() -> List:
    accounts = setup_accounts()
    yield accounts

    for i in accounts:
        parity.delete_account(i.address)


@pytest.fixture(scope='module')
def setup_participate() -> Tuple[List, List]:
    """Setup accounts on a parity dev node and participate some coins with the first account."""
    accounts = setup_accounts()
    coins = participate_account(accounts[1].address)
    yield accounts, coins

    for i in accounts:
        parity.delete_account(i.address)


def setup_accounts(count: int = 8) -> List:
    """Create some accounts in the parity node."""
    accounts = parity.generate_accounts(count)
    # parity.sendTransaction() is the function which sends sends some amount of ether to an account.
    for i in accounts:
        parity.send_transaction(i.address, w3.eth.accounts[0])
    # defaultAccount is the default account | if there is no ({'from'}) provided the account[0] will be taken as default caller
    w3.eth.defaultAccount = w3.eth.accounts[0]
    # deployer deploying the contracts in localhost web3 provider and also setting the global instances of contracts
    deployer.deployContracts()
    return accounts


def participate_account(account_address) -> List:
    """Make the given account participate."""
    # getting the plasma_instance set by deployer.
    plasma_instance = instances.plasma_instance
    # getting deployed plasma address
    plasma_address = plasma_instance.address
    # transfering erc20 tokens to account_address so she can participate into plasma contract.
    erc20.transfer(account_address, w3.toWei(5000000, ETHER_NAME))
    # account_address approving the tokens to plasma_address so when participate function is called the
    # tokens will be transfered from her address to plasma_address
    erc20.approve(plasma_address, account_address, w3.toWei(5000000, ETHER_NAME))
    # participating to plasma 10 times with denomination 5000 for each token
    coins = participate.participate(account_address, 10, COIN_DENOMINATION)
    return coins
