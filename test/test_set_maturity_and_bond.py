from fixtures.const import ETHER_NAME, DEFAULT_PASSWORD, w3
from helpers import estimate_gas


# testing setMaturityAndBond function on PlasmaContract
def test_maturity_and_bond(setup):
    accounts, deployed_contracts = setup
    # getting plasma_instance set by deployer
    plasma_instance = deployed_contracts.plasma_instance

    # getting gas cost on setMaturityAndBond function
    gas = estimate_gas.setMaturityAndBond(plasma_instance)

    w3.personal.unlockAccount(w3.eth.accounts[0], '')
    bond = plasma_instance.functions.setMaturityAndBond(
        w3.toWei(0.1, ETHER_NAME),
        2,
        1
    ).transact(
        {'from': w3.eth.accounts[0]}
    )
    tx_receipt = w3.eth.waitForTransactionReceipt(bond)

    maturity_period, challenge_window, bond = plasma_instance.functions.getMaturityAndBond().call()

    assert tx_receipt.status == 1
    assert bond == w3.toWei(0.1, ETHER_NAME)
    assert maturity_period == 2
    assert challenge_window == 1


# testing unsuccessful set of maturityAndbond since function can be called only
# by the owner and not by pariticipants.
def test_unsuccessful_maturity_and_bond(setup):
    accounts, deployed_contracts = setup
    alice_addr = accounts[1].address

    # getting plasma_instance set by deployer
    plasma_instance = deployed_contracts.plasma_instance

    # getting gas cost on setMaturityAndBond function
    gas = estimate_gas.setMaturityAndBond(plasma_instance)

    w3.personal.unlockAccount(alice_addr, DEFAULT_PASSWORD)
    bond = plasma_instance.functions.setMaturityAndBond(
        w3.toWei(0.1, ETHER_NAME),
        2,
        1
    ).transact(
        {'from': alice_addr, 'gas': gas}
    )
    tx_receipt = w3.eth.waitForTransactionReceipt(bond)

    maturity_period, challenge_window, bond = plasma_instance.functions.getMaturityAndBond().call()

    # respond status should be 0 since contract throws 
    assert tx_receipt.status == 0
