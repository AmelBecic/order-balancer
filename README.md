Full-Stack Decentralized Order Book Exchange
This project is a complete, real-time, full-stack decentralized trading platform that features an off-chain order matching engine and on-chain settlement via a smart contract on the Sepolia testnet.

Features
Real-time Order Book: Live updates for bids and asks using WebSockets.

Off-Chain Matching Engine: A high-performance matching engine built in Python for instant order processing.

On-Chain Settlement: Matched trades are settled on the Sepolia testnet via a custom Settlement smart contract.

Wallet Integration: Connects to user wallets (like MetaMask) for secure trade authorization via cryptographic signatures.

Dockerized Environment: The entire application stack (frontend, backend, worker, database, message queue) is containerized for easy setup and deployment.

Prerequisites
Before you begin, ensure you have the following installed on your system:

Docker & Docker Compose: Install Docker Desktop

Node.js: Required for the Hardhat project.

A Web3 Wallet: Like MetaMask, configured for the Sepolia testnet.

🚀 How to Run the Application
1. Clone the Repository
First, clone this repository to your local machine.

git clone <your-repository-url>
cd <your-repository-folder>

2. Create the Environment File
The application uses a .env file to manage all its secret keys and configuration variables.

Create a new file named .env in the root directory of the project.

Copy the entire content of the sample file below and paste it into your new .env file.

Sample .env File
# Application
API_V1_STR=/api/v1
SECRET_KEY=a-very-secret-key-that-you-should-change

# MongoDB
MONGODB_URL=mongodb://root:example@mongo:27017/
DATABASE_NAME=trading_simulator

# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/

# A JSON-style list of origins that are allowed to connect.
BACKEND_CORS_ORIGINS='["http://localhost:8080"]'

# --- Blockchain Configuration ---
# The public address of your deployed Settlement smart contract
# Replace with your deployed contract address if you deploy a new one.
SETTLEMENT_CONTRACT_ADDRESS="0x0fE0Fb91b0d58c2ba65275f71De2C79017a32FB3"

# The RPC URL for the Sepolia test network (e.g., from Alchemy or Infura)
# You should replace this with your own key for production use.
SEPOLIA_RPC_URL="[https://eth-sepolia.g.alchemy.com/v2/wrDohIDEatXcEGTrlDx_r](https://eth-sepolia.g.alchemy.com/v2/wrDohIDEatXcEGTrlDx_r)"

# The private key of the wallet that will send transactions (the contract owner)
# This wallet needs Sepolia ETH to pay for gas fees.
BACKEND_WALLET_PRIVATE_KEY="YOUR_BACKEND_WALLET_PRIVATE_KEY"

3. Build and Run with Docker Compose
With the .env file in place, you can start the entire application stack with a single command.

docker-compose up --build

This command will build the images for your frontend, backend, and worker services and then start all the containers.

Accessing the Application
Once the containers are running, you can access the different parts of the application:

Frontend Application: http://localhost:8080

Backend API Docs: http://localhost:8000/docs

RabbitMQ Management: http://localhost:15672 (user: guest, pass: guest)

You can now connect your wallet, mock your balances, and start testing the full trading and settlement flow!