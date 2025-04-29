import asyncio
import aiohttp
from datetime import datetime, timedelta
from collections import defaultdict

ALL_PAIRS_URL = "https://dlmm-api.meteora.ag/pair/all"
tracked_tokens = {}


async def fetch_all_pools(session):
    """Obtém dados das pools da API"""
    try:
        async with session.get(ALL_PAIRS_URL, timeout=10) as response:
            if response.status == 200:
                return await response.json()
            print(f"Erro HTTP: {response.status}")
            return None
    except aiohttp.ClientError as e:
        print(f"Erro de conexão: {str(e)}")
        return None


def get_token_metrics(pools):
    """Calcula métricas dos tokens"""
    token_data = defaultdict(lambda: {
        "volume": 0.0,
        "first_seen": datetime.now(),
        "pools": [],
        "liquidity": 0.0,
        "latest_price": None
    })

    for pool in pools:
        try:
            vol = float(pool.get("cumulative_trade_volume", 0))
            liq = float(pool.get("liquidity", 0)) if pool.get(
                "liquidity") else 0.0
            price = float(pool.get("current_price", 0))

            for mint in [pool.get("mint_x"), pool.get("mint_y")]:
                if not mint:
                    continue
                token_data[mint]["volume"] += vol
                token_data[mint]["liquidity"] += liq
                token_data[mint]["pools"].append(pool.get("address"))
                if token_data[mint]["latest_price"] is None:
                    token_data[mint]["latest_price"] = price

        except (TypeError, ValueError) as e:
            print(f"Erro ao processar pool: {str(e)}")
            continue

    return token_data


async def check_new_tokens():
    """Detecta novos tokens"""
    async with aiohttp.ClientSession() as session:
        pools = await fetch_all_pools(session)
        if not pools:
            return []

        current_tokens = get_token_metrics(pools)
        alerts = []
        now = datetime.now()

        # Limpa tokens antigos
        expired = [mint for mint, data in tracked_tokens.items()
                   if now - data["start_time"] > timedelta(minutes=30)]
        for mint in expired:
            del tracked_tokens[mint]

        for mint, data in current_tokens.items():
            if not mint:
                continue

            if mint not in tracked_tokens:
                tracked_tokens[mint] = {
                    "initial_volume": data["volume"],
                    "start_time": now,
                    "alerted": False
                }
                alerts.append({
                    "mint": mint,
                    "volume": data["volume"],
                    "pools": len(data["pools"]),
                    "liquidity": data["liquidity"],
                    "price": data["latest_price"]
                })
        return alerts


async def monitor():
    """Loop principal de monitoramento"""
    while True:
        try:
            alerts = await check_new_tokens()
            if alerts:
                print("\n🚨 ** NOVO TOKEN DETECTADO **")
                for token in alerts:
                    print(f"► Contrato: {token['mint']}")
                    print(f"► Volume Total: ${token['volume']:,.2f}")
                    print(f"► Liquidez: ${token['liquidity']:,.2f}")
                    print(f"► Pools Relacionadas: {token['pools']}")
                    print(f"► Preço Atual: {token['price']}\n")
            else:
                print("\n✅ Nenhum novo token detectado\n")

            await asyncio.sleep(120)

        except Exception as e:
            print(f"Erro: {str(e)}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    try:
        asyncio.run(monitor())
    except KeyboardInterrupt:
        print("\nMonitoramento interrompido")
