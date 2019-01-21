from helpers.web3Provider import w3
from helpers import instances, fetcher, estimate_gas

# account password
pwd = 'passw0rd'

# participate function is used to participate on Plasma.
# address: the user's address who wants to participate.
# nrOfTokens: number of tokens that will be created.
# amount : the denomination of each token.
def participate(address, nrOfTokens, amount):

    # getting the plasma_instance set by deployer.
    plasma_instance = instances.plasma_instance
    
    for i in range(0, nrOfTokens):
        # getting gas cost of participate using estimateGas script.
        gas = estimate_gas.participate(address, amount)

        # unlocking account so we can call function participate.
        w3.personal.unlockAccount(address, pwd)
        # calling participate function of PlasmaContract.
        p = plasma_instance.functions.participate(
            amount).transact({'from': address, 'gas': gas})
        w3.eth.waitForTransactionReceipt(p)

    # getting owned coins of the user.
    coins = fetcher.owned_coins(address)
    # length of coins(array) has to be equal with number of Tokens.
    assert len(coins) == nrOfTokens

    return coins
