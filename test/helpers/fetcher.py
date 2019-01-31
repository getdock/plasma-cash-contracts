# owned_coins calling DockPlasmaToken Contract getOwnedTokens function.
# addr: address of the user.
def owned_coins(erc721_instance, addr):
    #  getOwnedTokens will return tokens that are owned by addr
    return erc721_instance.functions.getOwnedTokens(addr).call()


# coinById calling PlasmaContract getPlasmaCoin.
# coin_id: ID of the  plasma coin.
def coin_by_id(plasma_instance, coin_id):
    # getPlasmaCoin will return coin struct.
    coin = plasma_instance.functions.getPlasmaCoin(coin_id).call()
    return coin
