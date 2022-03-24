import json, os
from dotenv import load_dotenv
from web3 import Web3


class LiquityContracts:
    __base_dir = os.path.dirname(os.path.realpath(__file__))
    load_dotenv(os.path.join(__base_dir, '.env'))
    __infura_id = os.getenv('INFURA_ID')
    __w3 = Web3(
        Web3.HTTPProvider("https://mainnet.infura.io/v3/" + __infura_id))

    with open(os.path.join(__base_dir, "abi/ChainLink.json")) as f:
        __ChainLinkAbi = json.load(f)
    ChainLink = __w3.eth.contract(
        address='0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419',
        abi=__ChainLinkAbi)

    with open(os.path.join(__base_dir, "abi/PriceFeed.json")) as f:
        __PriceFeedAbi = json.load(f)
    PriceFeed = __w3.eth.contract(
        address='0x4c517D4e2C851CA76d7eC94B805269Df0f2201De',
        abi=__PriceFeedAbi)

    with open(os.path.join(__base_dir, "abi/TroveManager.json")) as f:
        __TroveManagerAbi = json.load(f)
    TroveManager = __w3.eth.contract(
        address='0xA39739EF8b0231DbFA0DcdA07d7e29faAbCf4bb2',
        abi=__TroveManagerAbi)

    with open(os.path.join(__base_dir, "abi/MultiTroveGetter.json")) as f:
        __MultiTroveGetterAbi = json.load(f)
    MultiTroveGetter = __w3.eth.contract(
        address='0xFc92d0E9Fa35df17E3A6d9F40716ca2cE749922B',
        abi=__MultiTroveGetterAbi)
