from helpers.const import (CHALLENGE_PARAMS, DEFAULT_BOND, DEFAULT_FROM,
                           DEFAULT_PASSWORD)
from helpers.const import W3 as w3


def test_maturity_and_bond(setup):
    '''
        test setMaturityAndBond function
    '''
    _, deployed_contracts = setup
    plasma_instance = deployed_contracts.plasma_instance

    args = (CHALLENGE_PARAMS['bond-to-wei'], CHALLENGE_PARAMS['maturity-period'], CHALLENGE_PARAMS['challenge-window'])
    kwargs = {'from': w3.eth.accounts[0]}

    w3.personal.unlockAccount(w3.eth.defaultAccount, '')
    fn_set = plasma_instance.functions.setMaturityAndBond(*args)
    kwargs['gas'] = fn_set.estimateGas(kwargs)
    tx_hash = fn_set.transact(kwargs)
    assert w3.eth.waitForTransactionReceipt(tx_hash).status

    maturity_period, challenge_window, bond = plasma_instance.functions.getMaturityAndBond().call()
    assert bond == CHALLENGE_PARAMS['bond-to-wei']
    assert maturity_period == CHALLENGE_PARAMS['maturity-period']
    assert challenge_window == CHALLENGE_PARAMS['challenge-window']


def test_unsuccessful_maturity_and_bond(setup):
    '''
        failed setMaturityAndBond since function can only be called by the
        contract owner
    '''
    accounts, deployed_contracts = setup
    alice_addr = accounts[1].address
    plasma_instance = deployed_contracts.plasma_instance

    args = (CHALLENGE_PARAMS['bond-to-wei'], CHALLENGE_PARAMS['maturity-period'], CHALLENGE_PARAMS['challenge-window'])
    kwargs = {'from': w3.eth.accounts[0]}

    w3.personal.unlockAccount(w3.eth.defaultAccount, '')
    fn_set = plasma_instance.functions.setMaturityAndBond(*args)
    gas = fn_set.estimateGas(kwargs)

    kwargs = {'from': alice_addr, 'gas': gas}
    w3.personal.unlockAccount(alice_addr, DEFAULT_PASSWORD)
    tx_hash = fn_set.transact(kwargs)
    assert w3.eth.waitForTransactionReceipt(tx_hash).status == 0
