import requests
import json
import base64
import os
from pathlib import Path

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

# Pasta para salvar boundaries
BOUNDARIES_FOLDER = "boundaries_cidades"
CITIES_FILE = "cities_data.json"

# ==========================================
# FUNÇÕES
# ==========================================

def criar_pasta_boundaries():
    """Cria pasta para salvar boundaries"""
    Path(BOUNDARIES_FOLDER).mkdir(exist_ok=True)
    print(f"📁 Pasta criada/verificada: {BOUNDARIES_FOLDER}/")

def buscar_cidades():
    """Busca todas as cidades"""
    if Path(CITIES_FILE).exists():
        print(f"📁 Carregando cidades de {CITIES_FILE}...")
        with open(CITIES_FILE, "r", encoding="utf-8") as f:
            cidades = json.load(f)
        print(f"✓ {len(cidades)} cidades carregadas")
        return cidades
    
    print("🌍 Buscando cidades da API...")
    url = f"{BASE_URL}/cities"
    response = requests.get(url, headers=HEADERS, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        cidades = data.get("cities", [])
        
        with open(CITIES_FILE, "w", encoding="utf-8") as f:
            json.dump(cidades, f, ensure_ascii=False, indent=2)
        
        print(f"✓ {len(cidades)} cidades encontradas")
        return cidades
    
    return []

def buscar_neighborhoods_cidade(city_id, city_name):
    """Busca neighborhoods de uma cidade"""
    url = f"{BASE_URL}/neighborhoods"
    params = {"cityId": city_id}
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            neighborhoods = data.get("results", [])
            return neighborhoods
        
        return []
    
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return []

def salvar_boundaries_cidade(cidade):
    """Salva boundaries de uma cidade em arquivo JSON"""
    city_id = cidade.get("id")
    city_name = cidade.get("name", f"cidade_{city_id}")
    
    # Nome do arquivo (remove caracteres especiais)
    filename = city_name.lower().replace(" ", "_").replace("-", "_")
    filename = "".join(c for c in filename if c.isalnum() or c == "_")
    filepath = Path(BOUNDARIES_FOLDER) / f"boundaries_{filename}.json"
    
    # Se já existe, pula
    if filepath.exists():
        print(f"   ⏭️  Já existe, pulando")
        return True
    
    print(f"   🔍 Buscando neighborhoods...", end=" ")
    
    neighborhoods = buscar_neighborhoods_cidade(city_id, city_name)
    
    if not neighborhoods:
        print("❌ Nenhum bairro encontrado")
        return False
    
    # Filtra apenas neighborhoods com boundaries
    neighborhoods_validos = []
    for n in neighborhoods:
        if n.get("boundaries"):
            neighborhoods_validos.append({
                "id": n.get("id"),
                "name": n.get("name"),
                "boundaries": n.get("boundaries")
            })
    
    print(f"✓ {len(neighborhoods_validos)} bairros com boundaries")
    
    # Salva arquivo
    data_salvar = {
        "city_id": city_id,
        "city_name": city_name,
        "total_neighborhoods": len(neighborhoods_validos),
        "neighborhoods": neighborhoods_validos
    }
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data_salvar, f, ensure_ascii=False, indent=2)
    
    print(f"   💾 Salvo em: {filepath.name}")
    
    return True

# ==========================================
# MAIN
# ==========================================

def main():
    print("="*80)
    print("💾 SALVAR BOUNDARIES DE TODAS AS CIDADES".center(80))
    print("="*80)
    
    # Cria pasta
    criar_pasta_boundaries()
    
    # Busca cidades
    cidades = buscar_cidades()
    
    if not cidades:
        print("\n❌ Nenhuma cidade encontrada")
        return
    
    print(f"\n📋 Total de cidades: {len(cidades)}\n")
    
    sucessos = 0
    erros = 0
    pulados = 0
    
    for i, cidade in enumerate(cidades, 1):
        city_name = cidade.get("name", f"Cidade {cidade.get('id')}")
        
        print(f"[{i}/{len(cidades)}] 🌆 {city_name}")
        
        resultado = salvar_boundaries_cidade(cidade)
        
        if resultado is True:
            sucessos += 1
        elif resultado is False:
            erros += 1
        else:
            pulados += 1
    
    # Resumo
    print(f"\n{'='*80}")
    print("✅ PROCESSO CONCLUÍDO")
    print(f"{'='*80}")
    print(f"   ✓ Salvos com sucesso: {sucessos}")
    print(f"   ⏭️  Já existiam: {pulados}")
    print(f"   ❌ Erros: {erros}")
    print(f"\n📁 Arquivos salvos em: {BOUNDARIES_FOLDER}/")
    print(f"\n💡 Agora execute: python 2_buscar_construcoes.py")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interrompido")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()