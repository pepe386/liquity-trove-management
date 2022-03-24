# Script to monitor trove health based on user predefined parameters. If trove falls off the predefined limits, user is alerted.

import logging, os, sys, pickle
from enum import IntEnum
from dotenv import load_dotenv
from pushover import Pushover
from contracts import LiquityContracts

log_level = logging.INFO
base_dir = os.path.dirname(os.path.realpath(__file__))
load_dotenv(os.path.join(base_dir, '.env'))
infura_id = os.getenv('INFURA_ID')
pushover_user = os.getenv('PUSHOVER_USER')
pushover_token = os.getenv('PUSHOVER_TOKEN')
trove_address = os.getenv("ETH_ADDRESS")
min_collateral_ratio = float(os.getenv('MIN_COLLATERAL_RATIO'))
max_collateral_ratio = float(os.getenv('MAX_COLLATERAL_RATIO'))
eth_redemption_buffer = float(os.getenv('ETH_REDEMPTION_BUFFER'))
liquity_contracts = LiquityContracts()
Priority = IntEnum('Level', 'LOWEST LOW NORMAL HIGH EMERGENCY', start=-2)


def init_logging():
    logging.basicConfig(
        filename=os.path.join(base_dir, 'trove_management.log'),
        level=log_level,
        format=
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"
    )
    logger = logging.getLogger("trove_management")
    logger.setLevel(log_level)
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    logger.addHandler(ch)
    return logger


def send_notification(title, message, priority):
    try:
        po = Pushover(pushover_token)
        po.user(pushover_user)
        msg = po.msg(message)
        msg.set("title", title)
        msg.set("priority", priority)
        msg.set("expire", 3600)
        msg.set("retry", 600)
        po.send(msg)
        return True
    except:
        logger.error(
            "send_notification: Could not send pushover notification.")
        return False


def test_chainlink():
    try:
        if (liquity_contracts.PriceFeed.functions.status().call() != 0):
            logger.error(
                "Liquity protocol is not using Chainlink price aggregator for ETH price. Script is not checking trove's health status, consider monitoring your trove some other way."
            )
            return False
        decimals = liquity_contracts.ChainLink.functions.decimals().call()
        if (decimals != 8):
            logger.error(
                'Chainlink price aggregator changed its "decimals" parameter. Script is not checking trove\'s health status, consider monitoring your trove some other way.'
            )
            return False
        return True
    except:
        logger.error(
            "test_chainlink: error while querying ChainkLink price aggregator."
        )
        return False


def get_eth_price():
    try:
        return liquity_contracts.ChainLink.functions.latestAnswer().call()
    except:
        logger.error(
            "get_eth_price: Error querying ETH price from ChainLink price aggregator."
        )
        return -1


def get_icr(eth_price):
    try:
        return liquity_contracts.TroveManager.functions.getCurrentICR(
            trove_address, eth_price).call() / 100000000
    except:
        logger.error(
            "get_icr: Error querying trove ICR from TroveManager contact.")
        return -1


def get_trove_owners_count():
    try:
        return liquity_contracts.TroveManager.functions.getTroveOwnersCount(
        ).call()
    except:
        logger.error(
            "get_trove_owners_count: Error querying trove owners count from TroveManager contact."
        )
        return -1


def get_trove_list(trove_count):
    try:
        return liquity_contracts.MultiTroveGetter.functions.getMultipleSortedTroves(
            -1, trove_count).call()
    except:
        logger.error(
            "get_trove_list: Error querying trove list from MultiTroveGetter contract."
        )
        return None


def notify_trove_health(eth_price, trove_icr):
    send_notification(
        "Liquity Trove Management", "Trove Health Summary\n" + "ETH price: $" +
        str(round(eth_price / 100000000)) + "\nTrove Collateral Ratio: " +
        str(round(trove_icr * 100)) + "%", Priority.NORMAL.value)


def check_collateral_ratio(trove_icr):
    if trove_icr < min_collateral_ratio:
        send_notification(
            "Liquity Trove Management", "Your collateral ratio is below " +
            str(min_collateral_ratio * 100) + "%", Priority.HIGH.value)
        logger.info("check_collateral_ratio: collateral ratio is below " +
                    str(min_collateral_ratio * 100) + "%")
    if trove_icr > max_collateral_ratio:
        send_notification(
            "Liquity Trove Management", "Your collateral ratio is above " +
            str(max_collateral_ratio * 100) + "%", Priority.NORMAL.value)
        logger.info("check_collateral_ratio: collateral ratio is above " +
                    str(max_collateral_ratio * 100) + "%")


def check_redemption_risk(eth_price, trove_icr, trove_list):
    eth_sum = 0
    for trove in trove_list:
        coll_ratio = trove[2] * eth_price / 100000000 / trove[1]
        if coll_ratio > trove_icr:
            break
        eth_sum += trove[2]
    if (eth_sum / 1000000000000000000) < eth_redemption_buffer:
        send_notification(
            "Liquity Trove Management",
            "Your trove is at risk of getting redeemed. The troves ahead for redemption have a collateral of "
            + str(round(eth_sum / 1000000000000000000)) + " ETH",
            Priority.HIGH.value)
        logger.info(
            "check_redemption_risk: Your trove is at risk of getting redeemed. The troves ahead for redemption have a collateral of "
            + str(round(eth_sum / 1000000000000000000)) + " ETH")


def get_trove_local():
    trove_data = None
    try:
        with open(os.path.join(base_dir, ".trove"), 'rb') as fp:
            trove_data = pickle.load(fp)
    except FileNotFoundError:
        with open(os.path.join(base_dir, ".trove"), 'wb') as fp:
            pickle.dump(trove_data, fp)
    return trove_data


def save_trove_local(trove_data):
    with open(os.path.join(base_dir, ".trove"), 'wb') as fp:
        pickle.dump(trove_data, fp)


def check_debt_coll(trove_list):
    trove_data = get_trove_local()
    for i, trove in enumerate(trove_list):
        if trove[0] == trove_address and trove_data != None:
            if trove_list[i][1] != trove_data[1] or trove_list[i][
                    2] != trove_data[2]:
                logger.info("Trove's debt and/or collateral were modified.")
                send_notification(
                    "Liquity Trove Management",
                    "Your trove's debt and/or collateral were modified",
                    Priority.HIGH.value)
            trove_data = trove_list[i]
            save_trove_local(trove_data)


logger = init_logging()
logger.info(
    "<--------------- Starting routine to monitor trove health -------------->"
)
logger.debug("File directory: " + base_dir)
logger.debug("INFURA_ID: " + infura_id)
logger.debug("PUSHOVER_USER: " + pushover_user)
logger.debug("PUSHOVER_TOKEN: " + pushover_token)
logger.info("Trove address: " + trove_address)
logger.info("ETH_REDEMPTION_BUFFER: " + str(round(eth_redemption_buffer)))
logger.info("MIN_COLLATERAL_RATIO: " + str(round(min_collateral_ratio * 100)) +
            "%")
logger.info("MAX_COLLATERAL_RATIO: " + str(round(max_collateral_ratio * 100)) +
            "%")

if (test_chainlink() == False):
    logger.debug("test_chainlink error")
    exit()

eth_price = get_eth_price()
if eth_price == -1:
    logger.debug("get_eth_price error")
    exit()
logger.info("ETH price: " + str(eth_price / 100000000))

trove_icr = get_icr(eth_price)
if trove_icr == -1:
    exit()
logger.info("Trove Collateral Ratio: " + str(round(trove_icr * 100)) + "%")

if "--force-notification" in sys.argv:
    notify_trove_health(eth_price, trove_icr)

# check if trove's collateral ratio is between predefined limits
check_collateral_ratio(trove_icr)

trove_count = get_trove_owners_count()
if trove_count == -1:
    exit()
logger.debug("Trove count: " + str(trove_count))

trove_list = get_trove_list(trove_count)
# logger.debug("First trove collateral: " + str(trove_list[0][2]))
# logger.debug("First trove debt: " + str(trove_list[0][1]))

# check if trove is at risk of getting redeemed
check_redemption_risk(eth_price, trove_icr, trove_list)

# check if trove's debt or collateral has been updated
check_debt_coll(trove_list)

logger.info(
    "<--------- Succesfully finished routine to check trove health. -------->")
