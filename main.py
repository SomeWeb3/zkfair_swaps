import random
import time
from random import randint

import requests
from eth_account import Account
from eth_account.signers.local import LocalAccount
from eth_typing import ChecksumAddress
from loguru import logger
from web3 import Web3
from web3.contract.contract import Contract
from web3.types import Wei

from config import (
    ERC20_ABI,
    GAS_LIMIT,
    LOOPS,
    ROUTER_ABI,
    RPC,
    SLEEP_BETWEEN_ACTIONS,
    SLEEP_BETWEEN_WALLETS,
    SWAP_AMOUNT_USD,
    SWAP_ROUTER,
    WETH,
    WUSDC,
)


def load_wallets() -> list[LocalAccount]:
    with open("wallets.txt", "r") as file:
        return [Account.from_key(line.strip()) for line in file.read().split("\n")]


def get_eth_price() -> float:
    """Get last ETH price in USD/USDT."""

    url = f"https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT"
    with requests.Session() as session:
        resp = session.get(url)
        resp_json = resp.json()
        return float(resp_json.get("price"))


def get_min_amount(value_in: float) -> tuple[int, int]:
    price = get_eth_price()
    return int(value_in * 10**18), int(value_in / price * 10**18)


def swap_usdc_to_eth(w3: Web3, wallet: LocalAccount, swap_contract: Contract) -> None:
    in_value, out_value = get_min_amount(SWAP_AMOUNT_USD)

    tx_data = swap_contract.functions.swapExactETHForTokens(
        amountOutMin=int(out_value * 0.95),
        path=[WUSDC, WETH],
        to=wallet.address,
        deadline=int(time.time()) + 600,
    ).build_transaction(
        {
            "value": Wei(in_value),
            "gasPrice": w3.eth.gas_price,
            "gas": GAS_LIMIT,
            "nonce": w3.eth.get_transaction_count(wallet.address),
        }
    )
    sign_tx = wallet.sign_transaction(tx_data)
    tx_hash = w3.eth.send_raw_transaction(sign_tx.rawTransaction)
    logger.info(f"{wallet.address} swap USDC->WETH. Tx: {tx_hash.hex()}")


def approve_eth(
    w3: Web3, wallet: LocalAccount, weth_contract: Contract, spender: ChecksumAddress
) -> None:
    weth_balance = weth_contract.functions.balanceOf(wallet.address).call()

    tx_data = weth_contract.functions.approve(
        spender=spender,
        amount=weth_balance,
    ).build_transaction(
        {
            "gasPrice": w3.eth.gas_price,
            "gas": 50000,
            "nonce": w3.eth.get_transaction_count(wallet.address),
        }
    )
    sign_tx = wallet.sign_transaction(tx_data)
    tx_hash = w3.eth.send_raw_transaction(sign_tx.rawTransaction)
    logger.info(f"{wallet.address} approve WETH. Tx: {tx_hash.hex()}")


def swap_eth_to_usdc(
    w3: Web3, wallet: LocalAccount, swap_contract, weth_contract: Contract
) -> None:
    weth_balance = weth_contract.functions.balanceOf(wallet.address).call()

    tx_data = swap_contract.functions.swapExactTokensForETH(
        amountIn=weth_balance,
        amountOutMin=0,
        path=[WETH, WUSDC],
        to=wallet.address,
        deadline=int(time.time()) + 600,
    ).build_transaction(
        {
            "gasPrice": w3.eth.gas_price,
            "gas": GAS_LIMIT,
            "nonce": w3.eth.get_transaction_count(wallet.address),
        }
    )
    sign_tx = wallet.sign_transaction(tx_data)
    tx_hash = w3.eth.send_raw_transaction(sign_tx.rawTransaction)
    logger.info(f"{wallet.address} swap WETH->USDC. Tx: {tx_hash.hex()}")


def swap(w3: Web3, wallet: LocalAccount) -> None:
    swap_contract = w3.eth.contract(w3.to_checksum_address(SWAP_ROUTER), abi=ROUTER_ABI)
    weth_contract = w3.eth.contract(w3.to_checksum_address(WETH), abi=ERC20_ABI)

    swap_usdc_to_eth(w3, wallet, swap_contract)
    sleep(SLEEP_BETWEEN_ACTIONS)
    approve_eth(w3, wallet, weth_contract, swap_contract.address)
    sleep(SLEEP_BETWEEN_ACTIONS)
    swap_eth_to_usdc(w3, wallet, swap_contract, weth_contract)


def sleep(range_) -> None:
    sleep_time = random.uniform(*range_)
    logger.info(f"Sleep {sleep_time}")
    time.sleep(sleep_time)


def format_proxies(line: str) -> dict:
    ip, port, user, password = line.strip().split(":")
    return {
        "http": f"http://{user}:{password}@{ip}:{port}",
        "https": f"https://{user}:{password}@{ip}:{port}",
    }


def main():
    wallets = load_wallets()

    with open("proxies.txt", "r") as file:
        proxies = [format_proxies(line) for line in file.read().split("\n")]

    for _ in range(LOOPS):
        for wallet, proxy in zip(wallets, proxies):
            try:
                swap(
                    Web3(Web3.HTTPProvider(RPC, request_kwargs={"proxies": proxy})),
                    wallet,
                )
                sleep(SLEEP_BETWEEN_WALLETS)
            except Exception as ex:
                logger.error(f"{wallet.address}: {ex}")


if __name__ == "__main__":
    main()
