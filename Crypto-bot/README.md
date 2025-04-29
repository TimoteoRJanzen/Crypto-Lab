# Monitor de Liquidez e Compra de Tokens na Rede Solana

Este projeto consiste em um conjunto de scripts para monitorar e interagir com tokens na rede Solana, com foco em detectar novos tokens com boa liquidez e volume.

## Versões do Monitor

### Liquidity_monitor1.0.py
- Versão simplificada do monitor.
- Foca apenas no monitoramento de novos tokens.
- Exibe informações no terminal.

### Liquidity_monitor1.1.py
- Adiciona sistema de loops para monitoramento.
- Implementa expiração de tokens monitorados.
- Melhora o sistema de métricas.
- Exibe mais informações nos logs.

### Liquidity_monitor1.2.py
- Versão mais recente e estável.
- Implementa sistema de métricas mais robusto.
- Melhor visualização dos dados no terminal.
- Monitoramento mais eficiente.
- Melhor gestão de recursos.

---

### 📋 Configuração do Telegram

#### 1. **Criar uma aplicação no Telegram**
1. Acesse: [https://my.telegram.org/apps](https://my.telegram.org/apps)
2. Faça login com sua conta.
3. Preencha:
   - **App title:** Nome do seu bot (ex: `Crypto Monitor Bot`)
   - **Short name:** Identificador curto (ex: `crypto_monitor`)
4. Clique em **Create Application**.
5. Anote o `API_ID` e o `API_HASH`.

---

#### 2. **Preparar o bot do Telegram**
1. Abra o @solana_trojanbot no Telegram.
2. Crie sua carteira e guarde sua frase secreta.
3. Clique em **Settings**.
4. Clique em **Auto Buy**.
5. Configure o valor em **Buy Amount**.
6. Clique em **Off** para ativar o recurso (**ON**).

---

### ⚙️ Configurações Necessárias

1. Instale as dependências:
```bash
pip install -r requirements.txt
```

2. Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:
```ini
# Credenciais da API do Telegram
TELEGRAM_API_ID=your_api_id_here
TELEGRAM_API_HASH=your_api_hash_here
TELEGRAM_BOT_USERNAME=@solana_trojanbot
```

3. Execute o monitor desejado:
```bash
python Liquidity_monitor1.2.py
```

4. **Primeira execução**
Ao executar o bot pela primeira vez, será solicitado o login:
```bash
Insira seu número de telefone (incluindo o código do país): +5511999999999
Insira o código recebido no Telegram: 12345
```
Se aplicável, autorize o login digitando sua senha 2FA.

---

## 🚀 Funcionamento

- Monitoramento em tempo real de novas pools de liquidez adicionadas na Meteora.
- Cada nova pool entra em um ciclo de 5 loops (por padrão de 1 minuto cada).
- Em cada ciclo, são aplicados filtros de volume e liquidez.
- Se durante o ciclo a pool atingir os critérios mínimos de volume e liquidez, o contrato é enviado para o bot do Telegram.
- O bot realiza automaticamente a compra da quantidade configurada pelo usuário.

---

## ✅ Requisitos

- Python 3.7+
- Conta no Telegram
- Carteira Solana
- Acesso à API da Meteora
- Acesso à API da Jupiter

---

## 🔐 Segurança

- Nunca compartilhe seu arquivo `.env`.
- Mantenha suas chaves privadas em segurança.
- Use valores conservadores nas compras automáticas.
- Monitore regularmente as transações.

---

## 🤝 Contribuição

Sinta-se à vontade para contribuir com o projeto via pull requests ou reportando issues.

---
