import pytest

from fixtures.const import COIN_DENOMINATION, ETHER_NAME, w3
from helpers import utils, erc20


def test_successful_participate(setup):
    """
    user owns 5000 dock tokens in decimals
    user approves plasma contract 5000 dock tokens

    user should be able to create one dock token with denomination 5000 since
    that is the amount owned and approved by user.

    """
    accounts, deployed_contracts = setup
    peter_addr = accounts[1].address

    plasma_address = deployed_contracts.plasma_instance.address

    erc20.transfer(peter_addr, COIN_DENOMINATION, deployed_contracts.erc20_instance)
    erc20.approve(plasma_address, peter_addr, COIN_DENOMINATION, deployed_contracts.erc20_instance)

    coins = utils.participate(deployed_contracts, peter_addr, 1, COIN_DENOMINATION)

    assert len(coins) == 1


def test_unsuccessful_participate(setup):
    """
    user owns 5000 dock tokens in decimals
    user approves plasma contract 5000 dock tokens

    user should not be able to create dock token with denomination 6000 or more since
    the amount owned and approved by user is 5000.

    """
    accounts, deployed_contracts = setup
    alice_addr = accounts[2].address

    plasma_address = deployed_contracts.plasma_instance.address

    erc20.transfer(alice_addr, COIN_DENOMINATION, deployed_contracts.erc20_instance)
    erc20.approve(plasma_address, alice_addr, COIN_DENOMINATION, deployed_contracts.erc20_instance)

    new_denomination = w3.toWei(6000, ETHER_NAME)

    with pytest.raises(Exception):
        utils.participate(deployed_contracts, alice_addr, 1, new_denomination)


def test_outOfBalance_participate(setup):
    """

    user owns 10 dock tokens in decimals
    user approves 5 dock tokens to plasma plasma
    user wants to mint(participate) 2 times to plasma with coins denomination 5
    he cant do so since the amount approved is 5 dock tokens in decimals

    """
    accounts, deployed_contracts = setup
    peter_addr = accounts[1].address
    oscar_addr = accounts[3].address

    plasma_address = deployed_contracts.plasma_instance.address

    deno = w3.toWei(5, ETHER_NAME)

    erc20.transfer(oscar_addr, w3.toWei(10, ETHER_NAME), deployed_contracts.erc20_instance)
    erc20.approve(plasma_address, peter_addr, w3.toWei(5, ETHER_NAME), deployed_contracts.erc20_instance)

    with pytest.raises(Exception):
        utils.participate(deployed_contracts, oscar_addr, 2, deno)
