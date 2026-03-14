import requests
import json
import base64

# Importa credenciais
try:
    from token_autenticacao import SECRET_KEY
except ImportError:
    print("❌ ERRO: Arquivo token_autenticacao.py não encontrado!")
    exit(1)

# ==========================================
# CONFIGURAÇÕES
# ==========================================

APP_ID = "207"
BASE_URL = "https://api.prod.upland.me/developers-api"

# Gera Basic Auth
credentials = f"{APP_ID}:{SECRET_KEY}"
auth_token = base64.b64encode(credentials.encode()).decode()

HEADERS = {
    "Authorization": f"Basic {auth_token}",
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# ID da propriedade que você sabe que está à venda
# (a que você mandou: 999.999 UPX)
PROP_ID = 80277672908070

print("="*80)
print("🔍 DEBUG - PREÇO DE VENDA")
print("="*80)

print(f"\nBuscando propriedade {PROP_ID}...")

# USA O ENDPOINT PÚBLICO (sem /developers-api)
url = f"https://api.prod.upland.me/api/properties/{PROP_ID}"

# Headers SEM autenticação
headers_publico = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

response = requests.get(url, headers=headers_publico, timeout=10)

if response.status_code == 200:
    detalhes = response.json()
    
    print(f"\n✅ Propriedade encontrada!")
    print(f"   Endereço: {detalhes.get('full_address')}")
    print(f"   Status: {detalhes.get('status')}")
    
    # Mostra on_market
    print(f"\n📊 CAMPO 'on_market':")
    on_market = detalhes.get("on_market")
    
    if on_market:
        print(f"   Tipo: {type(on_market)}")
        print(f"   Conteúdo:")
        print(json.dumps(on_market, indent=4))
    else:
        print("   ❌ Campo 'on_market' não existe ou é None")
    
    # Mostra price
    print(f"\n💰 CAMPO 'price':")
    price = detalhes.get("price")
    print(f"   Valor: {price}")
    print(f"   Tipo: {type(price)}")
    
    # Testa extração
    print(f"\n🧪 TESTANDO EXTRAÇÃO:")
    
    if on_market and isinstance(on_market, dict):
        currency = on_market.get("currency")
        token = on_market.get("token")
        fiat = on_market.get("fiat")
        
        print(f"   Currency: {currency}")
        print(f"   Token: {token} (tipo: {type(token)})")
        print(f"   Fiat: {fiat} (tipo: {type(fiat)})")
        
        if currency == "UPX" and token:
            try:
                preco_str = str(token).replace(" UPX", "").strip()
                print(f"\n   String processada: '{preco_str}'")
                preco = float(preco_str)
                print(f"   ✅ Preço extraído: {preco}")
            except Exception as e:
                print(f"   ❌ Erro ao converter: {e}")
    
    # Salva JSON completo
    with open("debug_propriedade.json", "w", encoding="utf-8") as f:
        json.dump(detalhes, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 JSON completo salvo em: debug_propriedade.json")

else:
    print(f"❌ Erro {response.status_code}")
    print(response.text)

print("\n" + "="*80)