import asyncio
import json
import logging
import os
import telegram
import websockets

# Configuração do logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

# Guardar tokens já enviados
sent_tokens = set()

async def listen_pump_ws():
    url = "wss://pump.fun/ws"
    async with websockets.connect(url) as ws:
        logging.info("Conectado ao WebSocket da Pump.fun")

        while True:
            try:
                raw = await ws.recv()
                data = json.loads(raw)

                # Processa apenas novos tokens
                if isinstance(data, dict) and data.get("type") == "newToken":
                    token_data = data.get("data", {})
                    name = token_data.get("name")
                    symbol = token_data.get("symbol")
                    twitter = token_data.get("twitter")
                    telegram_link = token_data.get("telegram")
                    website = token_data.get("website")
                    mint = token_data.get("mint")

                    # Verifica se tem Twitter ou Telegram e se ainda não foi enviado
                    if (twitter or telegram_link) and mint and mint not in sent_tokens:
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

                        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
                        sent_tokens.add(mint)
                        logging.info(f"Token enviado: {name} ({mint})")

            except Exception as e:
                logging.error(f"Erro no WebSocket: {e}")
                await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(listen_pump_ws())
