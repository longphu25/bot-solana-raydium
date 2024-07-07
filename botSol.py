
import requests
import logging
import prettytable as pt
import locale

import os
from dotenv import load_dotenv

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# Load .env file
load_dotenv()
# Enable logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

locale.setlocale( locale.LC_ALL, 'en_US.UTF-8' )


url_api_raydium = "https://api-v3.raydium.io/pools/info/list"
pageSize = 10

params = {
    "poolType": "all",
    "poolSortField": "default",
    "sortType": "desc",
    "pageSize": pageSize,
    "page": 1
}

headers = {
    "accept": "application/json"
}

async def table_data(data) -> pt.PrettyTable:
    table = pt.PrettyTable(['Token Pair', 'Liquidity', '24h volume', '24h fee', '24h APR'])
    table.align['Token Pair'] = 'l'
    table.align['Liquidity'] = 'r'
    table.align['24h volume'] = 'r'
    table.align['24h fee'] = 'r'
    table.align['24h APR'] = 'r'
    for token_pair, liquidity, volume, fee, apr in data:
        table.add_row([ token_pair, liquidity, volume, fee, apr])
    return table

async def requests_data(poolType = 'all') -> dict:
    params['poolType'] = poolType
    response = requests.get(url_api_raydium, params=params, headers=headers)
    data_json = response.json()
    data = data_json['data']['data']
    table_data = []
    for i in range(pageSize):
        token_pair = data[i]['mintA']['symbol'] + " - " + data[i]['mintB']['symbol']
        liquidity = locale.currency(data[i]['tvl'], grouping=True )
        volume = locale.currency(data[i]['day']['volume'], grouping=True )
        fee = locale.currency(data[i]['day']['feeApr'], grouping=True )
        apr = locale.currency(data[i]['day']['apr'], grouping=True )
        table_data.append((token_pair, liquidity, volume, fee, apr))

    return table_data

# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
    )
    await update.message.reply_text('Welcome! Use /all_pools, /concentrated_pools, or /standard_pools to get information.')

async def all_pools(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = await requests_data()
    table = await table_data(data)
    await update.message.reply_text(f'<pre>{table}</pre>', parse_mode=ParseMode.HTML)

async def concentrated_pools(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: 
    data = await requests_data('concentrated')
    table = await table_data(data)
    await update.message.reply_text(f'<pre>{table}</pre>', parse_mode=ParseMode.HTML)

async def standard_pools(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: 
    data = await requests_data('standard')
    table = await table_data(data)
    await update.message.reply_text(f'<pre>{table}</pre>', parse_mode=ParseMode.HTML)

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("all_pools", all_pools))
    application.add_handler(CommandHandler("concentrated_pools", concentrated_pools))
    application.add_handler(CommandHandler("standard_pools", standard_pools))
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()