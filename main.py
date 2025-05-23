import time
import os
import logging
import requests
import telegram
from requests.exceptions import RequestException

# Configuração do logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Variáveis de ambiente (segurança)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Inicializa o bot do Telegram
bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

# Guardar contratos já enviados
sent_tokens = set()

# Configuração da API
API_URL = "https://client-api-2-phi.vercel.app/api/trending"
HEADERS = {"User-Agent": "Mozilla/5.0"}
INTERVAL_SECONDS = 30  # Intervalo entre requisições
MAX_RETRIES = 3  # Número máximo de tentativas em caso de erro

def fetch_new_tokens():
    """Busca novos tokens e envia para o Telegram, com tratamento de erros."""
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(API_URL, headers=HEADERS, timeout=10)  # Timeout de 10s
            response.raise_for_status()  # Verifica erros HTTP
            data = response.json()

            for token in data:
                address = token.get("address")
                name = token.get("name")
                twitter = token.get("twitter")
                telegram_link = token.get("telegram")

                if not address or not name:
                    continue

                # Filtra os que têm Twitter e Telegram, e ainda não foram enviados
                if twitter and telegram_link and address not in sent_tokens:
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
            
            return  # Sai da função caso a requisição tenha sido bem-sucedida

        except RequestException as req_err:
            logging.warning(f"Tentativa {attempt + 1} falhou: {req_err}")
            time.sleep(5)  # Espera antes de tentar novamente
        except telegram.error.TelegramError as tg_err:
            logging.error(f"Erro no Telegram: {tg_err}")
            notify_admin(f"Erro no envio de mensagens: {tg_err}")
            break
        except Exception as e:
            logging.error(f"Erro inesperado: {e}")
            break

def notify_admin(error_msg):
    """Envia uma mensagem para o Telegram em caso de falha grave."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f"⚠️ Alerta: {error_msg}")
    except telegram.error.TelegramError as tg_err:
        logging.error(f"Erro ao notificar administrador: {tg_err}")

if __name__ == "__main__":
    logging.info("Bot iniciado...")
    while True:
        fetch_new_tokens()
        time.sleep(INTERVAL_SECONDS)
