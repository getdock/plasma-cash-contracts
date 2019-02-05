from helpers.const import COIN_DENOMINATION
from helpers import generate, events


# testing finalize exits function to exit all coins that are owned by alice
def test_finalize_exits(setup_participate):
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address

    alice_exit_txs = []

    # generating alice to alice deposit transctions
    for i in coins:
        alice_alice = generate.generate_tx(i, 0, COIN_DENOMINATION, alice_addr, alice_addr)
        alice_exit_txs.append(alice_alice)

    # starting exit from alice with all her deposit transactions
    for i in range(10):
        events.start_exit(
            deployed_contracts.plasma_instance,
            coins[i],
            '0x',  # prevtx_bytes
            alice_exit_txs[i]["tx"],  # exitingtx_bytes
            '0x',  # prevtx_inclusion_proof
            '0x',  # exitingtx_inclusion_proof
            alice_exit_txs[i]["signature"],  # signature
            [0, i + 1],  # blocks
            alice_addr  # exiter
        )
        events.finish_exits(deployed_contracts.plasma_instance, coins, alice_addr)

    exited_coins = []

    # getting all exited coins
    for i in coins:
        exited_coins.append(deployed_contracts.plasma_instance.functions.getPlasmaCoin(i).call())

    # checking if state of coin is set to EXITED
    for i in exited_coins:
        assert i[4] == 2
