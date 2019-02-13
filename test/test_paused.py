import pytest

import helpers.utils
from helpers import utils
from helpers.const import COIN_DENOMINATION, ETHER_NAME
from helpers.const import W3 as w3


def test_paused(setup):
    '''
        pause, unpause particpation in contract
    '''
    accounts, deployed_contracts = setup
    alice_addr = accounts[1].address

    plasma_instance = deployed_contracts.plasma_instance

    kwargs = {'from': w3.eth.accounts[0]}
    w3.personal.unlockAccount(w3.eth.defaultAccount, '')
    tx_hash = plasma_instance.functions.pause(True).transact(kwargs)
    assert w3.eth.waitForTransactionReceipt(tx_hash).status

    helpers.utils.erc20_transfer(alice_addr, w3.toWei(5_000_000, ETHER_NAME), deployed_contracts.erc20_instance)
    helpers.utils.erc20_approve(plasma_instance.address, alice_addr, w3.toWei(5_000_000, ETHER_NAME),
                                deployed_contracts.erc20_instance)

    # Plasma is paused so no one can participate
    with pytest.raises(Exception):
        utils.participate(deployed_contracts, alice_addr, 2, COIN_DENOMINATION)

    w3.personal.unlockAccount(w3.eth.defaultAccount, '')
    tx_hash = plasma_instance.functions.pause(False).transact(kwargs)
    assert w3.eth.waitForTransactionReceipt(tx_hash).status

    # Plasma now is not paused so every one can participate
    utils.participate(deployed_contracts, alice_addr, 2, COIN_DENOMINATION)
