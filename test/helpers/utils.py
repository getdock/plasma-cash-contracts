from fixtures.const import w3, DEFAULT_PASSWORD


# participate function is used to participate on Plasma.
# address: the user's address who wants to participate.
# nr_of_tokens: number of tokens that will be created.
# amount : the denomination of each token.
def participate(deployed_contracts, address, nr_of_tokens, amount):
    for i in range(0, nr_of_tokens):
        w3.personal.unlockAccount(address, DEFAULT_PASSWORD)
        gas = deployed_contracts.plasma_instance.functions.participate(amount).estimateGas({'from': address})
        p = deployed_contracts.plasma_instance.functions.participate(amount).transact({'from': address, 'gas': gas})
        w3.eth.waitForTransactionReceipt(p)

    coins = deployed_contracts.erc721_instance.functions.getOwnedTokens(address).call()
    assert len(coins) == nr_of_tokens

    return coins
