"""Deploy DecisionLogger to HashKey Chain."""
import os
import json
from web3 import Web3
from solcx import compile_source, install_solc


def deploy():
    """Deploy DecisionLogger contract to HashKey Chain."""
    # Install solc compiler
    install_solc("0.8.20")

    # Read contract source
    contract_dir = os.path.dirname(__file__)
    with open(os.path.join(contract_dir, "DecisionLogger.sol")) as f:
        source = f.read()

    # Compile contract
    compiled = compile_source(
        source,
        output_values=["abi", "bin"],
        solc_version="0.8.20"
    )
    contract_id, contract_interface = compiled.popitem()
    abi = contract_interface["abi"]
    bytecode = contract_interface["bin"]

    # Connect to HashKey Chain
    rpc = os.getenv("HSK_RPC_URL")
    pk = os.getenv("HSK_PRIVATE_KEY")

    if not rpc:
        raise ValueError("HSK_RPC_URL not set in environment")
    if not pk:
        raise ValueError("HSK_PRIVATE_KEY not set in environment")

    w3 = Web3(Web3.HTTPProvider(rpc))
    if not w3.is_connected():
        raise ConnectionError(f"Failed to connect to {rpc}")

    account = w3.eth.account.from_key(pk)

    print(f"Deploying from account: {account.address}")
    print(f"Account balance: {w3.eth.get_balance(account.address) / 1e18} ETH")

    # Build deployment transaction
    Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    tx = Contract.constructor().build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gas": 500000,
        "gasPrice": w3.eth.gas_price,
    })

    # Sign and send transaction
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)

    print(f"Deployment tx sent: {tx_hash.hex()}")
    print("Waiting for receipt...")

    # Wait for transaction receipt
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    print(f"\n✅ DecisionLogger deployed at: {receipt.contractAddress}")
    print(f"   Tx hash: {tx_hash.hex()}")
    print(f"   Block number: {receipt.blockNumber}")
    print(f"   Gas used: {receipt.gasUsed}")

    # Save ABI + address for runtime use
    deployed_path = os.path.join(contract_dir, "deployed.json")
    with open(deployed_path, "w") as f:
        json.dump({
            "address": receipt.contractAddress,
            "abi": abi,
            "tx_hash": tx_hash.hex(),
            "block_number": receipt.blockNumber,
        }, f, indent=2)

    print(f"\n✅ Deployment info saved to {deployed_path}")


if __name__ == "__main__":
    deploy()
