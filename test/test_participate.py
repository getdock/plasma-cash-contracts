import pytest

import helpers.utils
from helpers import utils
from helpers.const import COIN_DENOMINATION, ETHER_NAME
from helpers.const import W3 as w3


def test_successful_participate(setup):
    """
        user owns and approves tokens to plasma contract
        and should be able to create one DOCK token with specified denomination
    """
    accounts, deployed_contracts = setup
    peter_addr = accounts[1].address

    plasma_address = deployed_contracts.plasma_instance.address

    helpers.utils.erc20_transfer(peter_addr, COIN_DENOMINATION, deployed_contracts.erc20_instance)
    helpers.utils.erc20_approve(plasma_address, peter_addr, COIN_DENOMINATION, deployed_contracts.erc20_instance)

    coins = utils.participate(deployed_contracts, peter_addr, 1, COIN_DENOMINATION)

    assert len(coins) == 1


def test_unsuccessful_participate(setup):
    """
        user owns and approves tokens to plasma contract
        and should not be able to create DOCK token with different denomination
    """
    accounts, deployed_contracts = setup
    alice_addr = accounts[2].address

    wrong_denomination = 6_000
    assert wrong_denomination != COIN_DENOMINATION

    plasma_address = deployed_contracts.plasma_instance.address

    helpers.utils.erc20_transfer(alice_addr, COIN_DENOMINATION, deployed_contracts.erc20_instance)
    helpers.utils.erc20_approve(plasma_address, alice_addr, COIN_DENOMINATION, deployed_contracts.erc20_instance)

    new_denomination = w3.toWei(wrong_denomination, ETHER_NAME)

    with pytest.raises(Exception):
        utils.participate(deployed_contracts, alice_addr, 1, new_denomination)


def test_out_of_funds_participate(setup):
    """
        user owns 10 dock tokens in decimals
        and approves 5 dock tokens to plasma plasma
        user wants to mint(participate) 2 times to plasma with coin denomination 5
        he can't do that since the amount approved is 5 dock tokens in decimals
    """
    accounts, deployed_contracts = setup
    peter_addr = accounts[1].address
    oscar_addr = accounts[3].address

    plasma_address = deployed_contracts.plasma_instance.address
    helpers.utils.erc20_transfer(oscar_addr, w3.toWei(10, ETHER_NAME), deployed_contracts.erc20_instance)
    helpers.utils.erc20_approve(plasma_address, peter_addr, w3.toWei(5, ETHER_NAME), deployed_contracts.erc20_instance)
    denomination = w3.toWei(5, ETHER_NAME)
    with pytest.raises(Exception):
        utils.participate(deployed_contracts, oscar_addr, 2, denomination)
