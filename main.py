import os
import time
import requests
import telegram
import logging

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

# Já enviados
sent_tokens = set()

# Configuração de logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

API_URL = "https://pump.fun/api/tokens"
INTERVAL = 30  # segundos

def fetch_tokens():
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Erro ao buscar tokens: {e}")
        return []

def process_tokens():
    tokens = fetch_tokens()

    for token in tokens:
        mint = token.get("id")
        name = token.get("name")
        symbol = token.get("symbol", "")
        twitter = token.get("twitter")
        telegram_link = token.get("telegram")
        website = token.get("website")

        if mint in sent_tokens:
            continue

        if twitter or telegram_link:
            message = (
                f"🚀 Novo token criado na Pump.fun!\n\n"
                f"🪙 Nome: {name} ({symbol})\n"
                f"📄 Mint: {mint}"
            )
            if twitter:
                message += f"\n🐦 Twitter: {twitter}"
            if telegram_link:
                message += f"\n💬 Telegram: {telegram_link}"
            if website:
                message += f"\n🌐 Website: {website}"

            bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
            sent_tokens.add(mint)
            logging.info(f"Token enviado: {name} ({mint})")

if __name__ == "__main__":
    logging.info("Bot iniciado...")
    while True:
        process_tokens()
        time.sleep(INTERVAL)
