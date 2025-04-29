import asyncio
from datetime import datetime
import aiohttp
import os
from collections import defaultdict
from telethon import TelegramClient
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
        self.tracked_tokens = {}
        self.current_loop = 0
        self.tg_client = None

    def _clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    async def _log(self, message):
        print(message)

    async def send_contract(self, contract):
        try:
            await self.tg_client.send_message(TELEGRAM_BOT_USERNAME, contract)
            await self._log(f"[TG] Contrato enviado: {contract}")
        except Exception as e:
            await self._log(f"[ERRO Telegram] {str(e)}")

    async def fetch_pools(self):
        async with aiohttp.ClientSession() as session:
            for _ in range(3):
                try:
                    async with session.get(ALL_PAIRS_URL, timeout=10) as response:
                        if response.status == 200:
                            return await response.json()
                        await self._log(f"HTTP Error: {response.status}")
                except Exception as e:
                    await self._log(f"Erro na conexão: {str(e)}")
                await asyncio.sleep(5)
            return None

    def _process_pools(self, pools):
        current_tokens = set()
        metrics = defaultdict(
            lambda: {'volume': 0, 'liquidity': 0, 'pools': set(), 'price': 0})

        for pool in pools or []:
            try:
                vol = float(pool.get('trade_volume_24h', 0))
                liq = float(pool.get('liquidity', 0)) or 0.0
                price = float(pool.get('price', 0)) or 0.0

                for mint in [pool.get('mint_x'), pool.get('mint_y')]:
                    if not mint:
                        continue

                    current_tokens.add(mint)
                    metrics[mint]['volume'] += vol
                    metrics[mint]['liquidity'] += liq
                    metrics[mint]['pools'].add(pool.get('address'))
                    metrics[mint]['price'] = price

            except (TypeError, ValueError) as e:
                print(f"Erro processando pool: {str(e)}")

        return current_tokens, metrics

    async def _initial_load(self):
        await self._log("⏳ Carregando tokens históricos...")
        while True:
            pools = await self.fetch_pools()
            if pools:
                current_tokens, _ = self._process_pools(pools)
                self.historic_tokens = current_tokens
                await self._log(f"✅ {len(self.historic_tokens)} tokens históricos carregados")
                return
            await self._log("Falha ao carregar. Tentando novamente em 30s...")
            await asyncio.sleep(30)

    async def check_tokens(self):
        pools = await self.fetch_pools()
        if not pools:
            return []

        current_tokens, metrics = self._process_pools(pools)
        new_listings = current_tokens - self.historic_tokens
        now_loop = self.current_loop

        # Adiciona novos tokens
        for mint in new_listings:
            if mint not in self.tracked_tokens:
                self.tracked_tokens[mint] = {
                    'expires_at_loop': now_loop + MAX_LOOPS - 1,
                    'best_liq': metrics[mint]['liquidity'],
                    'best_vol': metrics[mint]['volume'],
                    'added_at': datetime.now().isoformat()
                }
                await self._log(f"🔍 Novo token em monitoramento: {mint}")

        alerts = []
        # Monitoramento detalhado
        await self._log("\n📊 Status dos Tokens Monitorados:")
        for mint, data in list(self.tracked_tokens.items()):
            current_liq = metrics[mint]['liquidity']
            current_vol = metrics[mint]['volume']
            remaining_loops = data['expires_at_loop'] - now_loop

            # Atualiza métricas
            data['best_liq'] = max(data['best_liq'], current_liq)
            data['best_vol'] = max(data['best_vol'], current_vol)

            # Exibe status detalhado
            status = [
                f"► Contrato: {mint}",
                f"├─ Liquidez Atual: ${current_liq:,.2f}",
                f"├─ Melhor Liquidez: ${data['best_liq']:,.2f}",
                f"├─ Volume Atual: ${current_vol:,.2f}",
                f"├─ Melhor Volume: ${data['best_vol']:,.2f}",
                f"├─ Nº de Pools: {len(metrics[mint]['pools'])}",
                f"└─ Loops Restantes: {remaining_loops}"
            ]
            await self._log('\n'.join(status))

            # Verifica critérios
            if data['best_liq'] >= MIN_LIQUIDITY and data['best_vol'] >= MIN_VOLUME:
                alerts.append(mint)
                del self.tracked_tokens[mint]
                self.historic_tokens.add(mint)
                await self._log("\n🚨🚨🚨 TOKEN VALIDADO! 🚨🚨🚨")

            elif now_loop >= data['expires_at_loop']:
                del self.tracked_tokens[mint]
                self.historic_tokens.add(mint)
                await self._log(f"⌛ Token expirado: {mint}")

        return alerts

    async def run(self):
        await self._initial_load()

        self.tg_client = TelegramClient('session_name', API_ID, API_HASH)
        await self.tg_client.start()

        await self._log("\n🚀 Monitoramento ativo com:")
        await self._log(f"• Liquidez: ≥ ${MIN_LIQUIDITY:,.0f}")
        await self._log(f"• Volume: ≥ ${MIN_VOLUME:,.0f}")
        await self._log(f"• Tentativas: {MAX_LOOPS} loops\n")

        try:
            while True:
                self._clear_terminal()
                self.current_loop += 1
                await self._log(f"\n🔁 Loop {self.current_loop} iniciado")
                await self._log(f"\n📈 Total monitorado: {len(self.tracked_tokens)} tokens")
                valid_tokens = await self.check_tokens()

                if valid_tokens:
                    await self._log(f"\n🚨 {len(valid_tokens)} tokens validados:")
                    for mint in valid_tokens:
                        await self.send_contract(mint)
                else:
                    await self._log("\n⏳ Nenhum novo token válido")

                await asyncio.sleep(CHECK_INTERVAL)

        except Exception as e:
            await self._log(f"Erro crítico: {str(e)}")
        finally:
            await self.tg_client.disconnect()


if __name__ == "__main__":
    monitor = TokenMonitor()
    try:
        asyncio.run(monitor.run())
    except KeyboardInterrupt:
        print("\nMonitoramento interrompido")
