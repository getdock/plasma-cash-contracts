import pytest

from fixtures.const import COIN_DENOMINATION
from helpers import fetcher, generate, exit, challenges


def test_owned_coin(setup_participate):
    """Assert the coins returned by participate are created as they should."""
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    alice_coins = fetcher.owned_coins(deployed_contracts.erc721_instance, alice_addr)
    assert coins == alice_coins


def test_challenge_after1(setup_participate):
    """
    Challenge After #1

    ___Scenario :
        bob tries to challenge an Exit that doesnt exist...', 'blue')

    """
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address

    # alice deposit transaction
    alice_alice = generate.tx(coins[0], 0, COIN_DENOMINATION, alice_addr, alice_addr)

    # alice sends coin to bob
    alice_bob = generate.tx(coins[0], 1, COIN_DENOMINATION, bob_addr, alice_addr)

    # plasma block is generated and submited to mainnet
    alice_bob["proof"], alice_bob["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[0], alice_bob["tx_hash"], 1000)

    with pytest.raises(Exception):
        # bob tries to challenge a non-exiting coin.
        challenges.challenge_after(
            deployed_contracts.plasma_instance,
            coins[0],
            alice_bob["block_number"],
            alice_bob["tx"],
            alice_bob["proof"],
            alice_bob["signature"],
            bob_addr
        )
        # he fails to challenge a non-exiting coin


def test_challenge_after2(setup_participate):
    """
    Challenge After #2

    ___Scenario : oscar tries to a exit a spent coin...

        alice legitimately sends coin to bob
        bob sends coin to oscar
        oscar sends coin to charlie
        oscar tries to exit but charlie challenges him and wins.
    """

    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address
    charlie_addr = accounts[4].address

    # alice deposit transaction
    alice_alice = generate.tx(coins[1], 0, COIN_DENOMINATION, alice_addr, alice_addr)

    # alice sends coin to bob
    alice_bob = generate.tx(coins[1], 2, COIN_DENOMINATION, bob_addr, alice_addr)

    # plasma block is generated and submited to mainnet
    alice_bob["proof"], alice_bob["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[1], alice_bob["tx_hash"], 2000)

    # bob sends coin to oscar
    bob_oscar = generate.tx(
        coins[1],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        oscar_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    bob_oscar["proof"], bob_oscar["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[1], bob_oscar["tx_hash"], 3000)

    # oscar sends coin to charlie
    oscar_charlie = generate.tx(
        coins[1],
        bob_oscar["block_number"],
        COIN_DENOMINATION,
        charlie_addr,
        oscar_addr)

    # plasma block is generated and submited to mainnet
    oscar_charlie["proof"], oscar_charlie["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[1], oscar_charlie["tx_hash"], 4000)

    # oscar starts exit with a coin he has sent to charlie
    exit.start_exit(
        deployed_contracts.plasma_instance,
        coins[1],
        alice_bob["tx"],
        bob_oscar["tx"],
        alice_bob["proof"],
        bob_oscar["proof"],
        bob_oscar["signature"],
        [alice_bob["block_number"], bob_oscar["block_number"]],
        oscar_addr
    )

    # charlie challenges the exit
    challenges.challenge_after(
        deployed_contracts.plasma_instance,
        coins[1],
        oscar_charlie["block_number"],
        oscar_charlie["tx"],
        oscar_charlie["proof"],
        oscar_charlie["signature"],
        charlie_addr
    )
    # charlie challenges successfully...


def test_challenge_after3(setup_participate):
    """
    Challenge After #3

    ___Scenario:
        Same as above but with invalid signature provided...
        Thus oscar can exit a double spent coin.
    """
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address
    charlie_addr = accounts[4].address

    # alice deposit transaction
    alice_alice = generate.tx(coins[2], 0, COIN_DENOMINATION, alice_addr, alice_addr)

    # alice sends coin to bob
    alice_bob = generate.tx(coins[2], 3, COIN_DENOMINATION, bob_addr, alice_addr)

    # plasma block is generated and submited to mainnet
    alice_bob["proof"], alice_bob["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[2], alice_bob["tx_hash"], 5000)

    # bob sends coin to oscar
    bob_oscar = generate.tx(
        coins[2],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        oscar_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    bob_oscar["proof"], bob_oscar["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[2], bob_oscar["tx_hash"], 6000)

    # invalid signature : coins[2], bob_oscar["block_number"], COIN_DENOMINATION, charlie_addr,
    # --> charlie <-- has to be oscar
    oscar_charlie = generate.tx(
        coins[2],
        bob_oscar["block_number"],
        COIN_DENOMINATION,
        charlie_addr,
        charlie_addr)

    # plasma block is generated and submited to mainnet
    oscar_charlie["proof"], oscar_charlie["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[2], oscar_charlie["tx_hash"], 7000)

    # oscar starts exit...
    exit.start_exit(
        deployed_contracts.plasma_instance,
        coins[2],
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
        challenges.challenge_after(
            deployed_contracts.plasma_instance,
            coins[2],
            oscar_charlie["block_number"],
            oscar_charlie["tx"],
            oscar_charlie["proof"],
            oscar_charlie["signature"],
            charlie_addr
        )

    # oscar finishes exit
    exit.finish_exit(deployed_contracts, coins[2], oscar_addr)


def test_challenge_after4(setup_participate):
    """
    Challenge After #4

    ___Scenario:
        Same as above but with invalid merkle proof provided...
        Thus oscar can exit a double sped coin.
    """
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address
    charlie_addr = accounts[4].address

    # alice deposit transaction
    alice_alice = generate.tx(coins[3], 0, COIN_DENOMINATION, alice_addr, alice_addr)

    # alice sends coin to bob
    alice_bob = generate.tx(coins[3], 4, COIN_DENOMINATION, bob_addr, alice_addr)

    # plasma block is generated and submited to mainnet
    alice_bob["proof"], alice_bob["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[3], alice_bob["tx_hash"], 8000)

    # bob sends coin to oscar
    bob_oscar = generate.tx(
        coins[3],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        oscar_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    bob_oscar["proof"], bob_oscar["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[3], bob_oscar["tx_hash"], 9000)

    # oscar to charlie transaction
    oscar_charlie = generate.tx(
        coins[3],
        bob_oscar["block_number"],
        COIN_DENOMINATION,
        charlie_addr,
        oscar_addr)

    # invalid merkle proof: generate.block(
    # deployed_contracts.plasma_instance, plasma_instance, -->coins[1]<-- it has to be coins[3],
# oscar_charlie["tx_hash"], 10000)
    # plasma block is generated and submited to mainnet
    oscar_charlie["proof"], oscar_charlie["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[1], oscar_charlie["tx_hash"], 10000)

    # oscar starts exit...
    exit.start_exit(
        deployed_contracts.plasma_instance,
        coins[3],
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
        challenges.challenge_after(
            deployed_contracts.plasma_instance,
            coins[3],
            oscar_charlie["block_number"],
            oscar_charlie["tx"],
            oscar_charlie["proof"],
            oscar_charlie["signature"],
            charlie_addr
        )
        # Invalid merkle proof provided!

    # oscar finishes exit
    exit.finish_exit(deployed_contracts, coins[3], oscar_addr)


def test_challenge_after5(setup_participate):
    """
    Challenge After #5

    ___Scenario:
        Same as above but with invalid tx provided...
        Thus oscar can exit a double spend coin.
    """
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address
    charlie_addr = accounts[4].address

    # alice deposit transaction
    alice_alice = generate.tx(coins[4], 0, COIN_DENOMINATION, alice_addr, alice_addr)

    # alice sends coin to bob
    alice_bob = generate.tx(coins[4], 5, COIN_DENOMINATION, bob_addr, alice_addr)
    # plasma block is generated and submited to mainnet
    alice_bob["proof"], alice_bob["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[4], alice_bob["tx_hash"], 11000)

    # bob sends coin to oscar
    bob_oscar = generate.tx(
        coins[4],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        oscar_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    bob_oscar["proof"], bob_oscar["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[4], bob_oscar["tx_hash"], 12000)

    # oscar sends coin to charlie
    oscar_charlie = generate.tx(
        coins[4],
        bob_oscar["block_number"],
        COIN_DENOMINATION,
        charlie_addr,
        oscar_addr)

    # plasma block is generated and submited to mainnet
    oscar_charlie["proof"], oscar_charlie["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[4], oscar_charlie["tx_hash"], 13000)

    # oscar starts exit...
    exit.start_exit(
        deployed_contracts.plasma_instance,
        coins[4],
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
        challenges.challenge_after(
            deployed_contracts.plasma_instance,
            coins[4],
            oscar_charlie["block_number"],
            bob_oscar["tx"],  # invalid tx provided, it has to be oscar_charlie["tx"]
            oscar_charlie["proof"],
            oscar_charlie["signature"],
            charlie_addr
        )

    # oscar finishes exit
    exit.finish_exit(deployed_contracts, coins[4], oscar_addr)


def test_challenge_after6(setup_participate):
    """
    Challenge After #6

    ___Scenario:
        No one challenges oscar so he can exit a double spend coin.
    """
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address
    charlie_addr = accounts[4].address

    # alice deposit transaction
    alice_alice = generate.tx(coins[5], 0, COIN_DENOMINATION, alice_addr, alice_addr)

    # alice sends coin to bob
    alice_bob = generate.tx(coins[5], 6, COIN_DENOMINATION, bob_addr, alice_addr)

    # plasma block is generated and submited to mainnet
    alice_bob["proof"], alice_bob["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[5], alice_bob["tx_hash"], 14000)

    # bob sends coin to oscar
    bob_oscar = generate.tx(
        coins[5],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        oscar_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    bob_oscar["proof"], bob_oscar["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[5], bob_oscar["tx_hash"], 15000)

    # oscar sends coin to charlie
    oscar_charlie = generate.tx(
        coins[5],
        bob_oscar["block_number"],
        COIN_DENOMINATION,
        charlie_addr,
        oscar_addr)

    # plasma block is generated and submited to mainnet
    oscar_charlie["proof"], oscar_charlie["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[5], oscar_charlie["tx_hash"], 16000)

    # oscar starts exit...
    exit.start_exit(
        deployed_contracts.plasma_instance,
        coins[5],
        alice_bob["tx"],
        bob_oscar["tx"],
        alice_bob["proof"],
        bob_oscar["proof"],
        bob_oscar["signature"],
        [alice_bob["block_number"], bob_oscar["block_number"]],
        oscar_addr,
    )

    # oscar finishes exit
    exit.finish_exit(deployed_contracts, coins[5], oscar_addr)


def test_challenge_after7(setup_participate):
    """
    Challenge After #7

    ___Scenario :
        Cannot challenge with earlier tx...

    """
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address

    # alice deposit transaction
    alice_alice = generate.tx(coins[6], 0, COIN_DENOMINATION, alice_addr, alice_addr)

    # alice sends coin to bob
    alice_bob = generate.tx(coins[6], 7, COIN_DENOMINATION, bob_addr, alice_addr)

    # plasma block is generated and submited to mainnet
    alice_bob["proof"], alice_bob["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[6], alice_bob["tx_hash"], 17000)

    # bob sends coin to oscar
    bob_oscar = generate.tx(
        coins[6],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        oscar_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    bob_oscar["proof"], bob_oscar["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[6], bob_oscar["tx_hash"], 18000)

    # oscar starts exit...
    exit.start_exit(
        deployed_contracts.plasma_instance,
        coins[6],
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
        challenges.challenge_after(
            deployed_contracts.plasma_instance,
            coins[6],
            alice_bob["block_number"],
            alice_bob["tx"],
            alice_bob["proof"],
            alice_bob["signature"],
            bob_addr
        )
        # he fails because he challenged with earlier tx!

    # oscar finishes exit
    exit.finish_exit(deployed_contracts, coins[6], oscar_addr)


def test_challenge_after8(setup_participate):
    """

    Challenge after #8

    ___Scenario :
        Can challenge with an direct spend

    """
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address

    # deposit tx of alice
    alice_alice = generate.tx(coins[7], 0, COIN_DENOMINATION, alice_addr, alice_addr)

    # alice sends coin to bob
    alice_bob = generate.tx(coins[7], 8, COIN_DENOMINATION, bob_addr, alice_addr)

    # plasma block is generated and submited to mainnet
    alice_bob["proof"], alice_bob["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[7], alice_bob["tx_hash"], 19000)

    # bob sends coin to oscar
    bob_oscar = generate.tx(
        coins[7],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        oscar_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    bob_oscar["proof"], bob_oscar["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[7], bob_oscar["tx_hash"], 20000)

    # bob starts exit
    exit.start_exit(
        deployed_contracts.plasma_instance,
        coins[7],
        alice_alice["tx"],
        alice_bob["tx"],
        '0x',
        alice_bob["proof"],
        alice_bob["signature"],
        [8, alice_bob["block_number"]],
        bob_addr
    )

    # oscar challenges bob...
    challenges.challenge_after(
        deployed_contracts.plasma_instance,
        coins[7],
        bob_oscar["block_number"],
        bob_oscar["tx"],
        bob_oscar["proof"],
        bob_oscar["signature"],
        oscar_addr,
    )
    # oscar challenges successfully


def test_challenge_after9(setup_participate):
    """
    Challenge after #9
    ___Scenario : Cannot challenge with non-direct spend
    """
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address
    charlie_addr = accounts[4].address

    # alice deposit transaction
    alice_alice = generate.tx(coins[8], 0, COIN_DENOMINATION, alice_addr, alice_addr)

    # alice sends coin to bob
    alice_bob = generate.tx(coins[8], 9, COIN_DENOMINATION, bob_addr, alice_addr)

    # plasma block is generated and submited to mainnet
    alice_bob["proof"], alice_bob["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[8], alice_bob["tx_hash"], 21000)

    # bob sends coin to oscar
    bob_oscar = generate.tx(
        coins[8],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        oscar_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    bob_oscar["proof"], bob_oscar["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[8], bob_oscar["tx_hash"], 22000)

    # oscar sends coin to charlie
    oscar_charlie = generate.tx(
        coins[8],
        bob_oscar["block_number"],
        COIN_DENOMINATION,
        charlie_addr,
        oscar_addr)

    # plasma block is generated and submited to mainnet
    oscar_charlie["proof"], oscar_charlie["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[8], oscar_charlie["tx_hash"], 23000)

    # bob starts exit
    exit.start_exit(
        deployed_contracts.plasma_instance,
        coins[8],
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
        challenges.challenge_after(
            deployed_contracts,
            coins[8],
            oscar_charlie["block_number"],
            oscar_charlie["tx"],
            oscar_charlie["proof"],
            oscar_charlie["signature"],
            charlie_addr
        )
        # Cannot challenge with non-direct spend.

    # bob finishes exit
    exit.finish_exit(deployed_contracts, coins[8], bob_addr)
