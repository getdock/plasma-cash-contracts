from itertools import count

import pytest

import helpers.events
import helpers.utils
from helpers import events, utils
from helpers.const import COIN_DENOMINATION, DEFAULT_PASSWORD
from helpers.const import W3 as w3

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


def test_exiting_1(setup_participate):
    '''
        Alice participated in plasma and has not done any transaction off-chain
        now she wants to exit due to suspected malicious behavior from validator/operator
        ... or any other ol' reason
    '''
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address

    # Exiting with a deposit transaction.
    token_uid = next(COIN_COUNTER)
    previous_block = 0
    args = (coins[token_uid], previous_block, COIN_DENOMINATION, alice_addr, alice_addr)
    alice_alice = helpers.utils.generate_tx(*args)

    # alice start exit
    events.start_exit(
        deployed_contracts.plasma_instance,
        coins[token_uid],
        '0x',  # prevtx_bytes
        alice_alice["tx"],  # exitingtx_bytes
        '0x',  # prevtx_inclusion_proof
        '0x',  # exitingtx_inclusion_proof
        alice_alice["signature"],  # signature
        [0, 1],  # blocks
        alice_addr  # exiter
    )

    # alice finishes exit
    events.finish_exit(deployed_contracts, coins[token_uid], alice_addr)


def test_exiting_2(setup_participate):
    '''
    '''
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address

    token_uid = next(COIN_COUNTER)
    previous_block = 0
    args = (coins[token_uid], previous_block, COIN_DENOMINATION, alice_addr, alice_addr)
    alice_alice = helpers.utils.generate_tx(*args)

    # alice sends coin to bob
    previous_block = deployed_contracts.plasma_instance.functions.getPlasmaCoin(coins[token_uid]).call()[1]
    args = (coins[token_uid], previous_block, COIN_DENOMINATION, bob_addr, alice_addr)
    alice_bob = utils.generate_tx(*args)

    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[token_uid], alice_bob["tx_hash"], block_height)
    alice_bob["proof"], alice_bob["block_number"] = helpers.utils.generate_block(*args)

    # bob starts exit
    events.start_exit(
        deployed_contracts.plasma_instance,
        coins[token_uid],
        alice_alice["tx"],
        alice_bob["tx"],
        '0x',
        # prevtx_inclusion_proof is 0x0 since prevtx of bob is alice deposit tx
        # which has no merkle proof.
        alice_bob["proof"],
        alice_bob["signature"],
        # 2 is the prevBlock of prevTx | since prevtx is deposit and coins is
        # [1] it means that it is in the block 2 since this coin is the second
        # which was minted.
        [2, alice_bob["block_number"]],
        bob_addr
    )

    # bob finishes exit
    events.finish_exit(deployed_contracts, coins[token_uid], bob_addr)


def test_exiting_3(setup_participate):
    '''
    '''
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address

    # alice deposit transaction
    token_uid = next(COIN_COUNTER)
    previous_block = 0
    alice_alice = utils.generate_tx(coins[token_uid], previous_block, COIN_DENOMINATION, alice_addr, alice_addr)

    # alice sends coin to bob
    previous_block = deployed_contracts.plasma_instance.functions.getPlasmaCoin(coins[token_uid]).call()[1]
    args = (coins[token_uid], previous_block, COIN_DENOMINATION, bob_addr, alice_addr)
    alice_bob = helpers.utils.generate_tx(*args)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[token_uid], alice_bob["tx_hash"], block_height)
    alice_bob["proof"], alice_bob["block_number"] = helpers.utils.generate_block(*args)

    # bob sends coins to oscar
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
        oscar_addr
    )

    # oscar finishes exit
    events.finish_exit(deployed_contracts, coins[token_uid], oscar_addr)


def test_challenge_1(setup_participate):
    '''
        alice legitimately has deposited and owns a coin
        bob in colludes with the operator to pretend she received a coin from alice
        operator includes fake tx in block
        bob transfers coin to oscar and oscar tries to exit
    '''
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address

    # deposit tx of alice / legit
    token_uid = next(COIN_COUNTER)
    previous_block = 0
    args = (coins[token_uid], previous_block, 20, alice_addr, alice_addr)
    alice_alice = helpers.utils.generate_tx(*args)

    # invalid tx...bob pretending she received coin from alice
    previous_block = deployed_contracts.plasma_instance.functions.getPlasmaCoin(coins[token_uid]).call()[1]
    args = (coins[token_uid], previous_block, 20, bob_addr, bob_addr)
    alice_bob = helpers.utils.generate_tx(*args)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[token_uid], alice_bob["tx_hash"], block_height)
    alice_bob["proof"], alice_bob["block_number"] = helpers.utils.generate_block(*args)

    # bob pretending to receive the coin sends it to oscar
    bob_oscar = helpers.utils.generate_tx(
        coins[token_uid],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        oscar_addr,
        bob_addr,
    )

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[token_uid], bob_oscar["tx_hash"], block_height)
    bob_oscar["proof"], bob_oscar["block_number"] = helpers.utils.generate_block(*args)

    # oscar exits
    w3.personal.unlockAccount(oscar_addr, DEFAULT_PASSWORD)
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

    # alice challenges with his deposit/valid tx.
    helpers.events.challenge_before(
        deployed_contracts.plasma_instance,
        coins[token_uid],
        alice_alice["tx"],
        '0x',
        alice_alice["signature"],
        4,
        alice_addr,
        # since it is a deposit tx from alice the tx_hash is the keccak256 of
        # token uid.
        w3.soliditySha3(['uint64'], [coins[token_uid]])
    )

    helpers.events.finish_challenge_exit(deployed_contracts.plasma_instance, coins[token_uid], alice_addr)
    coin_struct = deployed_contracts.plasma_instance.functions.getPlasmaCoin(coins[token_uid]).call()
    assert coin_struct[4] == 0


def test_challenge_2(setup_participate):
    '''
        alice legitimately has deposited and owns a coin...
        alice legitimately sends the coins off-chain to bob...
        oscar in colaboration with operator pretends she received the coin from bob and includes it in a block...
        oscar sends coin to charlie...
    '''
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address
    charlie_addr = accounts[4].address

    # deposit tx of alice / legit
    token_uid = next(COIN_COUNTER)
    previous_block = 0
    args = (coins[token_uid], previous_block, 20, alice_addr, alice_addr)
    alice_alice = helpers.utils.generate_tx(*args)

    # alice sends coin to bob
    previous_block = deployed_contracts.plasma_instance.functions.getPlasmaCoin(coins[token_uid]).call()[1]
    args = (coins[token_uid], previous_block, 20, bob_addr, alice_addr)
    alice_bob = helpers.utils.generate_tx(*args)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[token_uid], alice_bob["tx_hash"], block_height)
    alice_bob["proof"], alice_bob["block_number"] = helpers.utils.generate_block(*args)

    # oscar pretending to receive the coin from bob sends it to charlie
    bob_oscar = helpers.utils.generate_tx(
        coins[token_uid],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        oscar_addr,
        oscar_addr)

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

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[token_uid], oscar_charlie["tx_hash"], block_height)
    oscar_charlie["proof"], oscar_charlie["block_number"] = helpers.utils.generate_block(*args)

    # charlie starts exit
    events.start_exit(
        deployed_contracts.plasma_instance,
        coins[token_uid],
        bob_oscar["tx"],
        oscar_charlie["tx"],
        bob_oscar["proof"],
        oscar_charlie["proof"],
        oscar_charlie["signature"],
        [bob_oscar["block_number"], oscar_charlie["block_number"]],
        charlie_addr
    )

    # bob challenges with valid tx.
    helpers.events.challenge_before(
        deployed_contracts.plasma_instance,
        coins[token_uid],
        alice_bob["tx"],
        alice_bob["proof"],
        alice_bob["signature"],
        6000,
        bob_addr,
        alice_bob["tx_hash"]
    )

    # There is no response from charlie...
    # bob finishes exit to win the bond...
    helpers.events.finish_challenge_exit(deployed_contracts.plasma_instance, coins[token_uid], bob_addr)
    coin_struct = deployed_contracts.plasma_instance.functions.getPlasmaCoin(coins[token_uid]).call()
    assert coin_struct[4] == 0


def test_challenge_3(setup_participate):
    '''
        alice legitimately sends a coin he owns to bob...
        bob legitimately sends the received coin to oscar...
        charlie in colaboration with operator pretends he received the coin from oscar and includes it in a block...
        charlie sends coin to peter...
    '''
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address
    charlie_addr = accounts[4].address
    peter_addr = accounts[5].address

    # alice sends coin to bob
    token_uid = next(COIN_COUNTER)
    previous_block = previous_block = deployed_contracts.plasma_instance.functions.getPlasmaCoin(coins[token_uid]).call()[
        1]
    args = (coins[token_uid], previous_block, 20, bob_addr, alice_addr)
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

    # charlie pretens to receive coin from oscar
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

    # charlie sends coin to peter
    charlie_peter = helpers.utils.generate_tx(
        coins[token_uid],
        oscar_charlie["block_number"],
        COIN_DENOMINATION,
        peter_addr,
        charlie_addr)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[token_uid], charlie_peter["tx_hash"], block_height)
    charlie_peter["proof"], charlie_peter["block_number"] = helpers.utils.generate_block(*args)

    # peter starts exit
    events.start_exit(
        deployed_contracts.plasma_instance,
        coins[token_uid],
        oscar_charlie["tx"],
        charlie_peter["tx"],
        oscar_charlie["proof"],
        charlie_peter["proof"],
        charlie_peter["signature"],
        [oscar_charlie["block_number"], charlie_peter["block_number"]],
        peter_addr
    )

    # oscar challenges
    helpers.events.challenge_before(
        deployed_contracts.plasma_instance,
        coins[token_uid],
        bob_oscar["tx"],
        bob_oscar["proof"],
        bob_oscar["signature"],
        10000,
        oscar_addr,
        bob_oscar["tx_hash"]
    )
    """
    There is no response from peter...
    oscar finishes exit to win the bond...
    """
    helpers.events.finish_challenge_exit(deployed_contracts.plasma_instance, coins[token_uid], oscar_addr)
    coin_struct = deployed_contracts.plasma_instance.functions.getPlasmaCoin(coins[token_uid]).call()
    assert coin_struct[4] == 0


def test_challenge_4(setup_participate):
    '''
        alice legitimately sends a coin he owns to bob...
        bob legitimately sends the received coin to oscar...
        charlie in colaboration with operator pretends he received the coin from oscar and includes it in a block...
        charlie sends coin to peter...
        peter starts exit...
        oscar challenges peter tx...
        peter tries to respond oscars valid challenge...
    '''
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address
    charlie_addr = accounts[4].address
    peter_addr = accounts[5].address

    # alice sends coin to bob
    token_uid = next(COIN_COUNTER)
    previous_block = deployed_contracts.plasma_instance.functions.getPlasmaCoin(coins[token_uid]).call()[1]
    args = (coins[token_uid], previous_block, 20, bob_addr, alice_addr)
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

    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[token_uid], bob_oscar["tx_hash"], block_height)
    bob_oscar["proof"], bob_oscar["block_number"] = helpers.utils.generate_block(*args)

    # charlie pretens to receive coin from oscar
    oscar_charlie = helpers.utils.generate_tx(
        coins[token_uid],
        bob_oscar["block_number"],
        COIN_DENOMINATION,
        charlie_addr,
        charlie_addr)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[token_uid], oscar_charlie["tx_hash"], block_height)
    oscar_charlie["proof"], oscar_charlie["block_number"] = helpers.utils.generate_block(*args)

    # charlie sends coin to peter
    charlie_peter = helpers.utils.generate_tx(
        coins[token_uid],
        oscar_charlie["block_number"],
        COIN_DENOMINATION,
        peter_addr,
        charlie_addr)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[token_uid], charlie_peter["tx_hash"], block_height)
    charlie_peter["proof"], charlie_peter["block_number"] = helpers.utils.generate_block(*args)

    # peter exits
    events.start_exit(
        deployed_contracts.plasma_instance,
        coins[token_uid],
        oscar_charlie["tx"],
        charlie_peter["tx"],
        oscar_charlie["proof"],
        charlie_peter["proof"],
        charlie_peter["signature"],
        [oscar_charlie["block_number"], charlie_peter["block_number"]],
        peter_addr
    )

    # oscar challenges
    helpers.events.challenge_before(
        deployed_contracts.plasma_instance,
        coins[token_uid],
        bob_oscar["tx"],
        bob_oscar["proof"],
        bob_oscar["signature"],
        14000,
        oscar_addr,
        bob_oscar["tx_hash"]
    )

    # peter tries to respond the valid challenge...
    with pytest.raises(Exception):
        helpers.events.respond_challenge_before(
            deployed_contracts.plasma_instance,
            coins[token_uid],
            bob_oscar["tx_hash"],
            charlie_peter["block_number"],
            charlie_peter["tx"],
            charlie_peter["proof"],
            charlie_peter["signature"],
            peter_addr
        )
        # peter respond fails...

    # oscar finishes exit to win the bond...
    helpers.events.finish_challenge_exit(deployed_contracts.plasma_instance, coins[token_uid], oscar_addr)
    coin_struct = deployed_contracts.plasma_instance.functions.getPlasmaCoin(coins[token_uid]).call()
    assert coin_struct[4] == 0


def test_challenge_5(setup_participate):
    '''
        A group of participants gathered together with operator try to exit alice legitimately owned coin...
        bob in colaboration with operator pretends he received the coin from alice and includes it in a block...
        bob sends coin to oscar...
        oscar sends coin to charlie...
        charlie sends coin to peter...
        peter start exit...
        One of the group members challenges peter...
        alice also challenges with her legit deposit transaction...
    '''
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address
    charlie_addr = accounts[4].address
    peter_addr = accounts[5].address

    # deposit tx of alice / legit
    token_uid = next(COIN_COUNTER)
    previous_block = 0
    args = (coins[token_uid], previous_block, COIN_DENOMINATION, alice_addr, alice_addr)
    alice_alice = helpers.utils.generate_tx(*args)

    # Loid pretends she received coin from alice
    previous_block = deployed_contracts.plasma_instance.functions.getPlasmaCoin(coins[token_uid]).call()[1]
    args = (coins[token_uid], previous_block, COIN_DENOMINATION, bob_addr, bob_addr)
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

    # charlie sends coin to peter
    charlie_peter = helpers.utils.generate_tx(
        coins[token_uid],
        oscar_charlie["block_number"],
        COIN_DENOMINATION,
        peter_addr,
        charlie_addr)

    # plasma block is generated and submited to mainnet
    block_height = next(BLOCK_COUNTER)
    args = (deployed_contracts.plasma_instance, coins[token_uid], charlie_peter["tx_hash"], block_height)
    charlie_peter["proof"], charlie_peter["block_number"] = helpers.utils.generate_block(*args)

    # peter starts exits
    events.start_exit(
        deployed_contracts.plasma_instance,
        coins[token_uid],
        oscar_charlie["tx"],
        charlie_peter["tx"],
        oscar_charlie["proof"],
        charlie_peter["proof"],
        charlie_peter["signature"],
        [oscar_charlie["block_number"], charlie_peter["block_number"]],
        peter_addr
    )

    # oscar challenges
    helpers.events.challenge_before(
        deployed_contracts.plasma_instance,
        coins[token_uid],
        bob_oscar["tx"],
        bob_oscar["proof"],
        bob_oscar["signature"],
        18000,
        oscar_addr,
        bob_oscar["tx_hash"]
    )

    # alice also challenges with her valid deposit tx
    helpers.events.challenge_before(
        deployed_contracts.plasma_instance,
        coins[token_uid],
        alice_alice["tx"],
        '0x',
        alice_alice["signature"],
        8,
        alice_addr,
        w3.soliditySha3(['uint64'], [coins[token_uid]])
    )

    # charlie tries to respond challenges / can respond to first challenge but
    # not to alice since it is the valid one.
    helpers.events.respond_challenge_before(
        deployed_contracts.plasma_instance,
        coins[token_uid],
        bob_oscar["tx_hash"],
        oscar_charlie["block_number"],
        oscar_charlie["tx"],
        oscar_charlie["proof"],
        oscar_charlie["signature"],
        charlie_addr
    )

    # alice finishes exit since she owns the coin
    helpers.events.finish_challenge_exit(deployed_contracts.plasma_instance, coins[token_uid], alice_addr)
    coin_struct = deployed_contracts.plasma_instance.functions.getPlasmaCoin(coins[token_uid]).call()
    assert coin_struct[4] == 0
