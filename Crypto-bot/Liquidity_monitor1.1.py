import asyncio
import aiohttp
from datetime import datetime
from collections import defaultdict
from telethon.sync import TelegramClient
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# =========== CONFIGURAÇÕES ===========
ALL_PAIRS_URL = "https://dlmm-api.meteora.ag/pair/all"
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
TELEGRAM_BOT_USERNAME = os.getenv('TELEGRAM_BOT_USERNAME')

MIN_LIQUIDITY = 5000    # Mínimo de liquidez em dólares
MIN_VOLUME = 20000      # Mínimo de volume em dólares
MAX_LOOPS = 5           # Número máximo de loops em que a pool será monitorada
CHECK_INTERVAL = 60     # Segundos necessários para cada loop
# =====================================


class TokenMonitor:
    def __init__(self):
        self.historic_tokens = set()
        self.tracked_tokens = {}  # {mint: {expires_at_loop, best_liq, best_vol}}
        self.current_loop = 0

    async def send_contract(self, contract):
        try:
            async with TelegramClient('session_name', API_ID, API_HASH) as client:
                await client.send_message(TELEGRAM_BOT_USERNAME, contract)
                print(f"[TG] Contrato enviado: {contract}")
        except Exception as e:
            print(f"[ERRO Telegram] {str(e)}")

    async def fetch_pools(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(ALL_PAIRS_URL, timeout=10) as response:
                    return await response.json() if response.status == 200 else None
        except Exception as e:
            print(f"Erro na conexão: {str(e)}")
            return None

    def _process_pools(self, pools):
        current_tokens = set()
        metrics = defaultdict(lambda: {'volume': 0, 'liquidity': 0})

        for pool in pools or []:
            try:
                vol = float(pool.get('cumulative_trade_volume', 0))
                liq = float(pool.get('liquidity', 0)) or 0.0

                for mint in [pool.get('mint_x'), pool.get('mint_y')]:
                    if not mint:
                        continue

                    current_tokens.add(mint)
                    metrics[mint]['volume'] += vol
                    metrics[mint]['liquidity'] += liq

            except (TypeError, ValueError) as e:
                print(f"Erro processando pool: {str(e)}")

        return current_tokens, metrics

    async def _initial_load(self):
        print("⏳ Carregando tokens históricos...")
        pools = await self.fetch_pools()
        if pools:
            current_tokens, _ = self._process_pools(pools)
            self.historic_tokens = current_tokens
            print(f"✅ {len(self.historic_tokens)} tokens históricos carregados")

    async def check_tokens(self):
        pools = await self.fetch_pools()
        if not pools:
            return []

        current_tokens, metrics = self._process_pools(pools)
        new_listings = current_tokens - self.historic_tokens
        now_loop = self.current_loop

        # Adiciona novos tokens com expiração
        for mint in new_listings:
            if mint not in self.tracked_tokens:
                self.tracked_tokens[mint] = {
                    'expires_at_loop': now_loop + MAX_LOOPS,
                    'best_liq': metrics[mint]['liquidity'],
                    'best_vol': metrics[mint]['volume']
                }

        # Processa tokens rastreados
        alerts = []
        for mint, data in list(self.tracked_tokens.items()):
            # Atualiza métricas
            current_liq = metrics[mint]['liquidity']
            current_vol = metrics[mint]['volume']

            self.tracked_tokens[mint]['best_liq'] = max(
                data['best_liq'], current_liq)
            self.tracked_tokens[mint]['best_vol'] = max(
                data['best_vol'], current_vol)

            # Verifica critérios ou expiração
            if (data['best_liq'] >= MIN_LIQUIDITY and
                    data['best_vol'] >= MIN_VOLUME):

                alerts.append(mint)
                del self.tracked_tokens[mint]

            elif now_loop >= data['expires_at_loop']:
                print(f"⌛ Token expirado: {mint}")
                del self.tracked_tokens[mint]

        return alerts

    async def run(self):
        await self._initial_load()

        print("\n🚀 Monitoramento ativo com:")
        print(f"• Liquidez: ≥ ${MIN_LIQUIDITY:,.0f}")
        print(f"• Volume: ≥ ${MIN_VOLUME:,.0f}")
        print(f"• Tentativas: {MAX_LOOPS} loops\n")

        while True:
            try:
                self.current_loop += 1
                print(f"\n🔁 Loop {self.current_loop} iniciado")

                valid_tokens = await self.check_tokens()

                if valid_tokens:
                    print(f"🚨 {len(valid_tokens)} tokens validados:")
                    for mint in valid_tokens:
                        print(f"► {mint}")
                        # await self.send_contract(mint)
                else:
                    print(f"⏳ Nenhum novo token válido")

                print(f"📊 Tokens em monitoramento: {len(self.tracked_tokens)}")
                await asyncio.sleep(CHECK_INTERVAL)

            except Exception as e:
                print(f"Erro: {str(e)}")
                await asyncio.sleep(30)


if __name__ == "__main__":
    monitor = TokenMonitor()
    try:
        asyncio.run(monitor.run())
    except KeyboardInterrupt:
        print("\nMonitoramento interrompido")
