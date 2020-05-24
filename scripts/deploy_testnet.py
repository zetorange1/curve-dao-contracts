# Testnet deployment script

import json
from web3 import middleware
from web3.gas_strategies.time_based import fast_gas_price_strategy as gas_strategy
from brownie import web3, accounts, ERC20CRV, VotingEscrow

USE_STRATEGIES = False  # Needed for the ganache-cli tester which doesn't like middlewares
POA = True

DEPLOYER = "0x66aB6D9362d4F35596279692F0251Db635165871"
TOKEN_MANAGER = "0x941A4d37eaC4fA7d4A2Bc68a2c8eA3a760D19039"

DISTRIBUTION_AMOUNT = 10 ** 6 * 10 ** 18
DISTRIBUTION_ADDRESSES = ["0x33A4622B82D4c04a53e170c638B944ce27cffce3", "0x6cd85bbb9147b86201d882ae1068c67286855211"]


def repeat(f, *args):
    """
    Repeat when geth is not broadcasting (unaccounted error)
    """
    while True:
        try:
            return f(*args)
        except KeyError:
            continue


def main():
    if USE_STRATEGIES:
        web3.eth.setGasPriceStrategy(gas_strategy)
        web3.middleware_onion.add(middleware.time_based_cache_middleware)
        web3.middleware_onion.add(middleware.latest_block_based_cache_middleware)
        web3.middleware_onion.add(middleware.simple_cache_middleware)
        if POA:
            web3.middleware_onion.inject(middleware.geth_poa_middleware, layer=0)

    deployer = accounts.at(DEPLOYER)

    print("Deploying CRV token...")
    token = repeat(ERC20CRV.deploy, "Curve DAO Token", "CRV", 18, 10 ** 9, {'from': deployer})
    with open('token_crv.abi', 'w') as f:
        json.dump(token.abi, f)

    print("Deploying voting escrow...")
    escrow = repeat(VotingEscrow.deploy, token, {'from': deployer})
    with open('voting_escrow.abi', 'w') as f:
        json.dump(escrow.abi, f)

    print("Changing controller...")
    repeat(escrow.changeController, TOKEN_MANAGER, {'from': deployer})

    print("Sending coins...")
    for account in DISTRIBUTION_ADDRESSES:
        repeat(token.transfer, account, DISTRIBUTION_AMOUNT, {'from': deployer})
