from fixtures.const import w3, DEFAULT_PASSWORD
from helpers import estimate_gas


# participate function is used to participate on Plasma.
# address: the user's address who wants to participate.
# nr_of_tokens: number of tokens that will be created.
# amount : the denomination of each token.
def participate(deployed_contracts, address, nr_of_tokens, amount):
    for i in range(0, nr_of_tokens):
        # getting gas cost of participate using estimateGas script.
        gas = estimate_gas.participate(deployed_contracts.plasma_instance, address, amount)

        # unlocking account so we can call function participate.
        w3.personal.unlockAccount(address, DEFAULT_PASSWORD)
        # calling participate function of PlasmaContract.
        p = deployed_contracts.plasma_instance.functions.participate(
            amount).transact({'from': address, 'gas': gas})
        w3.eth.waitForTransactionReceipt(p)

    # getting owned coins of the user.
    coins = deployed_contracts.erc721_instance.functions.getOwnedTokens(address).call()
    # length of coins(array) has to be equal with number of Tokens.
    assert len(coins) == nr_of_tokens

    return coins
