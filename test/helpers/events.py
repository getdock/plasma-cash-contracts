import sys
import time

import rlp

from helpers.const import (BGS_LIMIT, CHALLENGE_PARAMS, COIN_DENOMINATION,
                           DEFAULT_BOND, DEFAULT_PASSWORD, ETHER_NAME)
from helpers.const import W3 as w3


def start_exit(
        plasma_instance,
        coin_id,
        prevtx_bytes,
        exitingtx_bytes,
        prevtx_inclusion_proof,
        exitingtx_inclusion_proof,
        signature,
        blocks,
        address):
    '''
        startExit calling PlasmaContract startExit function.
        coin_id: ID of the coin which user wants to exit.
        prevtx_bytes: the previous transaction bytes that happend right before exiting transaction.
        exitingtx_bytes: the transaction bytes of the transaction that user is starting exit with.
        prevtx_inclusion_proof: the previous transaction SparseMerkleTree proof.
        exitingtx_inclusion_proof: the exiting transaction SparseMerkleTree proof.
        signature: signature of the exiting transaction.
        blocks: block number of prevTx and exitTx.
        address: address of the exiter.
    '''
    # startExit function.
    args = (coin_id,
            prevtx_bytes,
            exitingtx_bytes,
            prevtx_inclusion_proof,
            exitingtx_inclusion_proof,
            signature,
            blocks)
    kwargs = {'from': address, 'value': DEFAULT_BOND}
    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)
    fn_start_x = plasma_instance.functions.startExit(*args)
    kwargs['gas'] = fn_start_x.estimateGas(kwargs)
    tx_hash = fn_start_x.transact(kwargs)
    assert w3.eth.waitForTransactionReceipt(tx_hash).status

    # getting exit struct from PlasmaContract and check if token is indeed EXITING
    exit_struct = plasma_instance.functions.getExit(coin_id).call()
    assert exit_struct[3]


def finish_exit(deployed_contracts, coin_id, address):
    '''
        finishExit calling PlasmaContract finalizeExit function.
        coinI_i : ID of the coin that user wants to finish exit.
        address : address of the user that finishes exit.

        NOTE: gas estimation will not work so we're defaulting to a tad below block size limit
    '''
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
    args = (coin_id,)
    kwargs = {'from': address, 'gas': BGS_LIMIT}
    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)
    fn_finalized_x = deployed_contracts.plasma_instance.functions.finalizeExit(*args)
    tx_hash = fn_finalized_x.transact(kwargs)
    assert w3.eth.waitForTransactionReceipt(tx_hash).status

    # calling ownerOfToken function on DockPlasmaToken.
    new_owner = erc721_instance.functions.ownerOfToken(coin_id).call()
    assert new_owner == address

    # calling the exit function on PlasmaContract and validate
    exit_struct = deployed_contracts.plasma_instance.functions.getExit(coin_id).call()
    assert exit_struct[0] == '0x0000000000000000000000000000000000000000'
    assert exit_struct[1] == 0
    assert exit_struct[2] == 0
    assert exit_struct[3] == 2

    # calling balances instance of Balance struct on PlasmaContract and validate
    balance = deployed_contracts.plasma_instance.functions.balances(address).call()
    expected = DEFAULT_BOND
    assert balance[0] == 0
    assert balance[1] == expected

    # check gas used
    kwargs = {'from': address}
    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)
    fn_withdraw = deployed_contracts.plasma_instance.functions.withdrawBonds()
    kwargs['gas'] = fn_withdraw.estimateGas(kwargs)
    tx_hash = fn_withdraw.transact(kwargs)
    assert w3.eth.waitForTransactionReceipt(tx_hash).status

    # calling balances instance of Balance struct on PlasmaContract.
    balance = deployed_contracts.plasma_instance.functions.balances(address).call()
    expected = w3.toWei(0, 'ether')
    assert balance[0] == 0
    assert balance[1] == expected

    # validate  balance(s) of ERC20DockToken contract.
    kwargs = {'from': address}
    balanceBefore = erc20_instance.functions.balanceOf(address).call()
    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)
    fn_withdraw = deployed_contracts.plasma_instance.functions.withdraw(coin_id)
    kwargs['gas'] = fn_withdraw.estimateGas(kwargs)
    tx_hash = fn_withdraw.transact(kwargs)
    assert w3.eth.waitForTransactionReceipt(tx_hash).status

    # validate  balance of ERC20DockToken contract.
    balanceAfter = erc20_instance.functions.balanceOf(address).call()
    assert balanceAfter == balanceBefore + COIN_DENOMINATION


def finish_exits(plasma_instance, tokens, address):
    '''
        exit multiple tokens
        NOTE:
            for MATURITY_PERIOD this changes from to 1 week / 5 days on on main/testnet
            explicit gas estimate needed for number of tokens (== loop iters in contract) and
            beware of block size limits in production
    '''
    challenge_ellapse = CHALLENGE_PARAMS['maturity-period'] + CHALLENGE_PARAMS['challenge-window']
    time.sleep(challenge_ellapse)

    kwargs = {'from': address}
    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)
    fn_finish_x = plasma_instance.functions.finalizeExits(tokens)
    gas = fn_finish_x.estimateGas(kwargs)
    kwargs['gas'] = gas * max(1, len(tokens))
    tx_hash = fn_finish_x.transact(kwargs)
    assert w3.eth.waitForTransactionReceipt(tx_hash).status


def cancel_exit(plasma_instance, coin_id, address):
    '''
        cancel exit of token reverts EXITING status
    '''
    args = (coin_id,)
    kwargs = {'from': address}
    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)
    fn_cancel_x = plasma_instance.functions.cancelExit(*args)
    kwargs['gas'] = fn_cancel_x.estimateGas(kwargs)
    tx_hash = fn_cancel_x.transact(kwargs)
    assert w3.eth.waitForTransactionReceipt(tx_hash).status

    # calling getExit function to check if Exit instance is delete
    exit_struct = plasma_instance.functions.getExit(coin_id).call()
    assert exit_struct[0] == '0x0000000000000000000000000000000000000000'
    assert exit_struct[1] == 0
    assert exit_struct[2] == 0
    assert exit_struct[3] == 0


def challenge_before(
        plasma_instance,
        token_id,
        tx_bytes,
        tx_inclusion_proof,
        signature,
        block_number,
        address,
        tx_hash):
    '''
        challenge_before calling PlasmaContract challenge_before function.
        token_id : the token_id which user wants to challenge.
        tx_bytes: the transaction bytes of the transaction that user is challenging with.
        tx_inclusion_proof : transaction SparseMerkleTree proof.
        signature: signature of the transaction that user is challenging with.
        block_number: block_number of the transaction that user is challenging with.
        address: the challenger address
        tx_hash: needed to get the challenge set on PlasmaContract.
    '''

    args = (token_id,
            tx_bytes,
            tx_inclusion_proof,
            signature,
            block_number)

    kwargs = {'from': address, 'value': DEFAULT_BOND}
    w3.personal.unlockAccount(w3.eth.defaultAccount, '')
    fn_challenge_before = plasma_instance.functions.challengeBefore(*args)
    kwargs['gas'] = fn_challenge_before.estimateGas(kwargs)

    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)
    fn_hash = fn_challenge_before.transact(kwargs)
    assert w3.eth.waitForTransactionReceipt(fn_hash).status

    # building (decoding) tx from tx_bytes and getting challenge from PlasmaContract
    tx_from_bytes = rlp.decode(tx_bytes)
    args = (token_id, tx_hash)
    challenge_struct = plasma_instance.functions.getChallenge(*args).call()

    assert bytes.fromhex(challenge_struct[0][2:]) == tx_from_bytes[3]
    assert challenge_struct[1] == address
    assert challenge_struct[2] == tx_hash
    assert challenge_struct[3] == block_number


def finish_challenge_exit(plasma_instance, token_id, address):
    '''
        finishChallengeExit to finalize an exited coin
        token_id: of the token that user wants to finalize
        address: the initiater of finalizeExit function.

        NOTE:
            use time.sleep as a proxy to ripe token to maturity
            web3 gas estimate won't do it and it needs to e set.
    '''
    challenge_ellapse = CHALLENGE_PARAMS['maturity-period'] + CHALLENGE_PARAMS['challenge-window']
    time.sleep(challenge_ellapse)

    args = (token_id,)
    gas_estimate = BGS_LIMIT
    kwargs = {'from': address, 'gas': gas_estimate}
    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)
    fn_finalize_x = plasma_instance.functions.finalizeExit(*args)
    tx_hash = fn_finalize_x.transact(kwargs)
    assert w3.eth.waitForTransactionReceipt(tx_hash).status

    # balance[0] is the bond provided by exiter/challenger after finalizeExit and make sure it's 0
    # balance[1] is the withdrawable amount and should be twice the bonding amount
    balances = plasma_instance.functions.balances(address).call()
    assert balances[0] == 0
    assert balances[1] == DEFAULT_BOND * 2

    # get exit struct from plasma_instance
    exit_struct = plasma_instance.functions.getExit(token_id).call()
    assert_non_existing_exit(exit_struct)

    # get bonded amount
    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)
    tx_hash = plasma_instance.functions.withdrawBonds().transact({'from': address})
    assert w3.eth.waitForTransactionReceipt(tx_hash).status

    # get balance after withdrawBonds is called and validate that it's 0
    balances = plasma_instance.functions.balances(address).call()
    assert balances[1] == 0


def respond_challenge_before(
        plasma_instance,
        token_id,
        challengingtx_hash,
        respondingblock_number,
        respondingTransaction,
        proof,
        signature,
        address):
    '''
        respondchallenge_before calling PlasmaContract respondchallenge_before function.
        token_id : the token_id which user wants to challenge.
        challengetx_hash: tx_hash of the tx that has challenged the exit
        respondingblock_number: block number of respond transaction
        respondingTransaction: the transaction which user responds to a challenge
        proof: proof of the respondingTransaction
        signature: signature of the respondingTransaction
        address: the responder address.
    '''
    args = (token_id,
            challengingtx_hash,
            respondingblock_number,
            respondingTransaction,
            proof,
            signature)
    kwargs = {'from': address}
    w3.personal.unlockAccount(w3.eth.defaultAccount, '')
    fn_respond_ch = plasma_instance.functions.respondChallengeBefore(*args)
    kwargs['gas'] = fn_respond_ch.estimateGas(kwargs)
    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)
    tx_hash = fn_respond_ch.transact(kwargs)
    assert w3.eth.waitForTransactionReceipt(tx_hash).status


def challenge_after(
        plasma_instance,
        token_id,
        challengingblock_number,
        challengingTransaction,
        proof,
        signature,
        address):
    '''
        challengeAfter calling PlasmaContract challengeAfter function.
        token_id : the token_id which user wants to challenge.
        challengingblock_number: challenge transaction block number
        challengingTransaction: challenge transaction bytes
        proof: proof of challengingTransaction.
        signature: signature of challengingTransaction.
        address: challenger address
    '''
    args = (token_id,
            challengingblock_number,
            challengingTransaction,
            proof,
            signature)
    kwargs = {'from': address}
    w3.personal.unlockAccount(w3.eth.defaultAccount, '')
    fn_after_ch = plasma_instance.functions.challengeAfter(*args)
    kwargs['gas'] = fn_after_ch.estimateGas(kwargs)

    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)
    tx_hash = fn_after_ch.transact(kwargs)
    assert w3.eth.waitForTransactionReceipt(tx_hash).status

    assert_successful_challenge(plasma_instance, address)

    exit_struct = plasma_instance.functions.getExit(token_id).call()
    assert_non_existing_exit(exit_struct)


def challenge_between(
        plasma_instance,
        token_id,
        block_number,
        tx_bytes,
        tx_inclusion_proof,
        signature,
        address):
    '''
        challengeBetween calling PlasmaContract challengeBetween function.
        token_id : the token_id which user wants to challenge.
        block_number: challenge tx block number
        tx_bytes: challenge tx bytes
        tx_inclusion_proof: smt proof of challenge tx
        signature: challenge tx signature
        address: challenger address
    '''
    args = (token_id,
            block_number,
            tx_bytes,
            tx_inclusion_proof,
            signature)
    kwargs = {'from': address}
    w3.personal.unlockAccount(w3.eth.defaultAccount, '')
    fn_between_ch = plasma_instance.functions.challengeBetween(*args)
    kwargs['gas'] = fn_between_ch.estimateGas(kwargs)
    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)
    tx_hash = fn_between_ch.transact(kwargs)
    assert w3.eth.waitForTransactionReceipt(tx_hash).status

    assert_successful_challenge(plasma_instance, address)

    exit_struct = plasma_instance.functions.getExit(token_id).call()
    assert_non_existing_exit(exit_struct)


def assert_non_existing_exit(exit_struct):
    '''
        check if exit is deleted/reset when a challenge is successful
    '''
    assert exit_struct[0] == '0x0000000000000000000000000000000000000000'
    assert exit_struct[1] == 0
    assert exit_struct[2] == 0
    assert exit_struct[3] == 0


def assert_successful_challenge(plasma_instance, address):
    '''
        check balance of challenger if challenge was successfull
        getting the balance of challenger
    '''
    balances = plasma_instance.functions.balances(address).call()

    # balances[0], bonded amount, should be 0 and balances[1], withdrawable bond,
    # should be set paramater amount
    assert balances[0] == 0
    assert balances[1] == DEFAULT_BOND

    # withdraw the bond
    kwargs = {'from': address}
    w3.personal.unlockAccount(w3.eth.defaultAccount, '')
    kwargs['gas'] = plasma_instance.functions.withdrawBonds().estimateGas(kwargs)
    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)
    tx_hash = plasma_instance.functions.withdrawBonds().transact(kwargs)
    assert w3.eth.waitForTransactionReceipt(tx_hash).status

    # get the balance of challenger where bonded and withdrawable amounts should be 0
    balances = plasma_instance.functions.balances(address).call()
    assert balances[0] == 0
    assert balances[1] == 0
