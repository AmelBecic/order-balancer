Full-Stack Decentralized Order Book Exchange
This is a complete, real-time trading platform that uses an off-chain server for matching orders and an on-chain smart contract for settling trades on the Sepolia testnet.

📋 Requirements
Before you begin, ensure you have the following installed on your system:

Docker & Docker Compose: Install Docker Desktop

Node.js: Required for the smart contract deployment.

A Web3 Wallet: Like MetaMask, configured for the Sepolia testnet.

🚀 How to Run
Clone the Repository:

git clone <your-repository-url>
cd <your-repository-folder>

Create .env File: Create a file named .env in the main project folder and add the variables listed below.

Start the Application:

docker-compose up --build

The application will be available at http://localhost:8080.

⚙️ Environment Variables (.env)
You must create a .env file in the project's root directory with the following variables:

API_V1_STR: The prefix for the API, usually /api/v1.

SECRET_KEY: A secret key for the backend.

MONGODB_URL: The connection URL for the MongoDB database.

DATABASE_NAME: The name of the database to use.

RABBITMQ_URL: The connection URL for the RabbitMQ message queue.

BACKEND_CORS_ORIGINS: A list of allowed origins for the backend, e.g., '["http://localhost:8080"]'.

SETTLEMENT_CONTRACT_ADDRESS: The address of your deployed Settlement smart contract on the Sepolia testnet.

SEPOLIA_RPC_URL: Your RPC URL for the Sepolia testnet (e.g., from Alchemy or Infura).

BACKEND_WALLET_PRIVATE_KEY: The private key of the wallet that will pay for gas fees to settle trades.

📝 What This App Does
Real-time Trading: The order book updates live as users place and cancel orders.

Off-Chain Matching: A Python-based worker instantly matches buy and sell orders.

On-Chain Settlement: When a trade is matched, the backend calls a smart contract to securely swap the assets on the Sepolia blockchain.

Wallet Authorization: Users must connect their MetaMask wallet and sign every order, ensuring all actions are secure and user-approved.