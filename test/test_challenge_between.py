import pytest

from fixtures.const import COIN_DENOMINATION
from helpers import generate, exit, challenges


def test_owned_coin(setup_participate):
    """Assert the coins returned by participate are created as they should."""
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    alice_coins = deployed_contracts.erc721_instance.functions.getOwnedTokens(alice_addr).call()
    assert coins == alice_coins


def test_failing_challenge_1(setup_participate):
    """

    ___Scenario:
        Trying to challenge a Exit that doesnt exist

    """
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address
    charlie_addr = accounts[4].address

    # alice deposit tx.
    alice_alice = generate.tx(coins[0], 0, COIN_DENOMINATION, alice_addr, alice_addr)

    # alice to bob tx.
    alice_bob = generate.tx(coins[0], 1, COIN_DENOMINATION, bob_addr, alice_addr)

    # plasma block is generated and submited to mainnet
    alice_bob["proof"], alice_bob["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[0], alice_bob["tx_hash"], 1000)

    # bob to oscar tx.
    bob_oscar = generate.tx(
        coins[0],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        oscar_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    bob_oscar["proof"], bob_oscar["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[0], bob_oscar["tx_hash"], 2000)

    # bob to charlie tx.
    bob_charlie = generate.tx(
        coins[0],
        bob_oscar["block_number"],
        COIN_DENOMINATION,
        charlie_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    bob_charlie["proof"], bob_charlie["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[0], bob_charlie["tx_hash"], 3000)

    # oscar challenges
    with pytest.raises(Exception):
        challenges.challengeBetween(
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
    """
    ___Scenario : bob tries to do a double spend
                  alice legitimately sends coin to bob
                  bob sends coin to oscar
                  bob sends coin to charlie

    """
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address
    charlie_addr = accounts[4].address
    # alice deposit transaction
    alice_alice = generate.tx(coins[1], 0, COIN_DENOMINATION, alice_addr, alice_addr)

    # alice to bob
    alice_bob = generate.tx(coins[1], 2, COIN_DENOMINATION, bob_addr, alice_addr)

    # plasma block is generated and submited to mainnet
    alice_bob["proof"], alice_bob["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[1], alice_bob["tx_hash"], 4000)

    # bob to oscar
    bob_oscar = generate.tx(
        coins[1],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        oscar_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    bob_oscar["proof"], bob_oscar["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[1], bob_oscar["tx_hash"], 5000)

    # bob to charlie | double spend
    bob_charlie = generate.tx(
        coins[1],
        bob_oscar["block_number"],
        COIN_DENOMINATION,
        charlie_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    bob_charlie["proof"], bob_charlie["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[1], bob_charlie["tx_hash"], 6000)

    # charlie starts exit
    exit.start_exit(
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
    challenges.challengeBetween(
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
    """

    ___Scenario :
        Same as above but with invalid signature

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
        deployed_contracts.plasma_instance, coins[2], alice_bob["tx_hash"], 7000)

    # bob sends coin to oscar
    bob_oscar = generate.tx(
        coins[2],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        oscar_addr,
        alice_addr
    )

    # plasma block is generated and submited to mainnet
    bob_oscar["proof"], bob_oscar["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[2], bob_oscar["tx_hash"], 8000)

    # bob sends coin to charlie.
    bob_charlie = generate.tx(
        coins[2],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        charlie_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    bob_charlie["proof"], bob_charlie["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[2], bob_charlie["tx_hash"], 9000)

    # charlie starts exit
    exit.start_exit(
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
        challenges.challengeBetween(
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
    exit.finish_exit(deployed_contracts, coins[2], charlie_addr)


def test_failing_challenge_3(setup_participate):
    """
    ___Scenario :
        Same as above but with invalid merkle proof provided

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
        deployed_contracts.plasma_instance, coins[3], alice_bob["tx_hash"], 10000)

    # bob sends coin to oscar
    bob_oscar = generate.tx(
        coins[3],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        oscar_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    bob_oscar["proof"], bob_oscar["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[3], bob_oscar["tx_hash"], 11000)

    # bob sends coin to charlie / charlie is a address owned by bob too.
    bob_charlie = generate.tx(
        coins[3],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        charlie_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    bob_charlie["proof"], bob_charlie["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[3], bob_charlie["tx_hash"], 12000)

    # oscar startes exit
    exit.start_exit(
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
        challenges.challengeBetween(
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
    exit.finish_exit(deployed_contracts, coins[3], charlie_addr)


def test_failing_challenge_4(setup_participate):
    """
    ___Scenario :
        Same as above but with invalid tx
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
        deployed_contracts.plasma_instance, coins[4], alice_bob["tx_hash"], 13000)

    # bob sends coin to oscar
    bob_oscar = generate.tx(
        coins[4],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        oscar_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    bob_oscar["proof"], bob_oscar["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[4], bob_oscar["tx_hash"], 14000)

    # bob sends coin to charlie / charlie is a address owned by bob too.
    bob_charlie = generate.tx(
        coins[4],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        charlie_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    bob_charlie['proof'], bob_charlie["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[4], bob_charlie["tx_hash"], 15000)

    # charlie starts exit
    exit.start_exit(
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
        challenges.challengeBetween(
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
    exit.finish_exit(deployed_contracts, coins[4], charlie_addr)


def test_successful_exit1(setup_participate):
    """
    ___Scenario :
        Same as above but no one challenges and maturity period is achived and coin can be finalized

    """
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address
    charlie_addr = accounts[4].address
    # alice deposit tx
    alice_alice = generate.tx(coins[5], 0, COIN_DENOMINATION, alice_addr, alice_addr)

    # alice sends coin to bob
    alice_bob = generate.tx(coins[5], 6, COIN_DENOMINATION, bob_addr, alice_addr)

    # plasma block is generated and submited to mainnet
    alice_bob["proof"], alice_bob["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[5], alice_bob["tx_hash"], 16000)

    # bob sends coin to oscar
    bob_oscar = generate.tx(
        coins[5],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        oscar_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    bob_oscar["proof"], bob_oscar["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[5], bob_oscar["tx_hash"], 17000)

    # bob sends coin to charlie
    bob_charlie = generate.tx(
        coins[5],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        charlie_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    bob_charlie["proof"], bob_charlie["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[5], bob_charlie["tx_hash"], 18000)

    # charlie starts exit
    exit.start_exit(
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
    exit.finish_exit(deployed_contracts, coins[5], charlie_addr)


def test_multiple_challenges(setup_participate):
    """
    ___Scenario : Multiple challenges | Later Spend(invalid), In Between Spend(valid)
                  bob sends coin to oscar
                  bob sends coin to charlie
                  charlie sends coin to peter
                  peter challenges but fails due to providing later spend
                  oscar challenges with valid tx proving the double spend to charlie
    """
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address
    charlie_addr = accounts[4].address
    peter_addr = accounts[5].address

    # alice deposit
    alice_alice = generate.tx(coins[6], 0, COIN_DENOMINATION, alice_addr, alice_addr)

    # alice sends coin to bob
    alice_bob = generate.tx(coins[6], 7, COIN_DENOMINATION, bob_addr, alice_addr)

    # plasma block is generated and submited to mainnet
    alice_bob["proof"], alice_bob["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[6], alice_bob["tx_hash"], 19000)

    # bob sends coin to oscar
    bob_oscar = generate.tx(
        coins[6],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        oscar_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    bob_oscar["proof"], bob_oscar["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[6], bob_oscar["tx_hash"], 20000)

    # bob sends coin to charlie / charlie is a address owned by bob too.
    bob_charlie = generate.tx(
        coins[6],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        charlie_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    bob_charlie["proof"], bob_charlie["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[6], bob_charlie["tx_hash"], 21000)

    # bob sends coin to charlie / charlie is a address owned by bob too.
    charlie_peter = generate.tx(
        coins[6],
        bob_charlie["block_number"],
        COIN_DENOMINATION,
        charlie_addr,
        charlie_addr)

    # plasma block is generated and submited to mainnet
    charlie_peter["proof"], charlie_peter["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[6], charlie_peter["tx_hash"], 22000)

    # charlie starts exit
    exit.start_exit(
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
        challenges.challengeBetween(
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
    challenges.challengeBetween(
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
    """
    ___Scenario : Cannot challenge exit with an earlier spend
                  bob sends coin to oscar
                  bob sends coin to charlie
                  charlie sends coin to peter
                  alice challenges but fails due to providing earlier spend

    """
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address
    charlie_addr = accounts[4].address
    # alice deposit tx
    alice_alice = generate.tx(coins[7], 0, COIN_DENOMINATION, alice_addr, alice_addr)

    # alice sends coin to bob
    alice_bob = generate.tx(coins[7], 8, COIN_DENOMINATION, bob_addr, alice_addr)

    # plasma block is generated and submited to mainnet
    alice_bob["proof"], alice_bob["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[7], alice_bob["tx_hash"], 23000)

    # bob sends coin to oscar
    bob_oscar = generate.tx(
        coins[7],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        oscar_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    bob_oscar["proof"], bob_oscar["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[7], bob_oscar["tx_hash"], 24000)

    # bob sends coin to charlie / charlie is a address owned by bob too.
    bob_charlie = generate.tx(
        coins[7],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        charlie_addr,
        bob_addr)

    # plasma block is generated and submited to mainnet
    bob_charlie["proof"], bob_charlie["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[7], bob_charlie["tx_hash"], 25000)

    # bob sends coin to charlie / charlie is a address owned by bob too.
    charlie_peter = generate.tx(
        coins[7],
        bob_charlie["block_number"],
        COIN_DENOMINATION,
        charlie_addr,
        charlie_addr)

    # plasma block is generated and submited to mainnet
    charlie_peter["proof"], charlie_peter["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[7], charlie_peter["tx_hash"], 26000)

    # charlie starts exit.
    exit.start_exit(
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
        challenges.challengeBetween(
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
    exit.finish_exit(deployed_contracts, coins[7], charlie_addr)


def test_double_spend(setup_participate):
    """
    ___Scenario : Double spend after many tx
                  alice legitimately sends coin to bob
                  bob legitimately sends coin to oscar
                  oscar legitimately sends coin to charlie
                  charlie legitimately sends coin to peter
                  bob double spends coin by sending it to dylan
    """
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address
    charlie_addr = accounts[4].address
    peter_addr = accounts[5].address
    dylan_addr = accounts[6].address

    # alice deposit tx
    alice_alice = generate.tx(coins[8], 0, COIN_DENOMINATION, alice_addr, alice_addr)

    # alice sends coin to bob
    alice_bob = generate.tx(coins[8], 9, COIN_DENOMINATION, bob_addr, alice_addr)

    # plasma block is generated and submited to mainnet
    alice_bob["proof"], alice_bob["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[8], alice_bob["tx_hash"], 27000)

    # bob sends coin to oscar
    bob_oscar = generate.tx(
        coins[8],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        oscar_addr,
        bob_addr
    )
    # plasma block is generated and submited to mainnet
    bob_oscar["proof"], bob_oscar["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[8], bob_oscar["tx_hash"], 28000)

    # oscar to charlie transaction
    oscar_charlie = generate.tx(
        coins[8],
        bob_oscar["block_number"],
        COIN_DENOMINATION,
        charlie_addr,
        oscar_addr
    )

    # plasma block is generated and submited to mainnet
    oscar_charlie["proof"], oscar_charlie["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[8], oscar_charlie["tx_hash"], 29000)

    charlie_peter = generate.tx(
        coins[8],
        oscar_charlie["block_number"],
        COIN_DENOMINATION,
        peter_addr,
        charlie_addr
    )

    # plasma block is generated and submited to mainnet
    charlie_peter["proof"], charlie_peter["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[8], charlie_peter["tx_hash"], 30000)

    # double spend | bob to dylan
    bob_dylan = generate.tx(
        coins[8],
        alice_bob["block_number"],
        COIN_DENOMINATION,
        dylan_addr,
        bob_addr
    )

    # plasma block is generated and submited to mainnet
    bob_dylan["proof"], bob_dylan["block_number"] = generate.block(
        deployed_contracts.plasma_instance, coins[8], bob_dylan["tx_hash"], 31000)

    # dylan starts exit
    exit.start_exit(
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

    # oscar challenges
    challenges.challengeBetween(
        deployed_contracts.plasma_instance,
        coins[8],
        bob_oscar["block_number"],
        bob_oscar["tx"],
        bob_oscar["proof"],
        bob_oscar["signature"],
        oscar_addr
    )
    # oscar challenges successfully
