from typing import Tuple, List

import pytest

from fixtures.const import ETHER_NAME, COIN_DENOMINATION, w3
from helpers import parity, deployer, erc20, participate


@pytest.fixture(scope='module')
def setup() -> List:
    """Setup accounts on a parity dev node."""
    accounts = setup_accounts()
    deployed_contracts = deployer.deploy_all_contracts(w3.eth.defaultAccount)
    yield accounts, deployed_contracts

    for i in accounts:
        parity.delete_account(i.address)


@pytest.fixture(scope='module')
def setup_participate() -> Tuple[List, List]:
    """Setup accounts on a parity dev node and participate some coins with the first account."""
    accounts = setup_accounts()
    deployed_contracts = deployer.deploy_all_contracts(w3.eth.defaultAccount)
    coins = participate_account(accounts[1].address, deployed_contracts)
    yield accounts, deployed_contracts, coins

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
    return accounts


def participate_account(account_address, deployed_contracts) -> List:
    """
    Make the given account participate.

    :param account_address: address to the account to participate
    :param deployed_contracts: instances of the deployed contracts
    :return: list of coins
    """
    # getting deployed plasma address
    plasma_address = deployed_contracts.plasma_instance.address
    # transfering erc20 tokens to account_address so she can participate into plasma contract.
    erc20.transfer(account_address, w3.toWei(5000000, ETHER_NAME), deployed_contracts.erc20_instance)
    # account_address approving the tokens to plasma_address so when participate function is called the
    # tokens will be transfered from her address to plasma_address
    erc20.approve(plasma_address, account_address, w3.toWei(5000000, ETHER_NAME), deployed_contracts.erc20_instance)
    # participating to plasma 10 times with denomination 5000 for each token
    coins = participate.participate(deployed_contracts, account_address, 10, COIN_DENOMINATION)
    return coins
