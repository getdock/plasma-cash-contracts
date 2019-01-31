import time

from fixtures.const import w3, DEFAULT_PASSWORD


# startExit calling PlasmaContract startExit function.
# coinId: ID of the coin which user wants to exit.
# prevtx_bytes: the previous transaction bytes that happend right before exiting transaction.
# exitingtx_bytes: the transaction bytes of the transaction that user is starting exit with.
# prevtx_inclusion_proof: the previous transaction SparseMerkleTree proof.
# exitingtx_inclusion_proof: the exiting transaction SparseMerkleTree proof.
# signature: signature of the exiting transaction.
# blocks: block number of prevTx and exitTx.
# addr: address of the exiter.
def start_exit(
        plasma_instance,
        coinId,
        prevtx_bytes,
        exitingtx_bytes,
        prevtx_inclusion_proof,
        exitingtx_inclusion_proof,
        signature,
        blocks,
        addr):
    # unlocking account so we can call startExit function
    w3.personal.unlockAccount(addr, DEFAULT_PASSWORD)
    # getting the gas cost of startExit function.
    gas = plasma_instance.functions.startExit(
        coinId,
        prevtx_bytes,
        exitingtx_bytes,
        prevtx_inclusion_proof,
        exitingtx_inclusion_proof,
        signature,
        blocks
    ).estimateGas({'from': addr, 'value': w3.toWei(0.1, 'ether')})

    # unlocking account so we can call startExit function.
    w3.personal.unlockAccount(addr, DEFAULT_PASSWORD)
    # calling startExit function on PlasmaContract.
    t = plasma_instance.functions.startExit(
        coinId,
        prevtx_bytes,
        exitingtx_bytes,
        prevtx_inclusion_proof,
        exitingtx_inclusion_proof,
        signature,
        blocks
    ).transact({'from': addr, 'value': w3.toWei(0.1, 'ether')})

    # asserting the status of respond to check if transaction is completed
    # successfully
    assert w3.eth.waitForTransactionReceipt(t).status == 1

    # getting exit struct from PlasmaContract.
    exitObj = plasma_instance.functions.getExit(coinId).call()
    # asserting the state of the coin, in this case 1 means coin is EXITING
    assert exitObj[3] == 1


# finishExit calling PlasmaContract finalizeExit function.
# coinId : ID of the coin that user wants to finish exit.
# address : address of the user that finishes exit.
def finish_exit(deployed_contracts, coinId, address):
    # getting the erc20_instance set by deployer.
    erc20_instance = deployed_contracts.erc20_instance
    # getting the erc721_instance set by deployer.
    erc721_instance = deployed_contracts.erc721_instance

    # time required to wait for MATURITY_PERIOD(on mainnet = 1 week / 5 days)
    time.sleep(3)

    """
    Note :
        estimateGas is not working as it should in the case of calling finalizeExit() function.
    """

    # unlocking account so we can call finalizeExit function.
    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)

    # calling finalizeExit function on PlasmaContract.
    final = deployed_contracts.plasma_instance.functions.finalizeExit(
        coinId).transact({'from': address, 'gas': 500000})

    # asserting the status of respond to check if transaction is completed
    # successfully.
    assert w3.eth.waitForTransactionReceipt(final).status == 1

    # calling ownerOfToken function on DockPlasmaToken.
    newOwner = erc721_instance.functions.ownerOfToken(coinId).call()

    # owner of the coin has to be the one who fulfills the requirements to execute finalizeExit.
    # asserting the owner of the coin, newOwner address is equal with address.
    assert newOwner == address

    # calling the exit function on PlasmaContract.
    exitObj = deployed_contracts.plasma_instance.functions.getExit(coinId).call()

    # asserting the none existing exit
    assertNonExistingExit(exitObj)

    # calling balances instance of Balance struct on PlasmaContract.
    balance = deployed_contracts.plasma_instance.functions.balances(address).call()
    expected = w3.toWei(0.1, 'ether')

    # asseting balance[0] which represent bonded value, after finalizeExit is
    # executed successfully bonded value is equal with zero.
    assert balance[0] == 0

    # asserting balance[1] which represent withdrawable value, the user who
    # finalizes exit successfully can withdraw the withdrawable bond,
    assert balance[1] == expected

    # unlocking account so we can find how much gas is used by withdrawBonds
    # function.
    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)

    # getting the gas cost of withdrawBonds function.
    gas = deployed_contracts.plasma_instance.functions.withdrawBonds().estimateGas({
        'from': address})

    # unlocking account so we can call withdrawBonds function.
    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)

    # calling withdrawBonds function on PlasmaContract.
    t = deployed_contracts.plasma_instance.functions.withdrawBonds().transact(
        {'from': address, 'gas': gas})
    w3.eth.waitForTransactionReceipt(t)

    # calling balances instance of Balance struct on PlasmaContract.
    balance = deployed_contracts.plasma_instance.functions.balances(address).call()
    expected = w3.toWei(0, 'ether')

    # asseting balance[0] which represent bonded value, after finalizeExit is
    # executed successfully bonded value is equal with zero.
    assert balance[0] == 0
    # asserting balance[1] which represent withdrawable value, after
    # withdrawBonds function is executed this value has to be equal with zero
    assert balance[1] == expected

    # calling  balanceOf ERC20DockToken contract.
    balanceBefore = erc20_instance.functions.balanceOf(address).call()

    # unlocking account so we can call withdraw function.
    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)

    # getting the gas cost of withdraw function.
    gas = deployed_contracts.plasma_instance.functions.withdraw(
        coinId).estimateGas({'from': address})

    # unlocking account so we can call withdraw function.
    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)

    # calling withdraw function on PlasmaContract.
    t = deployed_contracts.plasma_instance.functions.withdraw(
        coinId).transact({'from': address, 'gas': gas})
    w3.eth.waitForTransactionReceipt(t)

    # calling  balanceOf ERC20DockToken contract.
    balance = erc20_instance.functions.balanceOf(address).call()

    # asserting balance of the user that withdraws the coin, current balance
    # has to be equal with balance before calling withdrawn function  and the
    # denomination of the coin.
    assert balance == balanceBefore + w3.toWei(5000, 'ether')


def finish_exits(plasma_instance, tokens, address):
    # time required to wait for MATURITY_PERIOD(on mainnet = 1 week / 5 days)
    time.sleep(3)

    # unlocking account so we can call finalizeExit function.
    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)

    # calling finalizeExit function on PlasmaContract.
    t = plasma_instance.functions.finalizeExits(
        tokens).transact({'from': address, 'gas': 8000000})

    # asserting the status of respond to check if transaction is completed
    # successfully
    assert w3.eth.waitForTransactionReceipt(t).status == 1


def cancel_exit(plasma_instance, coinId, address):
    # unlocking account so we can find how much gas is used by cancelExit
    # function.
    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)

    # getting the gas cost of withdraw function.
    gas = plasma_instance.functions.cancelExit(
        coinId).estimateGas({'from': address})

    # unlocking account so we can call cancelExit function.
    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)

    # calling cancelExit function on PlasmaContract.
    cancelExit = plasma_instance.functions.cancelExit(
        coinId).transact({'from': address, 'gas': gas})

    # asserting the status of respond to check if transaction is completed
    # successfully.
    assert w3.eth.waitForTransactionReceipt(cancelExit).status == 1

    # calling getExit function to check if an instance of Exit struct is deleted
    # coinId : ID of the coin that is exiting.
    exitObj = plasma_instance.functions.getExit(coinId).call()

    # asserting deleted struct of an exit that is canceled.
    assert exitObj[0] == '0x0000000000000000000000000000000000000000'
    assert exitObj[1] == 0
    assert exitObj[2] == 0
    assert exitObj[3] == 0


def assertNonExistingExit(exitObj):
    # asserting deleted struct of an Exit that is finalized.
    assert exitObj[0] == '0x0000000000000000000000000000000000000000'
    assert exitObj[1] == 0
    assert exitObj[2] == 0
    assert exitObj[3] == 2
