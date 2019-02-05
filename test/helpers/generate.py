import random

import rlp
from hexbytes import HexBytes

from helpers.const import w3, DEFAULT_PASSWORD
from helpers.sparse_merkle_tree import SparseMerkleTree


def generate_dummy_txs():
    # function to generate dummy tx that will be included in sparse merkle tree.
    # The reason of generating dummy tx is just so we wont have a sparse merkle
    # tree containing only one transaction.
    uid = random.getrandbits(64)
    prevBlock = 5
    deno = 20
    owner = bytes.fromhex("30e3862ceb1a9b8b227bd2a53948c2ba2f1aa54a")

    tx = rlp.encode([uid, prevBlock, deno, owner])

    tx_hash = HexBytes(
        w3.soliditySha3(['bytes'], [tx])  # dummy hash(leaf)
    )

    tx = [uid, tx_hash]

    return tx


def generate_tx(token_id, prevBlock, denomination, to, address):
    # function used to generate tx that will be used off-chain to initiate transactions
    # which also be used to exit or challenge a coin.
    # token_id: token_id of the token we want to generate tx for.
    # prevBlock: prevBlock of the token.
    # denomination: denomination of token.
    # to: address where token is being send
    # address: the initiater of transaction
    # rlp encoded transaction
    tx = rlp.encode([token_id, prevBlock, denomination, bytes.fromhex(to[2:])])

    # checking if this tokens prev block is 0
    # if it is 0 it means that trasnaction is a deposit transction.
    # else : means that token was transfered before off-chain.
    if prevBlock == 0:

        # the kecca256 of token id since this is a deposit.
        tx_hash = w3.soliditySha3(['uint64'], [token_id])

        # unlocking account so we can sign the tx_hash.
        w3.personal.unlockAccount(address, DEFAULT_PASSWORD)

        # signing the hash with the address provided.
        signature = w3.eth.sign(address, data=tx_hash)

        # making a tx dictionary including signature and tx.
        tx = {
            "signature": signature,
            "tx": tx
        }

        # returning the tx dictionary
        return tx

    else:

        # the hash of the tx encoded bytes.
        tx_hash = w3.soliditySha3(['bytes'], [tx])
        # unlocking account to sign the tx_hash
        w3.personal.unlockAccount(address, DEFAULT_PASSWORD)
        # signing tx_hash with the address provided
        signature = w3.eth.sign(address, data=tx_hash)

        # building a dictionary including signature, tx, and tx_hash
        tx = {
            "signature": signature,
            "tx": tx,
            "tx_hash": tx_hash
        }

        # returning tx
        return tx


def generate_block(plasma_instance, token_id, tx_hash, block_number):
    # def block
    # function that is used to generate blocks which will be included in PlasmaContract on-chain
    # token_id: the token id which will be the key on smt.
    # tx_hash: transaction hash of the transaction which will be the value of the token_id on smt.
    # block_number: the block number which will be submited to PlasmaContract.
    """

        :param plasma_instance:
        :param token_id:
        :param tx_hash:
        :param block_number:
        :return:
        """
    dummy_txs = []
    hashes = {token_id: tx_hash}

    # filling dummy_txs list with dummy trasnactions
    for i in range(0, 20):
        dummy_txs.append(generate_dummy_txs())
    for i in dummy_txs:
        hashes.update({i[0]: i[1]})

    # Creating smt object with the provided hashes as leaves
    tree = SparseMerkleTree(64, leaves=hashes)

    # root of created smt
    root = tree.root

    # getting proof of the token id we just included in smt
    proof = tree.create_merkle_proof(token_id)

    # submiting the block to PlasmaContract on-chain
    w3.personal.unlockAccount(w3.eth.defaultAccount, '')
    submition = plasma_instance.functions.submitBlock(
        block_number, root).transact({'from': w3.eth.accounts[0]})
    # asserting the status of respond to check if transaction is completed
    # successfully
    assert w3.eth.waitForTransactionReceipt(submition).status == 1

    # returning proof of token id and the block number of it.
    return proof, block_number
