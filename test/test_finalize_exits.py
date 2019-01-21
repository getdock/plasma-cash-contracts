from fixtures.const import COIN_DENOMINATION
from helpers import fetcher, generate, exit


# testing finalize exits function to exit all coins that are owned by alice
def test_finalize_exits(setup_participate):
    accounts, coins = setup_participate
    alice_addr = accounts[1].address

    aliceExitTxs = []

    # generating alice to alice deposit transctions
    for i in coins:
        alice_alice = generate.tx(i, 0, COIN_DENOMINATION, alice_addr, alice_addr)
        aliceExitTxs.append(alice_alice)

    # starting exit from alice with all her deposit transactions
    for i in range(10):
        exit.start_exit(
            coins[i],
            '0x',  # prevtx_bytes
            aliceExitTxs[i]["tx"],  # exitingtx_bytes
            '0x',  # prevtx_inclusion_proof
            '0x',  # exitingtx_inclusion_proof
            aliceExitTxs[i]["signature"],  # signature
            [0, i + 1],  # blocks
            alice_addr  # exiter
        )
        exit.finish_exits(coins, alice_addr)

    c = []

    # getting all exited coins
    for i in coins:
        c.append(fetcher.coin_by_id(i))

    # checking if state of coin is set to EXITED
    for i in c:
        assert i[4] == 2
