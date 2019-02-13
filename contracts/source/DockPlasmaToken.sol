pragma solidity ^0.4.24;

import "./ERC721Full.sol";


contract DockPlasmaToken is ERC721Full("DockPlasmaToken", "DPT") {

    // Event for plasma address load logging.
    // @param plasmaAddress The address of the deployed PlasmaContract
    event loadPlasmaAddres(address plasmaAddress);

    //plasmaAddress is the address setted by loadPlasmaAddres function
    address public plasmaAddress;
    //owner/deployer of the contract
    address public owner;

    //modifier to check if caller is plasma contract
    modifier onlyPlasma() {
        require(msg.sender == plasmaAddress);
        _;
    }

    constructor() public {
        owner = msg.sender;
    }

    // @dev called by owner/deployer to link Plasma Contract with DockPlasmaToken
    // @param _plasmaAddress the address of deployed PlasmaContract
    function loadPlasmaAddress(address _plasmaAddress) public {
        require(msg.sender == owner);

        plasmaAddress = _plasmaAddress;

        emit loadPlasmaAddres(plasmaAddress);
    }

    // @dev called by PlasmaContract when deposit function is called
    // @param _plasmaAddress The address of deployed PlasmaContract
    // @param to The address of depositer
    // @param tokenId The token id generated on PlasmaContract
    function mint(address to, uint64 tokenId) public onlyPlasma() {
        _mint(to, tokenId);
    }

    // @dev called by PlasmaContract when a token is being finalized
    // @param from Current owner of the token.
    // @param to Address to receive the token.
    // @param tokenId ID of the token to be transferred.
    function transferFrom(address from, address to, uint64 tokenId) public onlyPlasma() {
        _transferFrom(from, to, tokenId);
    }

    // @dev called by PlasmaContract when a token is withdrawn.
    // @param tokenId ID of token to be burned.
    function burn(uint64 tokenId) public onlyPlasma() returns (bool) {
        _burn(tokenId);
        return true;
    }

    // @dev called by anyone to get owner of a token.
    // @param tokenId ID of the token to query the owner of.
    // @return address currently marked as the owner of the given token ID
    function ownerOfToken(uint64 tokenId) public view returns (address) {
        return ownerOf(tokenId);
    }

    /**
     * @dev Gets the list of token IDs of the requested owner
     * @param _owner address owning the tokens
     * @return uint256[] List of token IDs owned by the requested address
     */
    function getOwnedTokens(address _owner) public view returns (uint256[]) {
        return  _tokensOfOwner(_owner);
    }

}
