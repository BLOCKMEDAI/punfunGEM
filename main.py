import asyncio
import os
import logging
import json
import websockets
import telegram

# Configuração do logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Variáveis de ambiente (segurança)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Inicializa o bot do Telegram
bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

# Guardar contratos já enviados
sent_tokens = set()

# URL do WebSocket
WEBSOCKET_URL = "wss://pumpportal.fun/api/data"

async def subscribe_new_tokens():
    """Conecta ao WebSocket e recebe tokens recém-criados em tempo real."""
    async with websockets.connect(WEBSOCKET_URL) as websocket:
        # Enviar comando para assinar eventos de novos tokens
        payload = {"method": "subscribeNewToken"}
        await websocket.send(json.dumps(payload))
        logging.info("Assinado para receber novos tokens!")

        # Loop para processar mensagens recebidas
        async for message in websocket:
            data = json.loads(message)

            # Verifica se há informações de token
            token_info = data.get("token")
            if not token_info:
                continue

            name = token_info.get("name")
            address = token_info.get("address")
            twitter = token_info.get("twitter")
            telegram_link = token_info.get("telegram")

            if not name or not address:
                continue

            # Filtra tokens que ainda não foram enviados
            if address not in sent_tokens:
                message = (
                    f"🚀 Novo token lançado no Pump.fun!\n\n"
                    f"🪙 Nome: {name}\n"
                    f"📄 Contrato: {address}\n"
                    f"🐦 Twitter: {twitter}\n"
                    f"📢 Telegram: {telegram_link}"
                )
                bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
                sent_tokens.add(address)
                logging.info(f"Token enviado: {name} ({address})")

# Executar o WebSocket
if __name__ == "__main__":
    logging.info("Bot iniciado... Conectando ao WebSocket.")
    asyncio.get_event_loop().run_until_complete(subscribe_new_tokens())
