import requests
import json
import base64
import pandas as pd
from datetime import datetime
import time
import sys
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
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# ==========================================
# CONFIGURAÇÕES DA BUSCA
# ==========================================

# Tipos de construção para buscar
BUILDING_TYPES = [
    # "Large Factory I",
    # "Large Factory I max",
    # "Palácio da Luz (UGC Sao Paulo Winner)",
    # "Nursey"
    "High-Rise Residential Tower",
    # "Natural History Museum I"
]


# Apenas propriedades à venda?
ONLY_FOR_SALE = False  # False = mostra TODAS

# Pasta com boundaries salvos
BOUNDARIES_FOLDER = "boundaries_cidades"

# ⚠️ MODO DE BUSCA
# Opção 1: Buscar em TODAS as cidades
SEARCH_ALL_CITIES = True  # True = busca em todas

# Opção 2: Cidades específicas (se SEARCH_ALL_CITIES = False)
SPECIFIC_CITIES = [
    # "Washington",
    # "Rome",
    "Sao Paulo"
    # Adicione outras cidades aqui
]

# ==========================================
# FUNÇÕES
# ==========================================

def carregar_arquivos_boundaries():
    """Carrega todos os arquivos de boundaries"""
    pasta = Path(BOUNDARIES_FOLDER)
    
    if not pasta.exists():
        print(f"❌ Pasta {BOUNDARIES_FOLDER}/ não encontrada!")
        print(f"   Execute primeiro: python 1_salvar_boundaries.py")
        return []
    
    arquivos = list(pasta.glob("boundaries_*.json"))
    
    return arquivos

def filtrar_arquivos_por_cidades(arquivos, cidades_desejadas):
    """Filtra arquivos pelas cidades especificadas"""
    arquivos_filtrados = []
    
    for arquivo in arquivos:
        # Carrega arquivo para verificar nome da cidade
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            city_name = data.get("city_name")
            
            if city_name in cidades_desejadas:
                arquivos_filtrados.append(arquivo)
        
        except:
            continue
    
    return arquivos_filtrados

def buscar_construcoes_por_boundaries(boundaries):
    """Faz POST com boundaries"""
    url = f"{BASE_URL}/buildings"
    payload = {"boundaries": boundaries}
    
    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=60)
        
        if response.status_code in [200, 201]:
            data = response.json()
            return data.get("buildings", [])
        
        return []
    
    except:
        return []

def filtrar_construcoes(construcoes, building_types):
    """Filtra construções pelos tipos especificados"""
    filtradas = []
    
    for construcao in construcoes:
        building_name = construcao.get("name")
        
        if building_name:
            if any(tipo.lower() in building_name.lower() for tipo in building_types):
                filtradas.append(construcao)
    
    return filtradas

def buscar_detalhes_propriedade(prop_id):
    """Busca detalhes completos de uma propriedade (2 endpoints)"""
    
    # ENDPOINT 1: /api/properties/ (público, tem on_market com preço)
    url_publico = f"https://api.prod.upland.me/api/properties/{prop_id}"
    headers_publico = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    # ENDPOINT 2: /developers-api/properties/ (autenticado, tem mintPrice)
    url_dev = f"{BASE_URL}/properties/{prop_id}"
    
    detalhes = {}
    
    try:
        # Busca dados do endpoint público (tem on_market)
        response1 = requests.get(url_publico, headers=headers_publico, timeout=10)
        
        if response1.status_code == 200:
            detalhes = response1.json()
        else:
            return None
        
        # Busca mintPrice do endpoint autenticado
        response2 = requests.get(url_dev, headers=HEADERS, timeout=10)
        
        if response2.status_code == 200:
            data_dev = response2.json()
            # Adiciona mintPrice ao detalhes
            detalhes["mintPrice"] = data_dev.get("mintPrice", 0)
        
        return detalhes
    
    except:
        return None

def extrair_preco_venda(detalhes):
    """Extrai preço de venda da propriedade (apenas se estiver à venda)"""
    
    # Verifica se está à venda
    status = detalhes.get("status", "").lower()
    
    if status not in ["for sale", "forsale"]:
        # NÃO está à venda, retorna 0
        return 0
    
    # Está à venda - tenta pegar do on_market
    on_market = detalhes.get("on_market")
    
    if on_market and isinstance(on_market, dict):
        # Verifica a moeda
        currency = on_market.get("currency", "UPX")
        
        if currency == "UPX":
            # Preço em UPX está em "token"
            token = on_market.get("token")
            if token:
                try:
                    # Remove " UPX" do final, mantém o ponto decimal
                    preco_str = str(token).replace(" UPX", "").strip()
                    preco = float(preco_str)
                    return preco
                except:
                    pass
        
        elif currency == "USD":
            # Preço em USD está em "fiat"
            fiat = on_market.get("fiat")
            if fiat:
                try:
                    # Remove " FIAT" do final
                    preco_str = str(fiat).replace(" FIAT", "").strip()
                    preco = float(preco_str)
                    # Multiplica por 1000 para converter USD em UPX equivalente
                    return preco * 1000
                except:
                    pass
    
    # Se não conseguiu extrair de on_market mas está "For sale", 
    # tenta campo price como fallback
    price = detalhes.get("price")
    if price:
        try:
            if isinstance(price, (int, float)):
                return float(price)
        except:
            pass
    
    return 0

def processar_resultados(propriedades_encontradas):
    """Processa e salva resultados em Excel"""
    
    print(f"\n📊 Processando {len(propriedades_encontradas)} propriedades...")
    
    resultados = []
    erros = 0
    
    for i, prop_data in enumerate(propriedades_encontradas, 1):
        prop_id = prop_data.get("propertyId")
        
        if not prop_id:
            erros += 1
            continue
        
        print(f"   [{i}/{len(propriedades_encontradas)}] {prop_id}...", end=" ")
        
        detalhes = buscar_detalhes_propriedade(prop_id)
        
        if detalhes:
            status = detalhes.get("status", "N/A")
            
            if ONLY_FOR_SALE and status.lower() not in ["for sale", "forsale"]:
                print("(não à venda)")
                continue
            
            building_name = prop_data.get("name", "N/A")
            preco_venda = extrair_preco_venda(detalhes)
            
            # Detecta moeda de venda
            on_market = detalhes.get("on_market", {})
            moeda_venda = on_market.get("currency", "N/A") if isinstance(on_market, dict) and on_market else "N/A"
            
            # Extrai endereço (pode ser "address" ou "full_address")
            endereco = detalhes.get("full_address") or detalhes.get("address") or "N/A"
            
            resultado = {
                "ID": prop_id,
                "Endereço": endereco,
                "Cidade": prop_data.get("_city_name", detalhes.get("city", {}).get("name", "N/A")),
                "Bairro": prop_data.get("_neighborhood_name", detalhes.get("neighborhood", {}).get("name", "N/A")),
                "Construção": building_name,
                "Status": status,
                "Moeda": moeda_venda,
                "Preço de Venda": preco_venda,
                "Mint Price (UPX)": detalhes.get("mintPrice", 0),
                "Dono": detalhes.get("owner_username", "N/A"),
                "Link": f"https://play.upland.me/?prop_id={prop_id}"
            }
            
            resultados.append(resultado)
            print("✓")
        else:
            print("✗")
            erros += 1
        
        time.sleep(0.3)
    
    if not resultados:
        print("\n😔 Nenhuma propriedade válida")
        return []
    
    # Salva Excel
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    script_dir = Path(__file__).parent
    filename = script_dir / f"construcoes_encontradas_{timestamp}.xlsx"
    filename_str = str(filename)
    
    df = pd.DataFrame(resultados)
    df = df.sort_values("Preço de Venda", ascending=True)
    
    with pd.ExcelWriter(filename_str, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Propriedades', index=False)
        
        worksheet = writer.sheets['Propriedades']
        
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
        
        for row in range(2, len(df) + 2):
            worksheet.cell(row=row, column=8).number_format = '#,##0'  # Preço Venda
            worksheet.cell(row=row, column=9).number_format = '#,##0'  # Mint Price
    
    print(f"\n✅ Resultados salvos em: {filename}")
    print(f"📊 Total: {len(resultados)} propriedades")
    
    if erros > 0:
        print(f"⚠️  Erros: {erros}")
    
    return resultados

# ==========================================
# MAIN
# ==========================================

def main():
    print("="*80)
    print("🏗️  BUSCA DE CONSTRUÇÕES - USANDO BOUNDARIES SALVOS".center(80))
    print("="*80)
    
    # Carrega arquivos de boundaries
    todos_arquivos = carregar_arquivos_boundaries()
    
    if not todos_arquivos:
        return
    
    print(f"\n📁 Total de arquivos disponíveis: {len(todos_arquivos)}")
    
    # Filtra por cidades se necessário
    if SEARCH_ALL_CITIES:
        arquivos = todos_arquivos
        print(f"🌍 Modo: TODAS AS CIDADES ({len(arquivos)} cidades)")
    else:
        print(f"🎯 Modo: CIDADES ESPECÍFICAS")
        print(f"   Cidades configuradas: {', '.join(SPECIFIC_CITIES)}")
        
        arquivos = filtrar_arquivos_por_cidades(todos_arquivos, SPECIFIC_CITIES)
        
        if not arquivos:
            print(f"\n❌ Nenhuma das cidades especificadas foi encontrada!")
            print(f"\nCidades disponíveis:")
            
            # Mostra cidades disponíveis
            cidades_disponiveis = []
            for arq in todos_arquivos[:20]:
                try:
                    with open(arq, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    cidades_disponiveis.append(data.get("city_name"))
                except:
                    pass
            
            for cidade in sorted(cidades_disponiveis):
                print(f"   • {cidade}")
            
            if len(todos_arquivos) > 20:
                print(f"   ... e mais {len(todos_arquivos) - 20}")
            
            return
        
        print(f"   ✓ {len(arquivos)} cidades selecionadas")
    
    print(f"\n🎯 Buscando por: {', '.join(BUILDING_TYPES)}")
    print(f"💰 Apenas à venda: {'Sim' if ONLY_FOR_SALE else 'Não'}\n")
    
    todas_propriedades = []
    tempo_inicio = time.time()
    
    # Processa cada arquivo (cidade)
    for i, arquivo in enumerate(arquivos, 1):
        print(f"[{i}/{len(arquivos)}] 📄 {arquivo.name}")
        
        # Carrega dados da cidade
        with open(arquivo, "r", encoding="utf-8") as f:
            data_cidade = json.load(f)
        
        city_name = data_cidade.get("city_name")
        neighborhoods = data_cidade.get("neighborhoods", [])
        
        print(f"   🌆 {city_name} - {len(neighborhoods)} bairros")
        
        construcoes_cidade = 0
        
        # Processa cada bairro
        for j, neigh in enumerate(neighborhoods, 1):
            neigh_name = neigh.get("name")
            boundaries = neigh.get("boundaries")
            
            if not boundaries:
                continue
            
            print(f"   [{j}/{len(neighborhoods)}] {neigh_name}...", end=" ")
            sys.stdout.flush()
            
            # Busca construções
            construcoes = buscar_construcoes_por_boundaries(boundaries)
            
            if not construcoes:
                print()
                continue
            
            # Filtra por tipo
            filtradas = filtrar_construcoes(construcoes, BUILDING_TYPES)
            
            if filtradas:
                print(f"✓ {len(filtradas)}")
                construcoes_cidade += len(filtradas)
                
                for prop in filtradas:
                    prop["_city_name"] = city_name
                    prop["_neighborhood_name"] = neigh_name
                
                todas_propriedades.extend(filtradas)
            else:
                print()
            
            time.sleep(0.5)
        
        if construcoes_cidade > 0:
            print(f"   🎯 Total em {city_name}: {construcoes_cidade}\n")
        
        time.sleep(1)
    
    # Processa resultados
    tempo_decorrido = time.time() - tempo_inicio
    
    print(f"{'='*80}")
    print(f"🎉 BUSCA CONCLUÍDA EM {tempo_decorrido/60:.1f} MINUTOS!")
    print(f"{'='*80}")
    
    if todas_propriedades:
        print(f"Total encontrado: {len(todas_propriedades)} propriedades\n")
        processar_resultados(todas_propriedades)
    else:
        print("😔 Nenhuma propriedade encontrada")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interrompido")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()