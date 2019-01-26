import pytest

from fixtures.const import COIN_DENOMINATION, DEFAULT_PASSWORD, w3
from helpers import instances, fetcher, generate, exit, challenges


def test_owned_coin(setup_participate):
    """Assert the coins returned by participate are created as they should."""
    accounts, coins = setup_participate
    alice_addr = accounts[1].address
    alice_coins = fetcher.owned_coins(alice_addr)
    assert coins == alice_coins


def test_exiting_1(setup_participate):
    '''

    Alice has participated in plasma and she has not done any transaction off-chain and
    now she wants to exit due to snifing a malicious behavior from validator/operator or just
    wants to exit for whatever reason.
    '''
    accounts, coins = setup_participate
    alice_addr = accounts[1].address

    # Exiting with a deposit transaction.
    alice_alice = generate.tx(coins[0], 0, COIN_DENOMINATION, alice_addr, alice_addr)

    # alice start exit
    exit.start_exit(
        coins[0],
        '0x',  # prevtx_bytes
        alice_alice["tx"],  # exitingtx_bytes
        '0x',  # prevtx_inclusion_proof
        '0x',  # exitingtx_inclusion_proof
        alice_alice["signature"],  # signature
        [0, 1],  # blocks
        alice_addr  # exiter
    )

    # alice finishes exit
    exit.finish_exit(coins[0], alice_addr)


def test_exiting_2(setup_participate):
    accounts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    # Exiting with prevTx as deposit
    alice_alice = generate.tx(coins[1], 0, COIN_DENOMINATION, alice_addr, alice_addr)

    # alice sends coin to bob
    alice_bob = generate.tx(coins[1], 2, COIN_DENOMINATION, bob_addr, alice_addr)
    # plasma block is generated and submited to mainnet
    alice_bob["proof"], alice_bob["block_number"] = generate.block(
        coins[1], alice_bob["tx_hash"], 1000)

    # bob starts exit
    exit.start_exit(
        coins[1],
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
    exit.finish_exit(coins[1], bob_addr)


def test_exiting_3(setup_participate):
    accounts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address

    # alice deposit transaction
    alice_alice = generate.tx(coins[2], 0, COIN_DENOMINATION, alice_addr, alice_addr)

    # alice sends coin to bob
    alice_bob = generate.tx(coins[2], 3, COIN_DENOMINATION, bob_addr, alice_addr)

    # plasma block is generated and submited to mainnet
    alice_bob["proof"], alice_bob["block_number"] = generate.block(
        coins[2], alice_bob["tx_hash"], 2000)

    # bob sends coins to oscar
    bob_oscar = generate.tx(
        coins[2],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        oscar_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    bob_oscar["proof"], bob_oscar["block_number"] = generate.block(
        coins[2], bob_oscar["tx_hash"], 3000)

    # oscar starts exit
    exit.start_exit(
        coins[2],
        alice_bob["tx"],
        bob_oscar["tx"],
        alice_bob["proof"],
        bob_oscar["proof"],
        bob_oscar["signature"],
        [alice_bob["block_number"], bob_oscar["block_number"]],
        oscar_addr
    )

    # oscar finishes exit
    exit.finish_exit(coins[2], oscar_addr)


def test_challenge_1(setup_participate):
    '''
    ___Scenario :
        alice legitimately has deposited and owns a coin...
        bob in colaboration with operator pretends she received the coin from alice and includes it in a block...
        bob transfers coin to oscar and oscar tries to exit...
    '''
    accounts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address

    # deposit tx of alice / legit
    alice_alice = generate.tx(coins[3], 0, 20, alice_addr, alice_addr)

    # invalid tx...bob pretending she received coin from alice
    alice_bob = generate.tx(coins[3], 3, 20, bob_addr, bob_addr)

    # plasma block is generated and submited to mainnet
    alice_bob["proof"], alice_bob["block_number"] = generate.block(
        coins[3], alice_bob["tx_hash"], 4000)

    # bob pretending to receive the coin sends it to oscar
    bob_oscar = generate.tx(
        coins[3],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        oscar_addr,
        bob_addr,
    )

    # plasma block is generated and submited to mainnet
    bob_oscar["proof"], bob_oscar["block_number"] = generate.block(
        coins[3], bob_oscar["tx_hash"], 5000)

    # oscar exits
    w3.personal.unlockAccount(oscar_addr, DEFAULT_PASSWORD)
    exit.start_exit(
        coins[3],
        alice_bob["tx"],
        bob_oscar["tx"],
        alice_bob["proof"],
        bob_oscar["proof"],
        bob_oscar["signature"],
        [alice_bob["block_number"], bob_oscar["block_number"]],
        oscar_addr
    )

    # alice challenges with his deposit/valid tx.
    challenges.challenge_before(
        coins[3],
        alice_alice["tx"],
        '0x',
        alice_alice["signature"],
        4,
        alice_addr,
        # since it is a deposit tx from alice the tx_hash is the keccak256 of
        # token uid.
        w3.soliditySha3(['uint64'], [coins[3]])
    )

    challenges.finishChallengeExit(coins[3], alice_addr)
    coinObj = instances.plasma_instance.functions.getPlasmaCoin(coins[3]).call()
    assert coinObj[4] == 0


def test_challenge_2(setup_participate):
    '''
    ___Scenario :

        alice legitimately has deposited and owns a coin...
        alice legitimately sends the coins off-chain to bob...
        oscar in colaboration with operator pretends she received the coin from bob and includes it in a block...
        oscar sends coin to charlie...

    '''
    accounts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address
    charlie_addr = accounts[4].address

    # deposit tx of alice / legit
    alice_alice = generate.tx(coins[4], 0, 20, alice_addr, alice_addr)

    # alice sends coin to bob
    alice_bob = generate.tx(coins[4], 5, 20, bob_addr, alice_addr)

    # plasma block is generated and submited to mainnet
    alice_bob["proof"], alice_bob["block_number"] = generate.block(
        coins[4], alice_bob["tx_hash"], 6000)

    # oscar pretending to receive the coin from bob sends it to charlie
    bob_oscar = generate.tx(
        coins[4],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        oscar_addr,
        oscar_addr)

    # plasma block is generated and submited to mainnet
    bob_oscar["proof"], bob_oscar["block_number"] = generate.block(
        coins[4], bob_oscar["tx_hash"], 7000)

    # oscar to charlie transction
    oscar_charlie = generate.tx(
        coins[4],
        bob_oscar["block_number"],
        COIN_DENOMINATION,
        charlie_addr,
        oscar_addr)

    # plasma block is generated and submited to mainnet
    oscar_charlie["proof"], oscar_charlie["block_number"] = generate.block(
        coins[4], oscar_charlie["tx_hash"], 8000)

    # charlie starts exit
    exit.start_exit(
        coins[4],
        bob_oscar["tx"],
        oscar_charlie["tx"],
        bob_oscar["proof"],
        oscar_charlie["proof"],
        oscar_charlie["signature"],
        [bob_oscar["block_number"], oscar_charlie["block_number"]],
        charlie_addr
    )

    # bob challenges with valid tx.
    challenges.challenge_before(
        coins[4],
        alice_bob["tx"],
        alice_bob["proof"],
        alice_bob["signature"],
        6000,
        bob_addr,
        alice_bob["tx_hash"]
    )

    # There is no response from charlie...
    # bob finishes exit to win the bond...
    challenges.finishChallengeExit(coins[4], bob_addr)
    coinObj = instances.plasma_instance.functions.getPlasmaCoin(coins[4]).call()
    assert coinObj[4] == 0


def test_challenge_3(setup_participate):
    '''
    ___Scenario :

        alice legitimately sends a coin he owns to bob...
        bob legitimately sends the received coin to oscar...
        charlie in colaboration with operator pretends he received the coin from oscar and includes it in a block...
        charlie sends coin to peter...
    '''
    accounts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address
    charlie_addr = accounts[4].address
    peter_addr = accounts[5].address

    # alice sends coin to bob
    alice_bob = generate.tx(coins[5], 6, 20, bob_addr, alice_addr)
    # plasma block is generated and submited to mainnet
    alice_bob["proof"], alice_bob["block_number"] = generate.block(
        coins[5], alice_bob["tx_hash"], 9000)

    # bob sends coin to oscar
    bob_oscar = generate.tx(
        coins[5],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        oscar_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    bob_oscar["proof"], bob_oscar["block_number"] = generate.block(
        coins[5], bob_oscar["tx_hash"], 10000)

    # charlie pretens to receive coin from oscar
    oscar_charlie = generate.tx(
        coins[5],
        bob_oscar["block_number"],
        COIN_DENOMINATION,
        charlie_addr,
        charlie_addr)

    # plasma block is generated and submited to mainnet
    oscar_charlie["proof"], oscar_charlie["block_number"] = generate.block(
        coins[5], oscar_charlie["tx_hash"], 11000)

    # charlie sends coin to peter
    charlie_peter = generate.tx(
        coins[5],
        oscar_charlie["block_number"],
        COIN_DENOMINATION,
        peter_addr,
        charlie_addr)

    # plasma block is generated and submited to mainnet
    charlie_peter["proof"], charlie_peter["block_number"] = generate.block(
        coins[5], charlie_peter["tx_hash"], 12000)

    # peter starts exit
    exit.start_exit(
        coins[5],
        oscar_charlie["tx"],
        charlie_peter["tx"],
        oscar_charlie["proof"],
        charlie_peter["proof"],
        charlie_peter["signature"],
        [oscar_charlie["block_number"], charlie_peter["block_number"]],
        peter_addr
    )

    # oscar challenges
    challenges.challenge_before(
        coins[5],
        bob_oscar["tx"],
        bob_oscar["proof"],
        bob_oscar["signature"],
        10000,
        oscar_addr,
        bob_oscar["tx_hash"]
    )
    '''
    There is no response from peter...
    oscar finishes exit to win the bond...
    '''
    challenges.finishChallengeExit(coins[5], oscar_addr)
    coinObj = instances.plasma_instance.functions.getPlasmaCoin(coins[5]).call()
    assert coinObj[4] == 0


def test_challenge_4(setup_participate):
    '''
    ___Scenario :

        alice legitimately sends a coin he owns to bob...
        bob legitimately sends the received coin to oscar...
        charlie in colaboration with operator pretends he received the coin from oscar and includes it in a block...
        charlie sends coin to peter...
        peter starts exit...
        oscar challenges peter tx...
        peter tries to respond oscars valid challenge...

    '''
    accounts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address
    charlie_addr = accounts[4].address
    peter_addr = accounts[5].address

    # alice sends coin to bob
    alice_bob = generate.tx(coins[6], 7, 20, bob_addr, alice_addr)
    # plasma block is generated and submited to mainnet
    alice_bob["proof"], alice_bob["block_number"] = generate.block(
        coins[6], alice_bob["tx_hash"], 13000)

    # bob sends coin to oscar
    bob_oscar = generate.tx(
        coins[6],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        oscar_addr,
        bob_addr)
    # plasma block is generated and submited to mainnet
    bob_oscar["proof"], bob_oscar["block_number"] = generate.block(
        coins[6], bob_oscar["tx_hash"], 14000)

    # charlie pretens to receive coin from oscar
    oscar_charlie = generate.tx(
        coins[6],
        bob_oscar["block_number"],
        COIN_DENOMINATION,
        charlie_addr,
        charlie_addr)

    # plasma block is generated and submited to mainnet
    oscar_charlie["proof"], oscar_charlie["block_number"] = generate.block(
        coins[6], oscar_charlie["tx_hash"], 15000)

    # charlie sends coin to peter
    charlie_peter = generate.tx(
        coins[6],
        oscar_charlie["block_number"],
        COIN_DENOMINATION,
        peter_addr,
        charlie_addr)

    # plasma block is generated and submited to mainnet
    charlie_peter["proof"], charlie_peter["block_number"] = generate.block(
        coins[6], charlie_peter["tx_hash"], 16000)

    # peter exits
    exit.start_exit(
        coins[6],
        oscar_charlie["tx"],
        charlie_peter["tx"],
        oscar_charlie["proof"],
        charlie_peter["proof"],
        charlie_peter["signature"],
        [oscar_charlie["block_number"], charlie_peter["block_number"]],
        peter_addr
    )

    # oscar challenges
    challenges.challenge_before(
        coins[6],
        bob_oscar["tx"],
        bob_oscar["proof"],
        bob_oscar["signature"],
        14000,
        oscar_addr,
        bob_oscar["tx_hash"]
    )

    # peter tries to respond the valid challenge...
    with pytest.raises(Exception):
        challenges.respondchallenge_before(
            coins[6],
            bob_oscar["tx_hash"],
            charlie_peter["block_number"],
            charlie_peter["tx"],
            charlie_peter["proof"],
            charlie_peter["signature"],
            peter_addr
        )
        # peter respond fails...

    # oscar finishes exit to win the bond...
    challenges.finishChallengeExit(coins[6], oscar_addr)
    coinObj = instances.plasma_instance.functions.getPlasmaCoin(coins[6]).call()
    assert coinObj[4] == 0


def test_challenge_5(setup_participate):
    '''
    ___Scenario :

        A group of participants gathered together with operator try to exit alice legitimately owned coin...
        bob in colaboration with operator pretends he received the coin from alice and includes it in a block...
        bob sends coin to oscar...
        oscar sends coin to charlie...
        charlie sends coin to peter...
        peter start exit...
        One of the group members challenges peter...
        alice also challenges with her legit deposit transaction...

    '''
    accounts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address
    charlie_addr = accounts[4].address
    peter_addr = accounts[5].address

    # deposit tx of alice / legit
    alice_alice = generate.tx(coins[7], 0, COIN_DENOMINATION, alice_addr, alice_addr)

    # Loid pretends she received coin from alice
    alice_bob = generate.tx(coins[7], 8, COIN_DENOMINATION, bob_addr, bob_addr)

    # plasma block is generated and submited to mainnet
    alice_bob["proof"], alice_bob["block_number"] = generate.block(
        coins[7], alice_bob["tx_hash"], 17000)

    # bob sends coin to oscar
    bob_oscar = generate.tx(
        coins[7],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        oscar_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    bob_oscar["proof"], bob_oscar["block_number"] = generate.block(
        coins[7], bob_oscar["tx_hash"], 18000)

    # oscar sends coin to charlie
    oscar_charlie = generate.tx(
        coins[7],
        bob_oscar["block_number"],
        COIN_DENOMINATION,
        charlie_addr,
        oscar_addr)

    # plasma block is generated and submited to mainnet
    oscar_charlie["proof"], oscar_charlie["block_number"] = generate.block(
        coins[7], oscar_charlie["tx_hash"], 19000)

    # charlie sends coin to peter
    charlie_peter = generate.tx(
        coins[7],
        oscar_charlie["block_number"],
        COIN_DENOMINATION,
        peter_addr,
        charlie_addr)

    # plasma block is generated and submited to mainnet
    charlie_peter["proof"], charlie_peter["block_number"] = generate.block(
        coins[7], charlie_peter["tx_hash"], 20000)

    # peter starts exits
    exit.start_exit(
        coins[7],
        oscar_charlie["tx"],
        charlie_peter["tx"],
        oscar_charlie["proof"],
        charlie_peter["proof"],
        charlie_peter["signature"],
        [oscar_charlie["block_number"], charlie_peter["block_number"]],
        peter_addr
    )

    # oscar challenges
    challenges.challenge_before(
        coins[7],
        bob_oscar["tx"],
        bob_oscar["proof"],
        bob_oscar["signature"],
        18000,
        oscar_addr,
        bob_oscar["tx_hash"]
    )

    # alice also challenges with her valid deposit tx
    challenges.challenge_before(
        coins[7],
        alice_alice["tx"],
        '0x',
        alice_alice["signature"],
        8,
        alice_addr,
        w3.soliditySha3(['uint64'], [coins[7]])
    )

    # charlie tries to respond challenges / can respond to first challenge but
    # not to alice since it is the valid one.
    challenges.respondchallenge_before(
        coins[7],
        bob_oscar["tx_hash"],
        oscar_charlie["block_number"],
        oscar_charlie["tx"],
        oscar_charlie["proof"],
        oscar_charlie["signature"],
        charlie_addr
    )

    # alice finishes exit since she owns the coin
    challenges.finishChallengeExit(coins[7], alice_addr)
    coinObj = instances.plasma_instance.functions.getPlasmaCoin(coins[7]).call()
    assert coinObj[4] == 0
