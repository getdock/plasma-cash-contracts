from fixtures.const import w3, DEFAULT_PASSWORD

"""
    EstimateGas script deals with estimating gas cost of all functions that
    we are calling in contracts.
"""


# function to get gas cost of ERC20 deployement
# ercdata: contract json
def ERC20(ercdata):
    # building contract object.
    ERC20 = w3.eth.contract(
        # contract abi
        abi=ercdata['abi'],
        # compiled contract code.
        bytecode=ercdata['bytecode']
    )

    # unlocking account so we can call contract function
    w3.personal.unlockAccount(w3.eth.accounts[0], '')
    gas = ERC20.constructor().estimateGas({'from': w3.eth.accounts[0]})

    # returning gas cost
    return gas


# function to get gas cost of DoChecks deployement
# doChecksData: contract json
def DoChecks(doChecksData):
    # building contract object.
    DoChecks = w3.eth.contract(
        # contract abi
        abi=doChecksData['abi'],
        # compiled contract code.
        bytecode=doChecksData['bytecode']
    )

    # unlocking account so we can call contract function
    w3.personal.unlockAccount(w3.eth.accounts[0], '')
    gas = DoChecks.constructor().estimateGas({'from': w3.eth.accounts[0]})

    # returning gas cost
    return gas


# function to get gas cost of PlasmaTokenERC721 deployement
# erc721Data: contract json
def PlasmaTokenERC721(erc721Data):
    PlasmaTokenERC721 = w3.eth.contract(
        abi=erc721Data['abi'],
        bytecode=erc721Data['bytecode']
    )

    w3.personal.unlockAccount(w3.eth.accounts[0], '')
    gas = PlasmaTokenERC721.constructor().estimateGas(
        {'from': w3.eth.accounts[0]})

    return gas


# function to get gas cost of PlasmaContract deployement
# plasmadata: contract json
def PlasmaContract(plasmadata):
    Plasma = w3.eth.contract(
        abi=plasmadata['abi'],
        bytecode=plasmadata['bytecode']
    )

    w3.personal.unlockAccount(w3.eth.accounts[0], '')
    gas = Plasma.constructor().estimateGas({'from': w3.eth.accounts[0]})

    return gas


# function to get gas cost of loadAddress function
# plasmaAddress: parameter of loadPlasmaAddress() on erc721 token
def loadAddress(erc721_instance, plasmaAddress):
    w3.personal.unlockAccount(w3.eth.accounts[0], '')
    gas = erc721_instance.functions.loadPlasmaAddress(
        plasmaAddress).estimateGas({'from': w3.eth.accounts[0]})
    return gas


# function to get gas cost of challenge_before function
# token_id : the token_id which user wants to challenge.
# tx_bytes: the transaction bytes of the transaction that user is challenging with.
# tx_inclusion_proof : transaction SparseMerkleTree proof.
# signature: signature of the transaction that user is challenging with.
# block_number: block_number of the transaction that user is challenging with.
# address: the challenger address
# tx_hash: needed to get the challenge set on PlasmaContract.
def challenge_before(
        plasma_instance,
        token_id,
        tx_bytes,
        tx_inclusion_proof,
        signature,
        block_number,
        address
):
    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)
    gas = plasma_instance.functions.challengeBefore(
        token_id,
        tx_bytes,
        tx_inclusion_proof,
        signature,
        block_number
    ).estimateGas({'from': address, 'value': w3.toWei(0.1, 'ether')})

    return gas


# function to get gas cost of respondchallenge_before contract function
# token_id : the token_id which user wants to challenge.
# challengetx_hash: tx_hash of the tx that has challenged the exit
# respondingblock_number: block number of respond trasnaction
# respondingTransaction: the trasnaction which user responds to a challenge
# proof: proof of the respondingTransaction
# signature: signature of the respondingTransaction
# address: the responder address.
def respondchallenge_before(
        plasma_instance,
        token_id,
        challengingtx_hash,
        respondingblock_number,
        respondingTransaction,
        proof,
        signature,
        address):
    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)
    gas = plasma_instance.functions.respondChallengeBefore(
        token_id,
        challengingtx_hash,
        respondingblock_number,
        respondingTransaction,
        proof,
        signature
    ).estimateGas({'from': address})

    return gas


# function to get gas cost of challengeBetween contract function.
# token_id : the token_id which user wants to challenge.
# block_number: challenge tx block number
# tx_bytes: challenge tx bytes
# tx_inclusion_proof: smt proof of challenge tx
# signature: challenge tx signature
# address: challenger address
def challengeBetween(
        plasma_instance,
        token_id,
        block_number,
        tx_bytes,
        tx_inclusion_proof,
        signature,
        address):
    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)
    gas = plasma_instance.functions.challengeBetween(
        token_id,
        block_number,
        tx_bytes,
        tx_inclusion_proof,
        signature
    ).estimateGas({'from': address})

    return gas


# function to get gas cost of challengeAfter contract function
# token_id : the token_id which user wants to challenge.
# challengingblock_number: challenge trasnaction block number
# challengingTransaction: challenge trasnaction bytes
# proof: proof of challengingTransaction.
# signature: signature of challengingTransaction.
# address: challenger address
def challengeAfter(
        plasma_instance,
        token_id,
        challengingblock_number,
        challengingTransaction,
        proof,
        signature,
        address):
    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)
    gas = plasma_instance.functions.challengeAfter(
        token_id,
        challengingblock_number,
        challengingTransaction,
        proof,
        signature
    ).estimateGas({'from': address})

    return gas


# function to get gas cost of participate contract function
# address: function caller
# amount: amount to participate
def participate(plasma_instance, address, amount):
    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)
    gas = plasma_instance.functions.participate(
        amount).estimateGas({'from': address})

    return gas


# function to get gas cost of withdrawBonds contract function
# address: function caller
def withdrawBonds(plasma_instance, address):
    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)
    gas = plasma_instance.functions.withdrawBonds().estimateGas({
        'from': address})

    return gas


# function to get gas cost of erc20transfer contract function
# to: the recepient
# amount: the amount to be send
def erc20Transfer(erc20_instance, to, amount):
    w3.personal.unlockAccount(w3.eth.accounts[0], '')
    gas = erc20_instance.functions.transfer(
        to, amount).estimateGas({'from': w3.eth.accounts[0]})

    return gas


# function to get gas cost of erc20Approve contract function
# approveAddress : the address to approve
# address : the approver
# amount: amount to approve
def erc20Approve(erc20_instance, approveAddress, address, amount):
    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)
    gas = erc20_instance.functions.approve(
        approveAddress, amount).estimateGas({'from': address})

    return gas


# function to get gas cost of setMaturityAndBond contract function
def setMaturityAndBond(plasma_instance):
    w3.personal.unlockAccount(w3.eth.accounts[0], '')
    gas = plasma_instance.functions.setMaturityAndBond(
        w3.toWei(0.1, 'ether'), 2, 1).estimateGas({'from': w3.eth.accounts[0]})

    return gas


# function to get gas cost of erc20transfer contract function
# erc20_DOCK_addr = erc20 dock token contract address
# erc721_DPT_addr = erc721 token contract address
# do_checks_addr = DoChecks contract address
def load_addresses_on_plasma(deployed_contracts):
    w3.personal.unlockAccount(w3.eth.accounts[0], '')
    gas = deployed_contracts.plasma_instance.functions.setAddresses(
        deployed_contracts.erc20_instance.address,
        deployed_contracts.erc721_instance.address,
        deployed_contracts.checks_instance.address
    ).estimateGas(
        {'from': w3.eth.accounts[0]}
    )
    return gas
