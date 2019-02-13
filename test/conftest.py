from typing import List, Tuple

import pytest

import helpers.config
import helpers.utils
from helpers.utils import participate_account, setup_accounts


@pytest.fixture(scope='module')
def setup() -> List:
    '''
        Setup accounts on a parity dev node
    '''
    from helpers.const import W3 as w3
    accounts = setup_accounts()
    deployed_contracts = helpers.config.deploy_all_contracts(w3)
    yield accounts, deployed_contracts

    for i in accounts:
        helpers.utils.delete_parity_account(i.address)


@pytest.fixture(scope='module')
def setup_participate() -> Tuple[List, List]:
    '''
        Setup accounts on a parity dev node and participate some coins with the first account
    '''
    from helpers.const import W3 as w3
    accounts = setup_accounts()
    deployed_contracts = helpers.config.deploy_all_contracts(w3)
    coins = participate_account(accounts[1].address, deployed_contracts)
    yield accounts, deployed_contracts, coins

    for i in accounts:
        helpers.utils.delete_parity_account(i.address)
