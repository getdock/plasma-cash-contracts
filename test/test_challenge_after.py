from itertools import count

import pytest

import helpers.events
import helpers.utils
from helpers import events, utils
from helpers.const import COIN_DENOMINATION

BLOCK_COUNTER = count(start=1_000, step=1_000)
COIN_COUNTER = count(start=0, step=1)


def test_owned_coin(setup_participate):
    '''
        Assert the coins returned by participate are created as they should.
    '''
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    alice_coins = deployed_contracts.erc721_instance.functions.getOwnedTokens(alice_addr).call()
    assert coins == alice_coins


def test_challenge_after_1(setup_participate):
    """
    Bob tries to challenge an Exit that doesnt exist
    """
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address

    # alice deposit transaction
    token_uid = next(COIN_COUNTER)
    previous_block = 0
    args = (coins[token_uid], previous_block, COIN_DENOMINATION, alice_addr, alice_addr)
    alice_alice = utils.generate_tx(*args)

    # alice sends coin to bob
    # previous_block = 1
    previous_block = deployed_contracts.plasma_instance.functions.getPlasmaCoin(coins[token_uid]).call()[1]
    args = (coins[token_uid], previous_block, COIN_DENOMINATION, bob_addr, alice_addr)
    alice_bob = helpers.utils.generate_tx(*args)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[token_uid], alice_bob["tx_hash"], block_height)
    alice_bob["proof"], alice_bob["block_number"] = helpers.utils.generate_block(*args)

    with pytest.raises(Exception):
        # bob tries to challenge a non-exiting coin, which should fails
        helpers.events.challenge_after(
            deployed_contracts.plasma_instance,
            coins[token_uid],
            alice_bob["block_number"],
            alice_bob["tx"],
            alice_bob["proof"],
            alice_bob["signature"],
            bob_addr
        )


def test_challenge_after_2(setup_participate):
    '''
        Oscar tries to a exit a spent coin

        Alice legitimately sends coin to Bob
        Bob sends coin to Oscar
        Oscar sends coin to Charlie
        Oscar tries to exit but Charlie challenges and wins.
    '''
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address
    charlie_addr = accounts[4].address

    # alice deposit transaction
    token_uid = next(COIN_COUNTER)
    previous_block = 0
    args = (coins[token_uid], previous_block, COIN_DENOMINATION, alice_addr, alice_addr)
    alice_alice = helpers.utils.generate_tx(*args)

    # alice sends coin to bob
    # previous_block = 2
    previous_block = deployed_contracts.plasma_instance.functions.getPlasmaCoin(coins[token_uid]).call()[1]
    args = (coins[token_uid], previous_block, COIN_DENOMINATION, bob_addr, alice_addr)
    alice_bob = helpers.utils.generate_tx(*args)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[token_uid], alice_bob["tx_hash"], block_height)
    alice_bob["proof"], alice_bob["block_number"] = helpers.utils.generate_block(*args)

    # bob sends coin to oscar
    bob_oscar = utils.generate_tx(
        coins[token_uid],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        oscar_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[token_uid], bob_oscar["tx_hash"], block_height)
    bob_oscar["proof"], bob_oscar["block_number"] = helpers.utils.generate_block(*args)

    # oscar sends coin to charlie
    oscar_charlie = utils.generate_tx(
        coins[token_uid],
        bob_oscar["block_number"],
        COIN_DENOMINATION,
        charlie_addr,
        oscar_addr)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[token_uid], oscar_charlie["tx_hash"], block_height)
    oscar_charlie["proof"], oscar_charlie["block_number"] = helpers.utils.generate_block(*args)

    # oscar starts exit with a coin he has sent to charlie
    events.start_exit(
        deployed_contracts.plasma_instance,
        coins[token_uid],
        alice_bob["tx"],
        bob_oscar["tx"],
        alice_bob["proof"],
        bob_oscar["proof"],
        bob_oscar["signature"],
        [alice_bob["block_number"], bob_oscar["block_number"]],
        oscar_addr
    )

    # charlie challenges the exit successfully
    helpers.events.challenge_after(
        deployed_contracts.plasma_instance,
        coins[token_uid],
        oscar_charlie["block_number"],
        oscar_charlie["tx"],
        oscar_charlie["proof"],
        oscar_charlie["signature"],
        charlie_addr
    )


def test_challenge_after_3(setup_participate):
    '''
        Same as above but with invalid signature provided...
        Thus oscar can exit a double spent coin.
    '''
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address
    charlie_addr = accounts[4].address

    # alice deposit transaction
    token_uid = next(COIN_COUNTER)
    previous_block = 0
    args = (coins[token_uid], previous_block, COIN_DENOMINATION, alice_addr, alice_addr)
    alice_alice = helpers.utils.generate_tx(*args)

    # alice sends coin to bob
    # previous_block = 3
    previous_block = deployed_contracts.plasma_instance.functions.getPlasmaCoin(coins[token_uid]).call()[1]
    args = (coins[token_uid], previous_block, COIN_DENOMINATION, bob_addr, alice_addr)
    alice_bob = helpers.utils.generate_tx(*args)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[token_uid], alice_bob["tx_hash"], block_height)
    alice_bob["proof"], alice_bob["block_number"] = helpers.utils.generate_block(*args)

    # bob sends coin to oscar
    bob_oscar = utils.generate_tx(
        coins[token_uid],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        oscar_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[token_uid], bob_oscar["tx_hash"], block_height)
    bob_oscar["proof"], bob_oscar["block_number"] = helpers.utils.generate_block(*args)

    # invalid signature : coins[token_uid], bob_oscar["block_number"], COIN_DENOMINATION, charlie_addr,
    # --> charlie <-- has to be oscar
    oscar_charlie = utils.generate_tx(
        coins[token_uid],
        bob_oscar["block_number"],
        COIN_DENOMINATION,
        charlie_addr,
        charlie_addr)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[token_uid], oscar_charlie["tx_hash"], block_height)
    oscar_charlie["proof"], oscar_charlie["block_number"] = helpers.utils.generate_block(*args)

    # oscar starts exit...
    events.start_exit(
        deployed_contracts.plasma_instance,
        coins[token_uid],
        alice_bob["tx"],
        bob_oscar["tx"],
        alice_bob["proof"],
        bob_oscar["proof"],
        bob_oscar["signature"],
        [alice_bob["block_number"], bob_oscar["block_number"]],
        oscar_addr
    )

    # charlie challenges oscar but fails
    with pytest.raises(Exception):
        helpers.events.challenge_after(
            deployed_contracts.plasma_instance,
            coins[token_uid],
            oscar_charlie["block_number"],
            oscar_charlie["tx"],
            oscar_charlie["proof"],
            oscar_charlie["signature"],
            charlie_addr
        )

    # oscar finishes exit
    events.finish_exit(deployed_contracts, coins[token_uid], oscar_addr)


def test_challenge_after_4(setup_participate):
    '''
        Same as above but with invalid merkle proof provided...
        Thus oscar can exit a double sped coin.
    '''
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address
    charlie_addr = accounts[4].address

    # alice deposit transaction
    token_uid = next(COIN_COUNTER)
    previous_block = 0
    args = (coins[token_uid], previous_block, COIN_DENOMINATION, alice_addr, alice_addr)
    alice_alice = utils.generate_tx(*args)

    # alice sends coin to bob
    # previous_block = 4
    previous_block = deployed_contracts.plasma_instance.functions.getPlasmaCoin(coins[token_uid]).call()[1]
    args = (coins[token_uid], previous_block, COIN_DENOMINATION, bob_addr, alice_addr)
    alice_bob = utils.generate_tx(*args)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[token_uid], alice_bob["tx_hash"], block_height)
    alice_bob["proof"], alice_bob["block_number"] = helpers.utils.generate_block(*args)

    # bob sends coin to oscar
    bob_oscar = helpers.utils.generate_tx(
        coins[token_uid],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        oscar_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[token_uid], bob_oscar["tx_hash"], block_height)
    bob_oscar["proof"], bob_oscar["block_number"] = helpers.utils.generate_block(*args)

    # oscar to charlie transaction
    oscar_charlie = utils.generate_tx(
        coins[token_uid],
        bob_oscar["block_number"],
        COIN_DENOMINATION,
        charlie_addr,
        oscar_addr)

    # invalid merkle proof: utils.block(
    # deployed_contracts.plasma_instance, plasma_instance, -->coins[1]<-- it has to be coins[token_uid],
    # oscar_charlie["tx_hash"], 10000)
    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[1], oscar_charlie["tx_hash"], block_height)
    oscar_charlie["proof"], oscar_charlie["block_number"] = helpers.utils.generate_block(*args)

    # oscar starts exit...
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

    # it should fail
    with pytest.raises(Exception):
        # charlie challenges oscar_addr, but fails
        helpers.events.challenge_after(
            deployed_contracts.plasma_instance,
            coins[token_uid],
            oscar_charlie["block_number"],
            oscar_charlie["tx"],
            oscar_charlie["proof"],
            oscar_charlie["signature"],
            charlie_addr
        )
        # Invalid merkle proof provided!

    # oscar finishes exit
    events.finish_exit(deployed_contracts, coins[token_uid], oscar_addr)


def test_challenge_after_5(setup_participate):
    '''
        Same as above but with invalid tx provided...
        Thus oscar can exit a double spend coin.
    '''
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address
    charlie_addr = accounts[4].address

    # alice deposit transaction
    token_uid = next(COIN_COUNTER)
    previous_block = 0
    args = (coins[token_uid], previous_block, COIN_DENOMINATION, alice_addr, alice_addr)
    alice_alice = utils.generate_tx(*args)

    # alice sends coin to bob
    # previous_block = 5
    previous_block = deployed_contracts.plasma_instance.functions.getPlasmaCoin(coins[token_uid]).call()[1]
    args = (coins[token_uid], previous_block, COIN_DENOMINATION, bob_addr, alice_addr)
    alice_bob = helpers.utils.generate_tx(*args)

    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[token_uid], alice_bob["tx_hash"], block_height)
    alice_bob["proof"], alice_bob["block_number"] = helpers.utils.generate_block(*args)

    # bob sends coin to oscar
    bob_oscar = helpers.utils.generate_tx(
        coins[token_uid],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        oscar_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[token_uid], bob_oscar["tx_hash"], block_height)
    bob_oscar["proof"], bob_oscar["block_number"] = helpers.utils.generate_block(*args)

    # oscar sends coin to charlie
    oscar_charlie = helpers.utils.generate_tx(
        coins[token_uid],
        bob_oscar["block_number"],
        COIN_DENOMINATION,
        charlie_addr,
        oscar_addr)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[token_uid], oscar_charlie["tx_hash"], block_height)
    oscar_charlie["proof"], oscar_charlie["block_number"] = helpers.utils.generate_block(*args)

    # oscar starts exit...
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

    # it should fail
    with pytest.raises(Exception):
        # charlie challenges oscar but fails
        helpers.events.challenge_after(
            deployed_contracts.plasma_instance,
            coins[token_uid],
            oscar_charlie["block_number"],
            bob_oscar["tx"],  # invalid tx provided, it has to be oscar_charlie["tx"]
            oscar_charlie["proof"],
            oscar_charlie["signature"],
            charlie_addr
        )

    # oscar finishes exit
    events.finish_exit(deployed_contracts, coins[token_uid], oscar_addr)


def test_challenge_after_6(setup_participate):
    '''
        No one challenges oscar so he can exit a double spend coin.
    '''
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address
    charlie_addr = accounts[4].address

    # alice deposit transaction
    token_uid = next(COIN_COUNTER)
    previous_block = 0
    args = (coins[token_uid], previous_block, COIN_DENOMINATION, alice_addr, alice_addr)
    alice_alice = helpers.utils.generate_tx(*args)

    # alice sends coin to bob
    # previous_block = 6
    previous_block = deployed_contracts.plasma_instance.functions.getPlasmaCoin(coins[token_uid]).call()[1]
    args = (coins[token_uid], previous_block, COIN_DENOMINATION, bob_addr, alice_addr)
    alice_bob = helpers.utils.generate_tx(*args)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[token_uid], alice_bob["tx_hash"], block_height)
    alice_bob["proof"], alice_bob["block_number"] = helpers.utils.generate_block(*args)

    # bob sends coin to oscar
    bob_oscar = helpers.utils.generate_tx(
        coins[token_uid],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        oscar_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[token_uid], bob_oscar["tx_hash"], block_height)
    bob_oscar["proof"], bob_oscar["block_number"] = helpers.utils.generate_block(*args)

    # oscar sends coin to charlie
    oscar_charlie = helpers.utils.generate_tx(
        coins[token_uid],
        bob_oscar["block_number"],
        COIN_DENOMINATION,
        charlie_addr,
        oscar_addr)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[token_uid], oscar_charlie["tx_hash"], block_height)
    oscar_charlie["proof"], oscar_charlie["block_number"] = helpers.utils.generate_block(*args)

    # oscar starts exit...
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

    # oscar finishes exit
    events.finish_exit(deployed_contracts, coins[token_uid], oscar_addr)


def test_challenge_after_7(setup_participate):
    '''
        Cannot challenge with earlier tx
    '''
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address

    # alice deposit transaction
    token_uid = next(COIN_COUNTER)
    previous_block = 0
    args = (coins[token_uid], previous_block, COIN_DENOMINATION, alice_addr, alice_addr)
    alice_alice = helpers.utils.generate_tx(*args)

    # alice sends coin to bob
    # previous_block = 7
    previous_block = deployed_contracts.plasma_instance.functions.getPlasmaCoin(coins[token_uid]).call()[1]
    args = (coins[token_uid], previous_block, COIN_DENOMINATION, bob_addr, alice_addr)
    alice_bob = helpers.utils.generate_tx(*args)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[token_uid], alice_bob["tx_hash"], block_height)
    alice_bob["proof"], alice_bob["block_number"] = helpers.utils.generate_block(*args)

    # bob sends coin to oscar
    bob_oscar = helpers.utils.generate_tx(
        coins[token_uid],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        oscar_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[token_uid], bob_oscar["tx_hash"], block_height)
    bob_oscar["proof"], bob_oscar["block_number"] = helpers.utils.generate_block(*args)

    # oscar starts exit...
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

    # it should fail
    with pytest.raises(Exception):
        # bob challenge oscar's exit
        helpers.events.challenge_after(
            deployed_contracts.plasma_instance,
            coins[token_uid],
            alice_bob["block_number"],
            alice_bob["tx"],
            alice_bob["proof"],
            alice_bob["signature"],
            bob_addr
        )
        # he fails because he challenged with earlier tx!

    # oscar finishes exit
    events.finish_exit(deployed_contracts, coins[token_uid], oscar_addr)


def test_challenge_after_8(setup_participate):
    '''
        challenge with a direct spend
    '''
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address

    # deposit tx of alice
    token_uid = next(COIN_COUNTER)
    previous_block = 0
    args = (coins[token_uid], previous_block, COIN_DENOMINATION, alice_addr, alice_addr)
    alice_alice = helpers.utils.generate_tx(*args)

    # alice sends coin to bob
    # previous_block = 8
    previous_block = deployed_contracts.plasma_instance.functions.getPlasmaCoin(coins[token_uid]).call()[1]
    args = (coins[token_uid], previous_block, COIN_DENOMINATION, bob_addr, alice_addr)
    alice_bob = helpers.utils.generate_tx(*args)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[token_uid], alice_bob["tx_hash"], block_height)
    alice_bob["proof"], alice_bob["block_number"] = helpers.utils.generate_block(*args)

    # bob sends coin to oscar
    bob_oscar = helpers.utils.generate_tx(
        coins[token_uid],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        oscar_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[token_uid], bob_oscar["tx_hash"], block_height)
    bob_oscar["proof"], bob_oscar["block_number"] = helpers.utils.generate_block(*args)

    # bob starts exit
    events.start_exit(
        deployed_contracts.plasma_instance,
        coins[token_uid],
        alice_alice["tx"],
        alice_bob["tx"],
        '0x',
        alice_bob["proof"],
        alice_bob["signature"],
        [8, alice_bob["block_number"]],
        bob_addr
    )

    # oscar challenges bob...
    helpers.events.challenge_after(
        deployed_contracts.plasma_instance,
        coins[token_uid],
        bob_oscar["block_number"],
        bob_oscar["tx"],
        bob_oscar["proof"],
        bob_oscar["signature"],
        oscar_addr,
    )
    # oscar challenges successfully


def test_challenge_after_9(setup_participate):
    '''
        Cannot challenge with non-direct spend
    '''
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address
    charlie_addr = accounts[4].address

    # alice deposit transaction
    token_uid = next(COIN_COUNTER)
    previous_block = 0
    args = (coins[token_uid], previous_block, COIN_DENOMINATION, alice_addr, alice_addr)
    alice_alice = helpers.utils.generate_tx(*args)

    # alice sends coin to bob
    # previous_block = 9
    previous_block = deployed_contracts.plasma_instance.functions.getPlasmaCoin(coins[token_uid]).call()[1]
    args = (coins[token_uid], previous_block, COIN_DENOMINATION, bob_addr, alice_addr)
    alice_bob = helpers.utils.generate_tx(*args)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[token_uid], alice_bob["tx_hash"], block_height)
    alice_bob["proof"], alice_bob["block_number"] = helpers.utils.generate_block(*args)

    # bob sends coin to oscar
    bob_oscar = helpers.utils.generate_tx(
        coins[token_uid],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        oscar_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[token_uid], bob_oscar["tx_hash"], block_height)
    bob_oscar["proof"], bob_oscar["block_number"] = helpers.utils.generate_block(*args)

    # oscar sends coin to charlie
    oscar_charlie = helpers.utils.generate_tx(
        coins[token_uid],
        bob_oscar["block_number"],
        COIN_DENOMINATION,
        charlie_addr,
        oscar_addr)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[token_uid], oscar_charlie["tx_hash"], block_height)
    oscar_charlie["proof"], oscar_charlie["block_number"] = helpers.utils.generate_block(*args)

    # bob starts exit
    events.start_exit(
        deployed_contracts.plasma_instance,
        coins[token_uid],
        alice_alice["tx"],
        alice_bob["tx"],
        '0x',
        alice_bob["proof"],
        alice_bob["signature"],
        [9, alice_bob["block_number"]],
        bob_addr
    )

    with pytest.raises(Exception):
        # charlie challenges bob
        helpers.events.challenge_after(
            deployed_contracts,
            coins[token_uid],
            oscar_charlie["block_number"],
            oscar_charlie["tx"],
            oscar_charlie["proof"],
            oscar_charlie["signature"],
            charlie_addr
        )
        # Cannot challenge with non-direct spend.

    # bob finishes exit
    events.finish_exit(deployed_contracts, coins[token_uid], bob_addr)
