from fixtures.const import w3, DEFAULT_PASSWORD, DEFAULT_FROM


# transfer function to handle erc20 transfers to users
# address: the address where tokens are being transafered.
# amount: the amount that we want to trasnfer
def transfer(address, amount, erc20_instance):
    w3.personal.unlockAccount(w3.eth.accounts[0], '')
    gas = erc20_instance.functions.transfer(address, amount).estimateGas(DEFAULT_FROM)

    # calling transfer function on erc20 contract.
    transfer1 = erc20_instance.functions.transfer(
        address, amount).transact({'from': w3.eth.accounts[0], 'gas': gas})

    # asserting the status of respond to check if transaction is completed successfully
    assert w3.eth.waitForTransactionReceipt(transfer1).status == 1

    # checking if amount transfered is correct
    balance = erc20_instance.functions.balanceOf(address).call()
    assert balance == amount

    # returning the bilance of address
    return balance


# approve function to handle approves on erc20 contract
# approve_address : the address we want to approve
# address : approver(owner of erc20 tokens)
# amount: amount to approve
def approve(approve_address, address, amount, erc20_instance):
    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)
    gas = erc20_instance.functions.approve(approve_address, amount).estimateGas({'from': address})

    # calling approve function on erc20 contract.
    approve1 = erc20_instance.functions.approve(
        approve_address, amount).transact({'from': address, 'gas': gas})

    # asserting the status of respond to check if transaction is completed successfully
    assert w3.eth.waitForTransactionReceipt(approve1).status == 1

    # checking if amount was approved correctly.
    allowance = erc20_instance.functions.allowance(address, approve_address).call()
    assert allowance == amount

    # returning amount approved
    return allowance
