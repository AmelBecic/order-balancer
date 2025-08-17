import logging
import json
from collections import defaultdict
from heapq import heappush, heappop
from datetime import datetime
import aio_pika
from web3 import Web3

# Local imports
from config import settings

logging.basicConfig(level=logging.INFO)

# --- Blockchain Configuration ---

# This is the ABI (Application Binary Interface) for our Settlement contract.
# It tells web3.py what functions are available on the contract and how to call them.
SETTLEMENT_CONTRACT_ABI = json.loads('[{"inputs":[],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"tokenSold","type":"address"},{"indexed":true,"internalType":"address","name":"tokenBought","type":"address"},{"internalType":"address","name":"seller","type":"address"},{"internalType":"address","name":"buyer","type":"address"},{"internalType":"uint256","name":"amountSold","type":"uint256"},{"internalType":"uint256","name":"amountBought","type":"uint256"}],"name":"TradeSettled","type":"event"},{"inputs":[{"internalType":"address","name":"tokenSold","type":"address"},{"internalType":"address","name":"tokenBought","type":"address"},{"internalType":"address","name":"seller","type":"address"},{"internalType":"address","name":"buyer","type":"address"},{"internalType":"uint256","name":"amountSold","type":"uint256"},{"internalType":"uint256","name":"amountBought","type":"uint256"}],"name":"settleTrade","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}]')

# MOCK TOKEN ADDRESSES on Sepolia Testnet
# In a real application, this would come from a database or a more robust configuration.
# These are example addresses for wrapped tokens on Sepolia.
TOKEN_ADDRESSES = {
    "BTC": "0x1c842981d3106b89a25b0a3f5a5a4b572517133d", # Wrapped BTC (WBTC)
    "USDT": "0x28B33551586525526567545a0e36d2b21eba54df"  # Tether USD (USDT)
}


class MatchingEngine:
    def __init__(self):
        self.order_book = defaultdict(lambda: {"bids": [], "asks": []})
        self.market_data_exchange = None
        
        # --- Initialize Web3 Connection ---
        self.w3 = Web3(Web3.HTTPProvider(settings.SEPOLIA_RPC_URL))
        self.account = self.w3.eth.account.from_key(settings.BACKEND_WALLET_PRIVATE_KEY)
        self.settlement_contract = self.w3.eth.contract(
            address=settings.SETTLEMENT_CONTRACT_ADDRESS,
            abi=SETTLEMENT_CONTRACT_ABI
        )
        logging.info(f"Matching Engine initialized and connected to Web3. Operator address: {self.account.address}")
        # --- End of Web3 Initialization ---

    def set_market_data_exchange(self, exchange: aio_pika.abc.AbstractExchange):
        self.market_data_exchange = exchange
        logging.info("Market data exchange has been set in the engine.")

    async def process_order(self, order: dict, db):
        # ... (This function remains the same) ...
        symbol = order.get('symbol')
        if not symbol:
            logging.error("Order is missing a symbol.")
            return

        if order.get('type') == 'limit':
            await self.process_limit_order(order, db)
        elif order.get('type') == 'market':
            await self.process_market_order(order, db)
        else:
            logging.warning(f"Unsupported order type: {order.get('type')}")
        
        await self.publish_order_book_update(symbol)

    async def process_limit_order(self, order: dict, db):
        # ... (This function now calls the settlement logic) ...
        symbol = order['symbol']
        side = order['side']
        order_price = float(order['price'])
        order_quantity = float(order['quantity'])
        
        trades = []
        quantity_to_fill = order_quantity

        if side == 'buy':
            while self.order_book[symbol]['asks'] and quantity_to_fill > 0 and order_price >= self.order_book[symbol]['asks'][0][0]:
                best_ask_price, matched_order = self.order_book[symbol]['asks'][0]
                matched_quantity = float(matched_order['quantity'])
                
                trade_quantity = min(quantity_to_fill, matched_quantity)
                
                # --- Settle the trade on-chain ---
                tx_hash = self._settle_trade_on_chain(
                    symbol=symbol,
                    buyer_order=order,
                    seller_order=matched_order,
                    trade_price=best_ask_price,
                    trade_quantity=trade_quantity
                )
                if tx_hash:
                    trades.append({"price": best_ask_price, "quantity": trade_quantity, "tx_hash": tx_hash})
                # --- End of settlement ---
                
                quantity_to_fill -= trade_quantity
                matched_order['quantity'] = str(matched_quantity - trade_quantity)

                if float(matched_order['quantity']) <= 0:
                    heappop(self.order_book[symbol]['asks'])
        
        elif side == 'sell':
            while self.order_book[symbol]['bids'] and quantity_to_fill > 0 and order_price <= -self.order_book[symbol]['bids'][0][0]:
                best_bid_price_neg, matched_order = self.order_book[symbol]['bids'][0]
                best_bid_price = -best_bid_price_neg
                matched_quantity = float(matched_order['quantity'])

                trade_quantity = min(quantity_to_fill, matched_quantity)
                
                # --- Settle the trade on-chain ---
                tx_hash = self._settle_trade_on_chain(
                    symbol=symbol,
                    buyer_order=matched_order,
                    seller_order=order,
                    trade_price=best_bid_price,
                    trade_quantity=trade_quantity
                )
                if tx_hash:
                    trades.append({"price": best_bid_price, "quantity": trade_quantity, "tx_hash": tx_hash})
                # --- End of settlement ---

                quantity_to_fill -= trade_quantity
                matched_order['quantity'] = str(matched_quantity - trade_quantity)

                if float(matched_order['quantity']) <= 0:
                    heappop(self.order_book[symbol]['bids'])

        if quantity_to_fill > 0:
            order['quantity'] = str(quantity_to_fill)
            if side == 'buy':
                heappush(self.order_book[symbol]['bids'], (-order_price, order))
            else:
                heappush(self.order_book[symbol]['asks'], (order_price, order))
            await self.save_order_to_db(order, db)
        
        if trades:
            await self.save_trades_to_db(symbol, trades, db)

    async def process_market_order(self, order: dict, db):
        # ... (This function is left as an exercise, but would follow the same settlement pattern as process_limit_order) ...
        logging.warning("Market order processing with on-chain settlement is not yet implemented.")


    def _settle_trade_on_chain(self, symbol: str, buyer_order: dict, seller_order: dict, trade_price: float, trade_quantity: float):
        """
        Builds and sends a transaction to the Settlement smart contract.
        """
        try:
            logging.info(f"Attempting to settle trade for {trade_quantity} of {symbol} at ${trade_price}")
            
            token_a, token_b = symbol.split('/')
            token_sold_address = TOKEN_ADDRESSES[token_a]
            token_bought_address = TOKEN_ADDRESSES[token_b]

            # NOTE: This assumes 18 decimals for both tokens. In a real app, you'd fetch this.
            amount_sold = self.w3.to_wei(trade_quantity, 'ether') 
            amount_bought = self.w3.to_wei(trade_quantity * trade_price, 'ether')

            # Build the transaction to call the `settleTrade` function
            tx = self.settlement_contract.functions.settleTrade(
                token_sold_address,
                token_bought_address,
                seller_order['address'],
                buyer_order['address'],
                amount_sold,
                amount_bought
            ).build_transaction({
                'from': self.account.address,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'gas': 200000, # A reasonable gas limit
                'gasPrice': self.w3.eth.gas_price
            })

            # Sign the transaction with the backend's private key
            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=self.account.key)

            # Send the transaction to the blockchain
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            logging.info(f"Trade settlement transaction sent. Tx Hash: {tx_hash.hex()}")
            return tx_hash.hex()

        except Exception as e:
            logging.error(f"On-chain settlement failed: {e}")
            return None

    async def save_trades_to_db(self, symbol, trades, db):
        """Saves a list of executed trades, including the tx_hash, to the database."""
        trade_docs = [
            {
                "symbol": symbol,
                "price": t['price'],
                "quantity": t['quantity'],
                "tx_hash": t.get('tx_hash'), # Add the transaction hash
                "timestamp": datetime.utcnow()
            } for t in trades
        ]
        await db["trades"].insert_many(trade_docs)
        logging.info(f"Saved {len(trades)} trade(s) to database for symbol {symbol}.")

    # ... (The rest of the functions: save_order_to_db, publish_order_book_update, load_orders_from_db remain the same) ...

    async def save_order_to_db(self, order: dict, db):
        try:
            order['created_at'] = datetime.utcnow()
            result = await db["orders"].insert_one(order)
            logging.info(f"Order {result.inserted_id} saved to database by engine.")
        except Exception as e:
            logging.error(f"Engine failed to save order to DB: {e}")

    async def publish_order_book_update(self, symbol: str):
        if not self.market_data_exchange:
            logging.warning("Market data exchange not set. Cannot publish update.")
            return

        bids = sorted([order_dict for price, order_dict in self.order_book[symbol]['bids']], key=lambda x: float(x['price']), reverse=True)[:10]
        asks = sorted([order_dict for price, order_dict in self.order_book[symbol]['asks']], key=lambda x: float(x['price']))[:10]
        
        update_payload = {
            "symbol": symbol, 
            "bids": [[o['price'], o['quantity']] for o in bids], 
            "asks": [[o['price'], o['quantity']] for o in asks]
        }
        
        message = aio_pika.Message(body=json.dumps(update_payload).encode(), content_type="application/json")
        normalized_symbol = symbol.replace('/', '').lower()
        routing_key = f"orderbook.{normalized_symbol}"
        
        await self.market_data_exchange.publish(message, routing_key=routing_key)
        logging.info(f"Published order book update for {symbol} on routing key {routing_key}")

    async def load_orders_from_db(self, db):
        logging.info("Loading existing orders from database...")
        orders_cursor = db["orders"].find({"status": "open"})
        count = 0
        async for order in orders_cursor:
            count += 1
            symbol, price = order['symbol'], float(order.get('price', 0))
            if order['side'] == 'buy':
                heappush(self.order_book[symbol]['bids'], (-price, order))
            else:
                heappush(self.order_book[symbol]['asks'], (price, order))
        if count > 0:
            logging.info(f"Successfully loaded {count} existing open orders.")

