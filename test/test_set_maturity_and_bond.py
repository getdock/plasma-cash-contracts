from helpers.const import w3, DEFAULT_BOND, DEFAULT_FROM, DEFAULT_PASSWORD


# testing setMaturityAndBond function on PlasmaContract
def test_maturity_and_bond(setup):
    accounts, deployed_contracts = setup
    # getting plasma_instance set by deployer
    plasma_instance = deployed_contracts.plasma_instance

    w3.personal.unlockAccount(w3.eth.defaultAccount, '')
    gas = plasma_instance.functions.setMaturityAndBond(DEFAULT_BOND, 2, 1).estimateGas(DEFAULT_FROM)

    bond = plasma_instance.functions.setMaturityAndBond(
        DEFAULT_BOND,
        2,
        1
    ).transact(
        {'from': w3.eth.accounts[0]}
    )
    tx_receipt = w3.eth.waitForTransactionReceipt(bond)

    maturity_period, challenge_window, bond = plasma_instance.functions.getMaturityAndBond().call()

    assert tx_receipt.status == 1
    assert bond == DEFAULT_BOND
    assert maturity_period == 2
    assert challenge_window == 1


# testing unsuccessful set of maturityAndbond since function can be called only
# by the owner and not by pariticipants.
def test_unsuccessful_maturity_and_bond(setup):
    accounts, deployed_contracts = setup
    alice_addr = accounts[1].address

    # getting plasma_instance set by deployer
    plasma_instance = deployed_contracts.plasma_instance

    w3.personal.unlockAccount(w3.eth.defaultAccount, '')
    gas = plasma_instance.functions.setMaturityAndBond(DEFAULT_BOND, 2, 1).estimateGas(DEFAULT_FROM)

    w3.personal.unlockAccount(alice_addr, DEFAULT_PASSWORD)
    bond = plasma_instance.functions.setMaturityAndBond(
        DEFAULT_BOND,
        2,
        1
    ).transact(
        {'from': alice_addr, 'gas': gas}
    )
    tx_receipt = w3.eth.waitForTransactionReceipt(bond)

    maturity_period, challenge_window, bond = plasma_instance.functions.getMaturityAndBond().call()

    # respond status should be 0 since contract throws 
    assert tx_receipt.status == 0
