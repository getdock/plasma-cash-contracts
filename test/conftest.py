import os
from typing import Tuple, List

import pytest

from fixtures.const import ETHER_NAME, COIN_DENOMINATION
from helpers import parity, deployer, erc20, participate, instances
from helpers.web3Provider import w3


@pytest.fixture(scope='module')
def accounts() -> List:
    # setup_parity_dev_node()
    accounts = setup_accounts()
    yield accounts

    # Delete all the accounts after using them.
    for i in accounts:
        parity.deleteAccount(i.address)
    # reset_parity_dev_node()


@pytest.fixture(scope='module')
def setup_participate() -> Tuple[List, List]:
    # setup_parity_dev_node()
    accounts = setup_accounts()
    coins = participate_account(accounts[1].address)
    yield accounts, coins

    # Delete all the accounts after using them.
    for i in accounts:
        parity.deleteAccount(i.address)
    # reset_parity_dev_node()


def setup_accounts(count: int = 8) -> List:
    """Create some accounts in the parity node."""
    accounts = parity.generateAccounts(count)
    # parity.sendTransaction() is the function which sends sends some amount of ether to an account.
    for i in accounts:
        parity.sendTransaction(i.address)
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

    # def setup_parity_dev_node() -> str:
    """Set up a parity node in docker."""
    command = "sudo docker run -d -ti -v ~/.parity/plasma-mvp/parity/:/home/.local/share/io.parity.ethereum/ " \
              "-p 8545:8545 --name dock-mvp parity/parity:stable --chain dev --jsonrpc-interface all --jsonrpc-apis all" \
              " --jsonrpc-cors all  --jsonrpc-hosts all"
    container_id = os.system(command)
    return container_id


def reset_parity_dev_node() -> str:
    """Reset a running parity node in docker."""
    # TODO: add running tests and switch to docker-py
    command = "sudo docker stop dock-mvp; sudo docker rm dock-mvp; sudo rm -r ~/.parity; sudo mkdir ~/.parity; " \
              "sudo chmod -R 777 ~/.parity; parityup"
    container_id = os.system(command)
    return container_id
