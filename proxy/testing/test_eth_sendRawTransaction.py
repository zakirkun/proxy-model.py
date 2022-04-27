import unittest
import os
import json
import requests


import eth_utils
from web3 import Web3
from .testing_helpers import request_airdrop
from solcx import compile_source
from solana.rpc.api import Client as SolanaClient


EXTRA_GAS = int(os.environ.get("EXTRA_GAS", "0"))
proxy_url = os.environ.get('PROXY_URL', 'http://localhost:9090/solana')
solana_url = os.environ.get("SOLANA_URL", "http://127.0.0.1:8899")
proxy = Web3(Web3.HTTPProvider(proxy_url))
eth_account = proxy.eth.account.create('https://github.com/neonlabsorg/proxy-model.py/issues/147')
proxy.eth.default_account = eth_account.address

STORAGE_SOLIDITY_SOURCE_147 = '''
pragma solidity >=0.7.0 <0.9.0;
/**
 * @title Storage
 * @dev Store & retrieve value in a variable
 */
contract Storage {
    uint256 number;
    /**
     * @dev Store value in variable
     * @param num value to store
     */
    function store(uint256 num) public {
        number = num;
    }
    /**
     * @dev Return value
     * @return value of 'number'
     */
    function retrieve() public view returns (uint256){
        return number;
    }
}
'''

SOLIDITY_SOURCE_185 = '''
pragma solidity >=0.7.0 <0.9.0;

contract test_185 {
    bytes public emprty_string = "";

    function getKeccakOfEmptyString() public view returns (bytes32 variant) {
        variant = keccak256(emprty_string);
    }

    bytes32 constant neonlabsHash = keccak256("neonlabs");

    function endlessCycle() public view returns (bytes32 variant) {
        variant = keccak256(emprty_string);
        for(;neonlabsHash != variant;) {
            variant = keccak256(abi.encodePacked(variant));
        }
        return variant;
    }

    bytes32 public value = "";

    function initValue(string memory s) public {
        value = keccak256(bytes(s));
    }

    function calculateKeccakAndStore(uint256 times) public {
        for(;times > 0; --times) {
            value = keccak256(abi.encodePacked(value));
        }
    }

    function getValue() public view returns (bytes32) {
        return value;
    }

}
'''


class Test_eth_sendRawTransaction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        request_airdrop(eth_account.address, 100)
        cls.deploy_storage_147_solidity_contract(cls)
        cls.deploy_test_185_solidity_contract(cls)

    def deploy_storage_147_solidity_contract(self):
        compiled_sol = compile_source(STORAGE_SOLIDITY_SOURCE_147)
        contract_id, contract_interface = compiled_sol.popitem()
        storage = proxy.eth.contract(abi=contract_interface['abi'], bytecode=contract_interface['bin'])
        trx_deploy = proxy.eth.account.sign_transaction(dict(
            nonce=proxy.eth.get_transaction_count(proxy.eth.default_account),
            chainId=proxy.eth.chain_id,
            gas=987654321,
            gasPrice=2000000000,
            to='',
            value=0,
            data=storage.bytecode),
            eth_account.key
        )
        self.trx_deploy_hash = proxy.eth.send_raw_transaction(trx_deploy.rawTransaction)
        trx_deploy_receipt = proxy.eth.wait_for_transaction_receipt(self.trx_deploy_hash)

        self.deploy_block_hash = trx_deploy_receipt['blockHash']
        self.deploy_block_num = trx_deploy_receipt['blockNumber']

        self.storage_contract = proxy.eth.contract(
            address=trx_deploy_receipt.contractAddress,
            abi=storage.abi
        )

    def deploy_test_185_solidity_contract(self):
        compiled_sol = compile_source(SOLIDITY_SOURCE_185)
        contract_id, contract_interface = compiled_sol.popitem()
        test_185_solidity_contract = proxy.eth.contract(
            abi=contract_interface['abi'], bytecode=contract_interface['bin'])
        trx_deploy = proxy.eth.account.sign_transaction(dict(
            nonce=proxy.eth.get_transaction_count(proxy.eth.default_account),
            chainId=proxy.eth.chain_id,
            gas=987654321,
            gasPrice=1000000000,
            to='',
            value=0,
            data=test_185_solidity_contract.bytecode),
            eth_account.key
        )
        trx_deploy_hash = proxy.eth.send_raw_transaction(trx_deploy.rawTransaction)
        trx_deploy_receipt = proxy.eth.wait_for_transaction_receipt(trx_deploy_hash)

        self.test_185_solidity_contract = proxy.eth.contract(
            address=trx_deploy_receipt.contractAddress,
            abi=test_185_solidity_contract.abi
        )

    # @unittest.skip("a.i.")
    def test_06_transfer_one_and_a_half_gweis(self):
        eth_account_alice = proxy.eth.account.create('alice')
        eth_account_bob = proxy.eth.account.create('bob')
        request_airdrop(eth_account_alice.address)
        request_airdrop(eth_account_bob.address)
        if True:
            trx_transfer = proxy.eth.account.sign_transaction(dict(
                nonce=proxy.eth.get_transaction_count(proxy.eth.default_account),
                chainId=proxy.eth.chain_id,
                gas=987654321,
                gasPrice=1000000000,
                to=eth_account_alice.address,
                value=2 * eth_utils.denoms.gwei),
                eth_account.key
            )
            trx_transfer_hash = proxy.eth.send_raw_transaction(trx_transfer.rawTransaction)
            trx_transfer_receipt = proxy.eth.wait_for_transaction_receipt(trx_transfer_hash)
            trx_transfer = proxy.eth.account.sign_transaction(dict(
                nonce=proxy.eth.get_transaction_count(proxy.eth.default_account),
                chainId=proxy.eth.chain_id,
                gas=987654321,
                gasPrice=1000000000,
                to=eth_account_bob.address,
                value=2 * eth_utils.denoms.gwei),
                eth_account.key
            )
            trx_transfer_hash = proxy.eth.send_raw_transaction(trx_transfer.rawTransaction)
            trx_transfer_receipt = proxy.eth.wait_for_transaction_receipt(trx_transfer_hash)
        one_and_a_half_gweis = 1_500_000_000
        trx_transfer = proxy.eth.account.sign_transaction(dict(
            nonce=proxy.eth.get_transaction_count(eth_account_alice.address),
            chainId=proxy.eth.chain_id,
            gas=987654321,
            gasPrice=1000000000,
            to=eth_account_bob.address,
            value=one_and_a_half_gweis),
            eth_account_alice.key
        )
        trx_transfer_hash = proxy.eth.send_raw_transaction(trx_transfer.rawTransaction)
        _trx_transfer_receipt = proxy.eth.wait_for_transaction_receipt(trx_transfer_hash)

        response = requests.post(proxy_url, json={"jsonrpc":"2.0","method":"neon_getSolanaTransactionByNeonTransaction","params":[trx_transfer_hash.hex()],"id":123456789}).json()
        solana_client = SolanaClient(solana_url)
        receipt = solana_client.get_confirmed_transaction(response['result'][0])
        print(json.dumps(receipt, indent=3))


if __name__ == '__main__':
    unittest.main()
