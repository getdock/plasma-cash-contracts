from helpers import instances


# owned_coins calling DockPlasmaToken Contract getOwnedTokens function.
# addr: address of the user.
def owned_coins(addr):
    # getting the plasma_instance set by deployer.
    erc721_instance = instances.erc721_instance
    #  getOwnedTokens will return tokens that are owned by addr
    return erc721_instance.functions.getOwnedTokens(addr).call()


# coinById calling PlasmaContract getPlasmaCoin.
# coin_id: ID of the  plasma coin.
def coin_by_id(coin_id):
    # getting the plasma_instance set by deployer.
    plasma_instance = instances.plasma_instance
    # getPlasmaCoin will return coin struct.
    coin = plasma_instance.functions.getPlasmaCoin(coin_id).call()
    return coin
