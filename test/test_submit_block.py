import pytest

from helpers.const import DEFAULT_PASSWORD
from helpers.const import W3 as w3


def test_successful_block_submition(setup):
    '''
        successful submission of a block on-chain
        sparse_merkle_tree not included since the test is done just to see if
        values are being stored as expected.
    '''
    _, deployed_contracts = setup
    plasma_instance = deployed_contracts.plasma_instance

    # dummy root hash
    root = w3.soliditySha3(['string'], ['test'])
    args = (1_000, root)
    kwargs = {'from': w3.eth.accounts[0]}

    w3.personal.unlockAccount(w3.eth.defaultAccount, '')
    fn_submit = plasma_instance.functions.submitBlock(*args)
    kwargs['gas'] = fn_submit.estimateGas(kwargs)
    tx_hash = fn_submit.transact(kwargs)
    assert w3.eth.waitForTransactionReceipt(tx_hash).status

    root_on_contract = plasma_instance.functions.childChain(1_000).call()
    assert root_on_contract[0] == root


def test_unsuccessful_block_submition(setup):
    '''
        fails as block number provided is not greater than current block on smart contract
    '''
    _, deployed_contracts = setup
    plasma_instance = deployed_contracts.plasma_instance

    root = w3.soliditySha3(['string'], ['test'])

    with pytest.raises(Exception):
        args = (0, root)
        kwargs = {'from': w3.eth.accounts[0]}

        w3.personal.unlockAccount(w3.eth.defaultAccount, '')
        fn_submit = plasma_instance.functions.submitBlock(*args)
        kwargs['gas'] = fn_submit.estimateGas(kwargs)
        tx_hash = fn_submit.transact(kwargs)
        assert w3.eth.waitForTransactionReceipt(tx_hash).status


def test_unauthorized_user_submition(setup):
    accounts, deployed_contracts = setup
    alice_addr = accounts[1].address

    plasma_instance = deployed_contracts.plasma_instance

    root = w3.soliditySha3(['string'], ['test'])

    with pytest.raises(Exception):
        args = (0, root)
        kwargs = {'from': alice_addr}
        fn_submit = plasma_instance.functions.submitBlock(*args)
        kwargs['gas'] = fn_submit.estimateGas()
        w3.personal.unlockAccount(alice_addr, DEFAULT_PASSWORD)
        tx_hash = fn_submit.transact(kwargs)
        assert w3.eth.waitForTransactionReceipt(tx_hash).status
