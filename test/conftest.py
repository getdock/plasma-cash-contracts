from typing import Tuple, List

import pytest

import helpers.config
from helpers import parity
from helpers.utils import setup_accounts, participate_account


@pytest.fixture(scope='module')
def setup() -> List:
    """Setup accounts on a parity dev node."""
    from helpers.const import w3
    accounts = setup_accounts()
    deployed_contracts = helpers.config.deploy_all_contracts(w3)
    yield accounts, deployed_contracts

    for i in accounts:
        parity.delete_account(i.address)


@pytest.fixture(scope='module')
def setup_participate() -> Tuple[List, List]:
    """Setup accounts on a parity dev node and participate some coins with the first account."""
    from helpers.const import w3
    accounts = setup_accounts()
    deployed_contracts = helpers.config.deploy_all_contracts(w3)
    coins = participate_account(accounts[1].address, deployed_contracts)
    yield accounts, deployed_contracts, coins

    for i in accounts:
        parity.delete_account(i.address)
