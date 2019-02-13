import helpers.utils
from helpers import events
from helpers.const import COIN_DENOMINATION


def test_finalize_exits(setup_participate):
    '''
        finalize exit for all owned token
    '''
    accounts, deployed_contracts, coins = setup_participate
    alice_addr = accounts[1].address

    alice_exit_txs = []

    # generating alice to alice deposit transactions
    for i in coins:
        previous_block = 0
        alice_alice = helpers.utils.generate_tx(i, previous_block, COIN_DENOMINATION, alice_addr, alice_addr)
        alice_exit_txs.append(alice_alice)

    # starting exit from alice
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

    coins_x = [deployed_contracts.plasma_instance.functions.getPlasmaCoin(c).call() for c in coins]

    # check if state of each coin is EXITED
    for c in coins_x:
        assert c[4] == 2
