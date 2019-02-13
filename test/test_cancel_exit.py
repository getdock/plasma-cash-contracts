from itertools import count

import pytest

import helpers.utils
from helpers import events
from helpers.const import COIN_DENOMINATION

BLOCK_COUNTER = count(start=1_000, step=1_000)
COIN_COUNTER = count(start=0, step=1)


def test_owned_coin(setup_participate):
    '''
        Assert the coins returned by participate are created as they should
    '''
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    alice_coins = deployed_contracts.erc721_instance.functions.getOwnedTokens(alice_addr).call()
    assert coins == alice_coins


def test_successful_cancel_exit(setup_participate):
    '''
    '''
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address

    # alice deposit transaction.
    token_uid = next(COIN_COUNTER)
    previous_block = 0
    args = (coins[token_uid], previous_block, COIN_DENOMINATION, alice_addr, alice_addr)
    alice_alice = helpers.utils.generate_tx(*args)

    # alice sends coin to bob.
    previous_block = deployed_contracts.plasma_instance.functions.getPlasmaCoin(coins[token_uid]).call()[1]
    args = (coins[token_uid], previous_block, COIN_DENOMINATION, bob_addr, alice_addr)
    alice_bob = helpers.utils.generate_tx(*args)

    # plasma block is generated and submited to mainnet.
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[token_uid], alice_bob["tx_hash"], block_height)
    alice_bob["proof"], alice_bob["block_number"] = helpers.utils.generate_block(*args)

    # bob sends coin to oscar.
    args = (coins[token_uid], alice_bob["block_number"], COIN_DENOMINATION, oscar_addr, bob_addr)
    bob_oscar = helpers.utils.generate_tx(*args)

    # plasma block is generated and submited to mainnet.
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[token_uid], bob_oscar["tx_hash"], block_height)
    bob_oscar["proof"], bob_oscar["block_number"] = helpers.utils.generate_block(*args)

    # oscar starts exit.
    events.start_exit(
        deployed_contracts.plasma_instance,
        coins[token_uid],
        alice_bob["tx"],
        bob_oscar["tx"],
        alice_bob["proof"],
        bob_oscar["proof"],
        bob_oscar["signature"],
        [alice_bob["block_number"], bob_oscar["block_number"]],
        oscar_addr,
    )

    # calling cancelExit function from exit script.
    # exit is canceled by oscar.
    events.cancel_exit(deployed_contracts.plasma_instance, coins[0], oscar_addr)


def test_unsuccessful_cancel_exit(setup_participate):
    '''
        Bob trys to cancel an Exit he has not started, he fails to do it
    '''
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address

    # alice deposit transaction
    previous_block = 0
    token_uid = next(COIN_COUNTER)
    args = (coins[token_uid], previous_block, COIN_DENOMINATION, alice_addr, alice_addr)
    alice_alice = helpers.utils.generate_tx(*args)

    # alice sends coin to bob.
    previous_block = deployed_contracts.plasma_instance.functions.getPlasmaCoin(coins[token_uid]).call()[1]
    args = (coins[token_uid], previous_block, COIN_DENOMINATION, bob_addr, alice_addr)
    alice_bob = helpers.utils.generate_tx(*args)

    # plasma block is generated and submited to rootchain.
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[token_uid], alice_bob["tx_hash"], block_height)
    alice_bob["proof"], alice_bob["block_number"] = helpers.utils.generate_block(*args)

    # bob sends coin to oscar.
    args = (coins[token_uid], alice_bob["block_number"], COIN_DENOMINATION, oscar_addr, bob_addr)
    bob_oscar = helpers.utils.generate_tx(*args)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[token_uid], bob_oscar["tx_hash"], block_height)
    bob_oscar["proof"], bob_oscar["block_number"] = helpers.utils.generate_block(*args)

    # oscar starts exit
    events.start_exit(
        deployed_contracts.plasma_instance,
        coins[token_uid],
        alice_bob["tx"],
        bob_oscar["tx"],
        alice_bob["proof"],
        bob_oscar["proof"],
        bob_oscar["signature"],
        [alice_bob["block_number"], bob_oscar["block_number"]],
        oscar_addr,
    )

    # calling cancelExit function from exit script.
    # bob will try to cancel an exit he has not started, he fails to do it.
    with pytest.raises(Exception):
        events.cancel_exit(deployed_contracts.plasma_instance, coins[token_uid], bob_addr)
