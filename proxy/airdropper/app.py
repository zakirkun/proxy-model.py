import os
from logged_groups import logged_group
from solana.publickey import PublicKey

from ..environment import EVM_LOADER_ID, SOLANA_URL
from ..common_neon.neon_app import NeonApp, INeonAppImpl

from .airdropper import Airdropper


@logged_group("neon.Airdropper")
class AirdropperApp(NeonApp, INeonAppImpl):

    def __init__(self):
        pyth_mapping_account = PublicKey(os.environ['PYTH_MAPPING_ACCOUNT'])
        faucet_url = os.environ['FAUCET_URL']
        wrapper_whitelist = os.environ['INDEXER_ERC20_WRAPPER_WHITELIST']
        if wrapper_whitelist != 'ANY':
            wrapper_whitelist = wrapper_whitelist.split(',')
        neon_decimals = int(os.environ.get('NEON_DECIMALS', '9'))

        pp_solana_url = os.environ.get('PP_SOLANA_URL', None)
        max_conf = float(os.environ.get('MAX_CONFIDENCE_INTERVAL', 0.02))

        self.info(f"""Construct Airdropper with params:
                  solana_url: {SOLANA_URL},
                  evm_loader_id: {EVM_LOADER_ID},
                  pyth.network mapping account: {pyth_mapping_account},
                  faucet_url: {faucet_url},
                  wrapper_whitelist: {wrapper_whitelist},
                  NEON decimals: {neon_decimals},
                  Price provider solana: {pp_solana_url},
                  Max confidence interval: {max_conf}""")

        self._airdropper = Airdropper(SOLANA_URL, pyth_mapping_account, faucet_url, wrapper_whitelist, neon_decimals,
                                      pp_solana_url, max_conf)

    def run_impl(self):
        self._airdropper.run()
