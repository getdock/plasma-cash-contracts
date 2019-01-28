import pytest

from fixtures.const import w3, DEFAULT_PASSWORD


# successfully submits a block on-chain
# sparse_merkle_tree not included since test is being done just to see if
# values are being stored as expected.
def test_successful_block_submition(setup):
    accounts, deployed_contracts = setup

    # getting plasma_instance set by deployer()
    plasma_instance = deployed_contracts.plasma_instance

    # dummy root hash
    root = w3.soliditySha3(['string'], ['test'])

    w3.personal.unlockAccount(w3.eth.accounts[0], '')
    submition = plasma_instance.functions.submitBlock(
        1000, root).transact({'from': w3.eth.accounts[0]})
    w3.eth.waitForTransactionReceipt(submition)

    rootOnContract = plasma_instance.functions.childChain(
        1000).call()

    assert rootOnContract[0] == root


# fails : block number provided is not greater than current block on smart contract.
def test_unsuccessful_block_submition(setup):
    accounts, deployed_contracts = setup

    plasma_instance = deployed_contracts.plasma_instance

    root = w3.soliditySha3(['string'], ['test'])

    with pytest.raises(Exception):
        gas = plasma_instance.functions.submitBlock(
            0, root).estimateGas({'from': w3.eth.accounts[0]})

        w3.personal.unlockAccount(w3.eth.accounts[0], '')
        submition = plasma_instance.functions.submitBlock(
            0, root).transact({'from': w3.eth.accounts[0]})
        w3.eth.waitForTransactionReceipt(submition)


def test_unauthorized_user_submition(setup):
    accounts, deployed_contracts = setup
    alice_addr = accounts[1].address

    plasma_instance = deployed_contracts.plasma_instance

    root = w3.soliditySha3(['string'], ['test'])

    with pytest.raises(Exception):
        gas = plasma_instance.functions.submitBlock(
            0, root).estimateGas({'from': alice_addr})

        w3.personal.unlockAccount(alice_addr, DEFAULT_PASSWORD)
        submition = plasma_instance.functions.submitBlock(
            0, root).transact({'from': alice_addr, 'gas': gas})
        w3.eth.waitForTransactionReceipt(submition)
