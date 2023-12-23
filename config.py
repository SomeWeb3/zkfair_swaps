import json


SWAP_AMOUNT_USD = 1
GAS_LIMIT = 200_000
LOOPS = 1  # Сколько раз повторить количество прокрутов
SLEEP_BETWEEN_ACTIONS = (5, 10)
SLEEP_BETWEEN_WALLETS = (10, 20)

RPC = "https://rpc.zkfair.io"

SWAP_ROUTER = "0x72E25Dd6a6E75fC8f7820bA2eDEc3F89bB61f7A4"
WUSDC = "0xD33Db7EC50A98164cC865dfaa64666906d79319C"
WETH = "0x4b21b980d0Dc7D3C0C6175b0A412694F3A1c7c6b"


with open("abi/swap_abi.json", "r") as file:
    ROUTER_ABI = json.load(file)

with open("abi/erc20_abi.json", "r") as file:
    ERC20_ABI = json.load(file)
