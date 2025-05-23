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

# Configuração da API (Pump.fun - Solana)
GRAPHQL_API_URL = "https://graphql.bitquery.io"
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0"
}

GRAPHQL_QUERY = {
    "query": """
    subscription {
      Solana {
        TokenSupplyUpdates(
          where: {Instruction: {Program: {Address: {is: "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"}, Method: {is: "create"}}}}
        ) {
          Block{
            Time
          }
          Transaction{
            Signer
          }
          TokenSupplyUpdate {
            Amount
            Currency {
              Symbol
              Name
              MintAddress
              MetadataAddress
            }
            PostBalance
          }
        }
      }
    }
    """
}

INTERVAL_SECONDS = 30  # Intervalo entre requisições
MAX_RETRIES = 3  # Número máximo de tentativas em caso de erro

def fetch_new_tokens():
    """Busca novos tokens via GraphQL e envia para o Telegram."""
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(GRAPHQL_API_URL, json=GRAPHQL_QUERY, headers=HEADERS, timeout=10)
            response.raise_for_status()  # Verifica erros HTTP
            data = response.json()

            # Extraindo informações dos tokens
            tokens = data.get("data", {}).get("Solana", {}).get("TokenSupplyUpdates", [])
            
            if not tokens:
                logging.warning("Nenhum token encontrado.")
                return
            
            for token in tokens:
                currency = token.get("TokenSupplyUpdate", {}).get("Currency", {})
                name = currency.get("Name")
                symbol = currency.get("Symbol")
                mint_address = currency.get("MintAddress")
                metadata_address = currency.get("MetadataAddress")
                post_balance = token.get("TokenSupplyUpdate", {}).get("PostBalance")

                if not name or not mint_address:
                    continue

                if mint_address not in sent_tokens:
                    message = (
                        f"🚀 Novo token Pump.fun criado!\n\n"
                        f"🪙 Nome: {name} ({symbol})\n"
                        f"📄 Mint Address: {mint_address}\n"
                        f"📝 Metadata Address: {metadata_address}\n"
                        f"💰 Suprimento Atual: {post_balance}"
                    )
                    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
                    sent_tokens.add(mint_address)
                    logging.info(f"Token enviado: {name} ({mint_address})")

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
