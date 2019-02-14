from itertools import count

import pytest

import helpers.events
import helpers.utils
from helpers import events
from helpers.const import COIN_DENOMINATION

BLOCK_COUNTER = count(start=1_000, step=1_000)


def test_owned_coin(setup_participate):
    '''
        Assert the coins returned by participate are created as they should.
    '''
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    alice_coins = deployed_contracts.erc721_instance.functions.getOwnedTokens(alice_addr).call()
    assert coins == alice_coins


def test_failing_challenge_1(setup_participate):
    '''
        challenge an Exit that doesnt exist
    '''
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address
    charlie_addr = accounts[4].address

    # alice deposit tx
    previous_block = 0
    args = (coins[0], previous_block, COIN_DENOMINATION, alice_addr, alice_addr)
    alice_alice = helpers.utils.generate_tx(*args)

    # alice to bob tx
    previous_block = deployed_contracts.plasma_instance.functions.getPlasmaCoin(coins[0]).call()[1]
    args = (coins[0], previous_block, COIN_DENOMINATION, bob_addr, alice_addr)
    alice_bob = helpers.utils.generate_tx(*args)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[0], alice_bob["tx_hash"], block_height)
    alice_bob["proof"], alice_bob["block_number"] = helpers.utils.generate_block(*args)

    # bob to oscar tx.
    bob_oscar = helpers.utils.generate_tx(
        coins[0],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        oscar_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[0], bob_oscar["tx_hash"], block_height)
    bob_oscar["proof"], bob_oscar["block_number"] = helpers.utils.generate_block(*args)

    # bob to charlie tx.
    bob_charlie = helpers.utils.generate_tx(
        coins[0],
        bob_oscar["block_number"],
        COIN_DENOMINATION,
        charlie_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[0], bob_charlie["tx_hash"], block_height)
    bob_charlie["proof"], bob_charlie["block_number"] = helpers.utils.generate_block(*args)

    # oscar challenges
    with pytest.raises(Exception):
        helpers.events.challenge_between(
            deployed_contracts.plasma_instance,
            coins[0],
            bob_oscar["block_number"],
            bob_oscar["tx"],
            bob_oscar["proof"],
            bob_oscar["signature"],
            oscar_addr
        )
        # Exit doesnt exist!


def test_successful_challenge_1(setup_participate):
    '''
        alice sends coin to bob
        bob tries to double spend and sends coin to oscar and charlie
    '''
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address
    charlie_addr = accounts[4].address

    # alice deposit transaction
    previous_block = 0
    args = (coins[1], previous_block, COIN_DENOMINATION, alice_addr, alice_addr)
    alice_alice = helpers.utils.generate_tx(*args)

    # alice to bob
    previous_block = deployed_contracts.plasma_instance.functions.getPlasmaCoin(coins[1]).call()[1]
    args = (coins[1], previous_block, COIN_DENOMINATION, bob_addr, alice_addr)
    alice_bob = helpers.utils.generate_tx(*args)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[1], alice_bob["tx_hash"], block_height)
    alice_bob["proof"], alice_bob["block_number"] = helpers.utils.generate_block(*args)

    # bob to oscar
    bob_oscar = helpers.utils.generate_tx(
        coins[1],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        oscar_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[1], bob_oscar["tx_hash"], block_height)
    bob_oscar["proof"], bob_oscar["block_number"] = helpers.utils.generate_block(*args)

    # bob to charlie | double spend
    bob_charlie = helpers.utils.generate_tx(
        coins[1],
        bob_oscar["block_number"],
        COIN_DENOMINATION,
        charlie_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[1], bob_charlie["tx_hash"], block_height)
    bob_charlie["proof"], bob_charlie["block_number"] = helpers.utils.generate_block(*args)

    # charlie starts exit
    events.start_exit(
        deployed_contracts.plasma_instance,
        coins[1],
        alice_bob["tx"],
        bob_charlie["tx"],
        alice_bob["proof"],
        bob_charlie["proof"],
        bob_charlie["signature"],
        [alice_bob["block_number"], bob_charlie["block_number"]],
        charlie_addr
    )

    # oscar challenges
    helpers.events.challenge_between(
        deployed_contracts.plasma_instance,
        coins[1],
        bob_oscar["block_number"],
        bob_oscar["tx"],
        bob_oscar["proof"],
        bob_oscar["signature"],
        oscar_addr
    )
    # oscar challenges succsefully


def test_failing_challenge_2(setup_participate):
    '''
        same challenge_1  but with invalid signature
    '''
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address
    charlie_addr = accounts[4].address

    # alice deposit transaction
    previous_block = 0
    alice_alice = helpers.utils.generate_tx(coins[2], previous_block, COIN_DENOMINATION, alice_addr, alice_addr)

    # alice sends coin to bob
    previous_block = deployed_contracts.plasma_instance.functions.getPlasmaCoin(coins[2]).call()[1]
    alice_bob = helpers.utils.generate_tx(coins[2], previous_block, COIN_DENOMINATION, bob_addr, alice_addr)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[2], alice_bob["tx_hash"], block_height)
    alice_bob["proof"], alice_bob["block_number"] = helpers.utils.generate_block(*args)

    # bob sends coin to oscar
    bob_oscar = helpers.utils.generate_tx(
        coins[2],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        oscar_addr,
        alice_addr
    )

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[2], bob_oscar["tx_hash"], block_height)
    bob_oscar["proof"], bob_oscar["block_number"] = helpers.utils.generate_block(*args)

    # bob sends coin to charlie.
    bob_charlie = helpers.utils.generate_tx(
        coins[2],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        charlie_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[2], bob_charlie["tx_hash"], block_height)
    bob_charlie["proof"], bob_charlie["block_number"] = helpers.utils.generate_block(*args)

    # charlie starts exit
    events.start_exit(
        deployed_contracts.plasma_instance,
        coins[2],
        alice_bob["tx"],
        bob_charlie["tx"],
        alice_bob["proof"],
        bob_charlie["proof"],
        bob_charlie["signature"],
        [alice_bob["block_number"], bob_charlie["block_number"]],
        charlie_addr
    )

    # oscar provides invalid signature, he fails to stop charlie's exit
    with pytest.raises(Exception):
        helpers.events.challenge_between(
            deployed_contracts.plasma_instance,
            coins[2],
            bob_oscar["block_number"],
            bob_oscar["tx"],
            bob_oscar["proof"],
            bob_oscar["signature"],
            oscar_addr
        )
        # Invalid signature provided!

    # charlie finishes exit.
    events.finish_exit(deployed_contracts, coins[2], charlie_addr)


def test_failing_challenge_3(setup_participate):
    '''
        same challenge_1  but with invalid merkle proof provided
    '''
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address
    charlie_addr = accounts[4].address

    previous_block = 0
    alice_alice = helpers.utils.generate_tx(coins[3], previous_block, COIN_DENOMINATION, alice_addr, alice_addr)

    # alice sends coin to bob
    previous_block = deployed_contracts.plasma_instance.functions.getPlasmaCoin(coins[3]).call()[1]
    alice_bob = helpers.utils.generate_tx(coins[3], previous_block, COIN_DENOMINATION, bob_addr, alice_addr)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[3], alice_bob["tx_hash"], block_height)
    alice_bob["proof"], alice_bob["block_number"] = helpers.utils.generate_block(*args)

    # bob sends coin to oscar
    bob_oscar = helpers.utils.generate_tx(
        coins[3],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        oscar_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[3], bob_oscar["tx_hash"], block_height)
    bob_oscar["proof"], bob_oscar["block_number"] = helpers.utils.generate_block(*args)

    # bob sends coin to charlie / charlie is a address owned by bob too.
    bob_charlie = helpers.utils.generate_tx(
        coins[3],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        charlie_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[3], bob_charlie["tx_hash"], block_height)
    bob_charlie["proof"], bob_charlie["block_number"] = helpers.utils.generate_block(*args)

    # oscar startes exit
    events.start_exit(
        deployed_contracts.plasma_instance,
        coins[3],
        alice_bob["tx"],
        bob_charlie["tx"],
        alice_bob["proof"],
        bob_charlie["proof"],
        bob_charlie["signature"],
        [alice_bob["block_number"], bob_charlie["block_number"]],
        charlie_addr
    )

    # oscar provides invalid merkle proof, he fails to stop charlie's exit
    with pytest.raises(Exception):
        helpers.events.challenge_between(
            deployed_contracts.plasma_instance,
            coins[3],
            bob_oscar["block_number"],
            bob_oscar["tx"],
            '0x12345678',
            bob_oscar["signature"],
            oscar_addr
        )
        # Invalid merkle proof provided!

    # charlie finishes exit.
    events.finish_exit(deployed_contracts, coins[3], charlie_addr)


def test_failing_challenge_4(setup_participate):
    '''
        same challenge_1  with invalid tx
    '''
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address
    charlie_addr = accounts[4].address

    previous_block = 0
    alice_alice = helpers.utils.generate_tx(coins[4], previous_block, COIN_DENOMINATION, alice_addr, alice_addr)

    # alice sends coin to bob
    previous_block = deployed_contracts.plasma_instance.functions.getPlasmaCoin(coins[4]).call()[1]
    alice_bob = helpers.utils.generate_tx(coins[4], previous_block, COIN_DENOMINATION, bob_addr, alice_addr)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[4], alice_bob["tx_hash"], block_height)
    alice_bob["proof"], alice_bob["block_number"] = helpers.utils.generate_block(*args)

    # bob sends coin to oscar
    bob_oscar = helpers.utils.generate_tx(
        coins[4],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        oscar_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[4], bob_oscar["tx_hash"], block_height)
    bob_oscar["proof"], bob_oscar["block_number"] = helpers.utils.generate_block(*args)

    # bob sends coin to charlie / charlie is a address owned by bob too.
    bob_charlie = helpers.utils.generate_tx(
        coins[4],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        charlie_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[4], bob_charlie["tx_hash"], block_height)
    bob_charlie['proof'], bob_charlie["block_number"] = helpers.utils.generate_block(*args)

    # charlie starts exit
    events.start_exit(
        deployed_contracts.plasma_instance,
        coins[4],
        alice_bob["tx"],
        bob_charlie["tx"],
        alice_bob["proof"],
        bob_charlie["proof"],
        bob_charlie["signature"],
        [alice_bob["block_number"], bob_charlie["block_number"]],
        charlie_addr
    )

    # oscar challenges
    with pytest.raises(Exception):
        helpers.events.challenge_between(
            deployed_contracts.plasma_instance,
            coins[4],
            bob_oscar["block_number"],
            alice_bob["tx"],
            bob_oscar["proof"],
            bob_oscar["signature"],
            oscar_addr
        )
        # Invalid tx provided!

    # charlie finishes exit
    events.finish_exit(deployed_contracts, coins[4], charlie_addr)


def test_successful_exit1(setup_participate):
    '''
        same challenge_1 but no one challenges and maturity period is achived and coin can be finalized
    '''
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address
    charlie_addr = accounts[4].address

    previous_block = 0
    alice_alice = helpers.utils.generate_tx(coins[5], previous_block, COIN_DENOMINATION, alice_addr, alice_addr)

    # alice sends coin to bob
    previous_block = deployed_contracts.plasma_instance.functions.getPlasmaCoin(coins[5]).call()[1]
    alice_bob = helpers.utils.generate_tx(coins[5], previous_block, COIN_DENOMINATION, bob_addr, alice_addr)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[5], alice_bob["tx_hash"], block_height)
    alice_bob["proof"], alice_bob["block_number"] = helpers.utils.generate_block(*args)

    # bob sends coin to oscar
    bob_oscar = helpers.utils.generate_tx(
        coins[5],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        oscar_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[5], bob_oscar["tx_hash"], block_height)
    bob_oscar["proof"], bob_oscar["block_number"] = helpers.utils.generate_block(*args)

    # bob sends coin to charlie
    bob_charlie = helpers.utils.generate_tx(
        coins[5],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        charlie_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[5], bob_charlie["tx_hash"], block_height)
    bob_charlie["proof"], bob_charlie["block_number"] = helpers.utils.generate_block(*args)

    # charlie starts exit
    events.start_exit(
        deployed_contracts.plasma_instance,
        coins[5],
        alice_bob["tx"],
        bob_charlie["tx"],
        alice_bob["proof"],
        bob_charlie["proof"],
        bob_charlie["signature"],
        [alice_bob["block_number"], bob_charlie["block_number"]],
        charlie_addr
    )

    # no one challenges thus charlie can finalize exit
    events.finish_exit(deployed_contracts, coins[5], charlie_addr)


def test_multiple_challenges(setup_participate):
    '''
        Multiple challenges | Later Spend(invalid), In Between Spend(valid)
          bob sends coin to oscar
          bob sends coin to charlie
          charlie sends coin to peter
          peter challenges but fails due to providing later spend
          oscar challenges with valid tx proving the double spend to charlie
    '''
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address
    charlie_addr = accounts[4].address
    peter_addr = accounts[5].address

    # alice deposit
    previous_block = 0
    alice_alice = helpers.utils.generate_tx(coins[6], previous_block, COIN_DENOMINATION, alice_addr, alice_addr)

    # alice sends coin to bob
    previous_block = deployed_contracts.plasma_instance.functions.getPlasmaCoin(coins[6]).call()[1]
    alice_bob = helpers.utils.generate_tx(coins[6], previous_block, COIN_DENOMINATION, bob_addr, alice_addr)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    alice_bob["proof"], alice_bob["block_number"] = helpers.utils.generate_block(
        deployed_contracts.plasma_instance, coins[6], alice_bob["tx_hash"], 19000)

    # bob sends coin to oscar
    bob_oscar = helpers.utils.generate_tx(
        coins[6],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        oscar_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[6], bob_oscar["tx_hash"], block_height)
    bob_oscar["proof"], bob_oscar["block_number"] = helpers.utils.generate_block(*args)

    # bob sends coin to charlie / charlie is a address owned by bob too.
    bob_charlie = helpers.utils.generate_tx(
        coins[6],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        charlie_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[6], bob_charlie["tx_hash"], block_height)
    bob_charlie["proof"], bob_charlie["block_number"] = helpers.utils.generate_block(*args)

    # bob sends coin to charlie / charlie is a address owned by bob too.
    charlie_peter = helpers.utils.generate_tx(
        coins[6],
        bob_charlie["block_number"],
        COIN_DENOMINATION,
        charlie_addr,
        charlie_addr)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[6], charlie_peter["tx_hash"], block_height)
    charlie_peter["proof"], charlie_peter["block_number"] = helpers.utils.generate_block(*args)

    # charlie starts exit
    events.start_exit(
        deployed_contracts.plasma_instance,
        coins[6],
        alice_bob["tx"],
        bob_charlie["tx"],
        alice_bob["proof"],
        bob_charlie["proof"],
        bob_charlie["signature"],
        [alice_bob["block_number"], bob_charlie["block_number"]],
        charlie_addr
    )

    # peter challenges charlie
    with pytest.raises(Exception):
        helpers.events.challenge_between(
            deployed_contracts.plasma_instance,
            coins[6],
            charlie_peter["block_number"],
            charlie_peter["tx"],
            charlie_peter["proof"],
            charlie_peter["signature"],
            peter_addr
        )
        # Cannot challenge with later spend tx!

    # oscar challenges
    helpers.events.challenge_between(
        deployed_contracts.plasma_instance,
        coins[6],
        bob_oscar["block_number"],
        bob_oscar["tx"],
        bob_oscar["proof"],
        bob_oscar["signature"],
        oscar_addr
    )
    # oscar challenges successfully


def test_failing_challenge_5(setup_participate):
    '''
        Cannot challenge exit with an earlier spend
            bob sends coin to oscar
            bob sends coin to charlie
            charlie sends coin to peter
            alice challenges but fails due to providing earlier spend
    '''
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address
    charlie_addr = accounts[4].address

    previous_block = 0
    alice_alice = helpers.utils.generate_tx(coins[7], previous_block, COIN_DENOMINATION, alice_addr, alice_addr)

    # alice sends coin to bob
    previous_block = deployed_contracts.plasma_instance.functions.getPlasmaCoin(coins[0]).call()[1]
    alice_bob = helpers.utils.generate_tx(coins[7], previous_block, COIN_DENOMINATION, bob_addr, alice_addr)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[7], alice_bob["tx_hash"], block_height)
    alice_bob["proof"], alice_bob["block_number"] = helpers.utils.generate_block(*args)

    # bob sends coin to oscar
    bob_oscar = helpers.utils.generate_tx(
        coins[7],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        oscar_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[7], bob_oscar["tx_hash"], block_height)
    bob_oscar["proof"], bob_oscar["block_number"] = helpers.utils.generate_block(*args)

    # bob sends coin to charlie / charlie is a address owned by bob too.
    bob_charlie = helpers.utils.generate_tx(
        coins[7],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        charlie_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[7], bob_charlie["tx_hash"], block_height)
    bob_charlie["proof"], bob_charlie["block_number"] = helpers.utils.generate_block(*args)

    # bob sends coin to charlie / charlie is a address owned by bob too.
    charlie_peter = helpers.utils.generate_tx(
        coins[7],
        bob_charlie["block_number"],
        COIN_DENOMINATION,
        charlie_addr,
        charlie_addr)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[7], charlie_peter["tx_hash"], block_height)
    charlie_peter["proof"], charlie_peter["block_number"] = helpers.utils.generate_block(*args)

    # charlie starts exit.
    events.start_exit(
        deployed_contracts.plasma_instance,
        coins[7],
        alice_bob["tx"],
        bob_charlie["tx"],
        alice_bob["proof"],
        bob_charlie["proof"],
        bob_charlie["signature"],
        [alice_bob["block_number"], bob_charlie["block_number"]],
        charlie_addr
    )

    # alice challenges charlie
    with pytest.raises(Exception):
        helpers.events.challenge_between(
            deployed_contracts.plasma_instance,
            coins[7],
            alice_bob["block_number"],
            alice_bob["tx"],
            alice_bob["proof"],
            alice_bob["signature"],
            alice_addr
        )
        # Cannot challenge exit with an earlier spend

    # charlie finishes exit.
    events.finish_exit(deployed_contracts, coins[7], charlie_addr)


def test_double_spend(setup_participate):
    '''
        Double spend after many tx
            alice legitimately sends coin to bob
            bob legitimately sends coin to oscar
            oscar legitimately sends coin to charlie
            charlie legitimately sends coin to peter
            bob double spends coin by sending it to dylan
    '''
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address
    charlie_addr = accounts[4].address
    peter_addr = accounts[5].address
    dylan_addr = accounts[6].address

    previous_block = 0
    alice_alice = helpers.utils.generate_tx(coins[8], previous_block, COIN_DENOMINATION, alice_addr, alice_addr)

    # alice sends coin to bob
    previous_block = deployed_contracts.plasma_instance.functions.getPlasmaCoin(coins[8]).call()[1]
    args = (coins[8], previous_block, COIN_DENOMINATION, bob_addr, alice_addr)
    alice_bob = helpers.utils.generate_tx(*args)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[8], alice_bob["tx_hash"], block_height)
    alice_bob["proof"], alice_bob["block_number"] = helpers.utils.generate_block(*args)

    # bob sends coin to oscar
    bob_oscar = helpers.utils.generate_tx(
        coins[8],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        oscar_addr,
        bob_addr
    )
    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[8], bob_oscar["tx_hash"], block_height)
    bob_oscar["proof"], bob_oscar["block_number"] = helpers.utils.generate_block(*args)

    # oscar to charlie transaction
    oscar_charlie = helpers.utils.generate_tx(
        coins[8],
        bob_oscar["block_number"],
        COIN_DENOMINATION,
        charlie_addr,
        oscar_addr
    )

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[8], oscar_charlie["tx_hash"], block_height)
    oscar_charlie["proof"], oscar_charlie["block_number"] = helpers.utils.generate_block(*args)

    charlie_peter = helpers.utils.generate_tx(
        coins[8],
        oscar_charlie["block_number"],
        COIN_DENOMINATION,
        peter_addr,
        charlie_addr
    )

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[8], charlie_peter["tx_hash"], block_height)
    charlie_peter["proof"], charlie_peter["block_number"] = helpers.utils.generate_block(*args)

    # double spend | bob to dylan
    bob_dylan = helpers.utils.generate_tx(
        coins[8],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        dylan_addr,
        bob_addr
    )

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[8], bob_dylan["tx_hash"], block_height)
    bob_dylan["proof"], bob_dylan["block_number"] = helpers.utils.generate_block(*args)

    # dylan starts exit
    events.start_exit(
        deployed_contracts.plasma_instance,
        coins[8],
        alice_bob["tx"],
        bob_dylan["tx"],
        alice_bob["proof"],
        bob_dylan["proof"],
        bob_dylan["signature"],
        [alice_bob["block_number"], bob_dylan["block_number"]],
        dylan_addr
    )

    # oscar challenges successfully
    helpers.events.challenge_between(
        deployed_contracts.plasma_instance,
        coins[8],
        bob_oscar["block_number"],
        bob_oscar["tx"],
        bob_oscar["proof"],
        bob_oscar["signature"],
        oscar_addr
    )
