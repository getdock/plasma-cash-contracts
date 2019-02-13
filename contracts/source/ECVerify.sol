pragma solidity ^0.4.24;

import "./ECDSA.sol";


library ECVerify {

    using ECDSA for bytes32;

    function recover(bytes32 hash, bytes signature) internal pure returns (address) {

        bytes32 prependMessage = hash.toEthSignedMessageHash();
        return prependMessage.recover(signature);

    }

    function ecverify(bytes32 hash, bytes sig, address signer) internal pure returns (bool) {
        return signer == recover(hash, sig);
    }

}
