// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// We need a standard interface to interact with ERC20 tokens (like USDT, LINK, etc.).
// This tells our contract what functions are available on a standard token.
interface IERC20 {
    function transferFrom(address sender, address recipient, uint256 amount) external returns (bool);
    function allowance(address owner, address spender) external view returns (uint256);
}

/**
 * @title Settlement
 * @dev This is a simple contract that facilitates the settlement of trades
 * matched by our off-chain matching engine. It acts as a trusted intermediary
 * to ensure that the token swap happens correctly on the blockchain.
 */
contract Settlement {
    // Only the backend server should be able to call the settleTrade function.
    // We store the address of our backend's wallet here.
    address public owner;

    // This event is emitted every time a trade is successfully settled.
    // It creates a public log on the blockchain that can be easily queried.
    event TradeSettled(
        address indexed tokenSold,
        address indexed tokenBought,
        address seller,
        address buyer,
        uint256 amountSold,
        uint256 amountBought
    );

    // The constructor is run only once when the contract is deployed.
    // It sets the deployer of the contract as the 'owner'.
    constructor() {
        owner = msg.sender;
    }

    /**
     * @dev A modifier to ensure that only the owner (our backend server)
     * can call a specific function. If anyone else tries, the transaction will fail.
     */
    modifier onlyOwner() {
        require(msg.sender == owner, "Settlement: Caller is not the owner");
        _;
    }

    /**
     * @notice This is the main function that our backend will call.
     * @dev It executes the token swap between the seller and the buyer.
     * @param tokenSold The address of the token the seller is giving up.
     * @param tokenBought The address of the token the buyer is giving up (and the seller is receiving).
     * @param seller The wallet address of the seller.
     * @param buyer The wallet address of the buyer.
     * @param amountSold The amount of tokens the seller is selling.
     * @param amountBought The amount of tokens the buyer is paying.
     *
     * IMPORTANT PRECONDITION: Before this function is called, both the buyer and the seller
     * must have approved this contract to spend their tokens on their behalf. This is done
     * by calling the `approve()` function on the respective ERC20 token contracts.
     */
    function settleTrade(
        address tokenSold,
        address tokenBought,
        address seller,
        address buyer,
        uint256 amountSold,
        uint256 amountBought
    ) external onlyOwner {
        // 1. Transfer the token from the seller to the buyer.
        // The `transferFrom` function will only succeed if the seller has previously
        // given this contract an allowance of at least `amountSold`.
        bool sentSold = IERC20(tokenSold).transferFrom(seller, buyer, amountSold);
        require(sentSold, "Settlement: Failed to transfer token from seller");

        // 2. Transfer the token from the buyer to the seller.
        // This will only succeed if the buyer has given this contract an
        // allowance of at least `amountBought`.
        bool sentBought = IERC20(tokenBought).transferFrom(buyer, seller, amountBought);
        require(sentBought, "Settlement: Failed to transfer token from buyer");

        // 3. Emit an event to log that the trade was successfully settled.
        emit TradeSettled(tokenSold, tokenBought, seller, buyer, amountSold, amountBought);
    }
}
