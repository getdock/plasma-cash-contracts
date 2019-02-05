import pytest

from helpers.const import COIN_DENOMINATION
from helpers import generate, events


def test_owned_coin(setup_participate):
    """Assert the coins returned by participate are created as they should."""
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    alice_coins = deployed_contracts.erc721_instance.functions.getOwnedTokens(alice_addr).call()
    assert coins == alice_coins


def test_successful_cancelexit(setup_participate):
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address

    # alice deposit transaction.
    alice_alice = generate.generate_tx(coins[0], 0, COIN_DENOMINATION, alice_addr, alice_addr)

    # alice sends coin to bob.
    alice_bob = generate.generate_tx(coins[0], 1, COIN_DENOMINATION, bob_addr, alice_addr)
    # plasma block is generated and submited to mainnet.
    alice_bob["proof"], alice_bob["block_number"] = generate.generate_block(deployed_contracts.plasma_instance, coins[0], alice_bob["tx_hash"], 1000)
    # bob sends coin to oscar.
    bob_oscar = generate.generate_tx(coins[0], alice_bob["block_number"], COIN_DENOMINATION, oscar_addr, bob_addr)
    # plasma block is generated and submited to mainnet.
    bob_oscar["proof"], bob_oscar["block_number"] = generate.generate_block(deployed_contracts.plasma_instance, coins[0], bob_oscar["tx_hash"], 2000)

    # oscar starts exit.
    events.start_exit(
        deployed_contracts.plasma_instance,
        coins[0],
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


# Bob trys to cancel an Exit he has not started, he fails to do it.
def test_unsuccessful_cancelExit(setup_participate):
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address
    bob_addr = accounts[2].address
    oscar_addr = accounts[3].address

    # alice deposit transaction.
    alice_alice = generate.generate_tx(coins[1], 0, COIN_DENOMINATION, alice_addr, alice_addr)

    # alice sends coin to bob.
    alice_bob = generate.generate_tx(coins[1], 2, COIN_DENOMINATION, bob_addr, alice_addr)
    # plasma block is generated and submited to mainnet.
    alice_bob["proof"], alice_bob["block_number"] = generate.generate_block(deployed_contracts.plasma_instance, coins[1], alice_bob["tx_hash"], 3000)

    # bob sends coin to oscar.
    bob_oscar = generate.generate_tx(coins[1], alice_bob["block_number"], COIN_DENOMINATION, oscar_addr, bob_addr)
    # plasma block is generated and submited to mainnet.
    bob_oscar["proof"], bob_oscar["block_number"] = generate.generate_block(deployed_contracts.plasma_instance, coins[1], bob_oscar["tx_hash"], 4000)

    # oscar starts exit.
    events.start_exit(
        deployed_contracts.plasma_instance,
        coins[1],
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
        events.cancel_exit(deployed_contracts.plasma_instance, coins[1], bob_addr)
