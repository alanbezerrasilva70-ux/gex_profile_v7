import time
import os
import pandas as pd
import re
import math
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# ==============================================================================
# CONFIGURAÇÕES V9 - QUANT ENGINE (HEATMAP + TIME TRAVEL 1DTE/7DTE)
# ==============================================================================
PASTA_DADOS = "./GEX_Data" 
HEADLESS_MODE = True 

# 1. MULTIPLICADORES DE CONTRATOS FUTUROS REAIS
MULTIPLIADORES = {
    "ES": 50,    # S&P 500 = $50 por ponto
    "NQ": 20,    # Nasdaq = $20 por ponto
    "CL": 1000,  # Petróleo = 1000 barris
    "GC": 100,   # Ouro = 100 onças
    "ZB": 1000,  # T-Bond = ~$1000 por ponto inteiro
    "ZN": 1000,  # T-Note = ~$1000 por ponto inteiro
    "YM": 5,     # Dow Jones = $5 por ponto
    "RTY": 50,   # Russell 2000 = $50 por ponto
    "NG": 10000  # Gás Natural = 10.000 mmBtu
}

# ==============================================================================
# MOTOR MATEMÁTICO BLACK-SCHOLES
# ==============================================================================
def pdf(x):
    return math.exp(-x**2 / 2) / math.sqrt(2 * math.pi)

def black_scholes_gamma(S, K, T, r, sigma):
    try:
        if T <= 0 or sigma <= 0 or S <= 0: 
            return 0.0
        d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        gamma = pdf(d1) / (S * sigma * math.sqrt(T))
        return gamma
    except:
        return 0.0

# ==============================================================================
# INICIALIZAÇÃO DO NAVEGADOR
# ==============================================================================
def iniciar_driver():
    print("👻 Iniciando Driver V9 (Time Travel e Heatmap Ativados)...")
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    options = ChromeOptions()
    if HEADLESS_MODE:
        options.add_argument("--headless=new") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    try:
        driver = webdriver.Chrome(options=options)
        print("✅ Driver Cloud iniciado com sucesso!")
        return driver
    except Exception as e:
        print(f"❌ ERRO ao iniciar driver: {e}")
        return None 

# ==============================================================================
# FUNÇÕES DE LIMPEZA E FORMATAÇÃO
# ==============================================================================
def clean_float(val):
    s = str(val).replace(',', '').replace('N/A', '').strip()
    try: 
        return float(s)
    except: 
        return 0.0

def format_money(val):
    v = abs(val)
    s = "-" if val < 0 else ""
    if v >= 1e9: 
        return f"{s}${v/1e9:.2f}B"
    if v >= 1e6: 
        return f"{s}${v/1e6:.2f}M"
    return f"{s}${v:.0f}"

# ==============================================================================
# LEITURA DE PREÇO COM RESILIÊNCIA (ANTI-BLOQUEIO)
# ==============================================================================
def get_price(driver, symbol):
    selectors = ["span.last-change", "div.price-change", ".quote-price", ".symbol-last-price", ".last-price"]
    
    for attempt in range(3): 
        for sel in selectors:
            try:
                el = driver.find_element(By.CSS_SELECTOR, sel)
                txt = el.text.split()[0].strip()
                if txt and txt != "---": 
                    # Lógica especial para Frações de T-Bonds e T-Notes
                    if symbol in ["ZB","ZN"] and "-" in txt:
                        try: 
                            p = txt.split('-')
                            return float(p[0]) + (float(p[1])/32.0)
                        except: 
                            pass
                    else:
                        try: 
                            return float(txt.replace(',',''))
                        except: 
                            pass
            except:
                continue
        # Pausa para o site carregar antes de tentar de novo
        time.sleep(2) 
        
    return 0.0

# ==============================================================================
# 🟢 FUNÇÃO NOVA: TIME TRAVEL (Extrai as datas ocultas do Barchart)
# ==============================================================================
def extract_expiration_dates(driver):
    try:
        # Injeta um script JS para raspar todas as opções de data do menu "Expiration"
        script = "return Array.from(document.querySelectorAll('select option')).map(o => o.value).filter(v => v.includes('-'));"
        dates = driver.execute_script(script)
        # Remove duplicatas mas mantém a ordem cronológica
        return list(dict.fromkeys(dates)) 
    except Exception as e:
        print(f"Erro ao extrair datas: {e}")
        return []

# ==============================================================================
# MOTOR PRINCIPAL DE PROCESSAMENTO DA TABELA DE OPÇÕES
# ==============================================================================
def process(driver, symbol, url):
    print(f" 🔎 Lendo URL: {url[-35:]}...", end="")
    try:
        driver.get(url)
        time.sleep(5) 
        spot = get_price(driver, symbol)
        
        # Fallback de página pesada
        if spot == 0: 
            print(" ⚠️ Atraso detectado. Recarregando (F5)...")
            driver.refresh()
            time.sleep(6)
            spot = get_price(driver, symbol)
            if spot == 0:
                print(" ❌ Spot Zero. Abortando extração.")
                return None, None

        # Scroll para forçar o Barchart a renderizar a tabela HTML
        body = driver.find_element(By.TAG_NAME, "body")
        for _ in range(6):
            body.send_keys(Keys.PAGE_DOWN)
            time.sleep(0.3)
        
        page_text = driver.find_element(By.TAG_NAME, "body").text
        tokens = page_text.split()
        
        data = []
        margin = spot * 0.15 
        T_years = 1.0 / 365.0  
        risk_free = 0.05       
        
        # Volatilidade adaptada por ativo
        iv_avg = 0.14
        if symbol == "NQ": iv_avg = 0.18
        if symbol == "CL": iv_avg = 0.25
        if symbol == "YM": iv_avg = 0.12
        if symbol == "RTY": iv_avg = 0.20
        if symbol == "NG": iv_avg = 0.40
        
        mult = MULTIPLIADORES.get(symbol, 100)
        
        for i in range(5, len(tokens)-5):
            t = tokens[i].replace(',', '')
            if not re.match(r'^\d{1,5}(\.\d{1,4})?$', t): 
                continue
            
            try: 
                strike = float(t)
            except: 
                continue

            # Cortando as asas extremas (economiza processamento)
            if strike < (spot - margin) or strike > (spot + margin): 
                continue
            
            try:
                c_oi = clean_float(tokens[i-2])
                c_vol = clean_float(tokens[i-3])
                p_oi = clean_float(tokens[i+3])
                p_vol = clean_float(tokens[i+2])
                
                if c_oi == 0 and p_oi == 0 and c_vol == 0 and p_vol == 0: 
                    continue
                
                gamma_unit = black_scholes_gamma(spot, strike, T_years, risk_free, iv_avg)
                
                call_gex = c_oi * gamma_unit * mult * spot 
                put_gex = p_oi * gamma_unit * mult * spot
                net_gex_strike = call_gex - put_gex
              
                net_flow_strike = c_vol - p_vol
                total_vol = c_vol + p_vol
                total_oi = c_oi + p_oi 
                
                # 🟢 DADOS COMPLETOS PARA O HEATMAP
                data.append({
                    "strike": strike, 
                    "ng": net_gex_strike,
                    "nf": net_flow_strike,
                    "c_vol": c_vol, 
                    "p_vol": p_vol, 
                    "coi": c_oi, 
                    "poi": p_oi, 
                    "vol": total_vol,
                    "toi": total_oi
                })
            except: 
                continue
            
        if not data: 
            print(" ❌ Sem contratos abertos nesta faixa.")
            return None, None
        
        df = pd.DataFrame(data).drop_duplicates('strike').sort_values('strike')
        
        try:
            mp_idx = df['toi'].idxmax() if 'toi' in df.columns else df.index[0]
            max_pain = df.loc[mp_idx]['strike']
        except: 
            max_pain = spot

        try:
            cw = df.loc[df['ng'].idxmax()] 
            pw = df.loc[df['ng'].idxmin()] 
        except:
            cw = df.iloc[-1]
            pw = df.iloc[0]

        try:
            zg_idx = df['ng'].abs().idxmin()
            zero_gamma = df.loc[zg_idx]['strike']
        except:
            zero_gamma = spot

        dp = df.loc[df['vol'].idxmax()]
        
        tot_gex = df['ng'].sum()
        tot_flow = df['nf'].sum()
        
        if tot_gex > 0:
            regime = "LONG GAMMA (Estavel/Suporte)"
        else:
            regime = "SHORT GAMMA (Volatil/Squeeze)"
            
        res = {
            "CW": cw['strike'], "CWM": format_money(cw['ng']), 
            "PW": pw['strike'], "PWM": format_money(pw['ng']),
            "ZG": zero_gamma, 
            "PG": cw['strike'], 
            "NG": pw['strike'], 
            "DP": dp['strike'], "DPM": format_money(dp['vol']*spot*mult), 
            "MP": max_pain, 
            "Rat": f"{(abs(df['ng'][df['ng']<0].sum()) / df['ng'][df['ng']>0].sum() if df['ng'][df['ng']>0].sum() > 0 else 0):.2f}",
            "FlowSig": "Bull" if tot_flow > 0 else "Bear",
            "GexSig": "Bull" if tot_gex > 0 else "Bear",
            "FlowVal": format_money(tot_flow * spot * mult), 
            "GexVal": format_money(tot_gex), 
            "AlvoUp": f"{spot*1.005:.2f}",
            "AlvoDown": f"{spot*0.995:.2f}",
            "Regime": regime
        }
        
        print(f" ✅ ZG:{res['ZG']:.2f}")
        return res, df
        
    except Exception as e: 
        print(f" ❌ Erro processamento: {e}")
        return None, None

# ==============================================================================
# SALVAR ARQUIVOS COM SUPORTE AO SUFIXO (_1DTE, _7DTE)
# ==============================================================================
def save(sym, res, df, suffix=""):
    if not os.path.exists(PASTA_DADOS): 
        os.makedirs(PASTA_DADOS)
    if res:
        file_niveis = os.path.join(PASTA_DADOS, f"NiveisGamma_{sym}{suffix}.csv")
        with open(file_niveis, "w") as f:
            f.write(f"{res['CW']},{res['PW']},{res['ZG']:.2f},{res['PG']},{res['NG']},{res['CWM']},{res['PWM']},{res.get('CW_0DTE',0)},{res.get('PW_0DTE',0)}")
        
        file_alvos = os.path.join(PASTA_DADOS, f"AlvosVolatilidade_{sym}{suffix}.csv")
        with open(file_alvos, "w") as f:
            f.write(f"{res['MP']},{res['DP']},{res['Rat']},15.5,{res['FlowSig']},{res['GexSig']},{res['DPM']},{res['FlowVal']},{res['GexVal']},{res['AlvoUp']},{res['AlvoDown']},{res['Regime']}")
            
    if df is not None:
        file_profile = os.path.join(PASTA_DADOS, f"GammaProfile_{sym}{suffix}.csv")
        # 🟢 CRÍTICO: Exportando as 6 colunas necessárias para o Heatmap
        df.to_csv(file_profile, index=False, columns=['strike','ng','c_vol','p_vol','coi','poi'])

# ==============================================================================
# DROPBOX SYNC
# ==============================================================================
def upload_to_dropbox():
    import dropbox
    app_key = "4pne4yuoe5ozz7u"
    app_secret = os.environ.get("DBX_SECRET")
    refresh_token = os.environ.get("DBX_REFRESH")
    
    if not app_secret or not refresh_token:
        print("⚠️ Credenciais do Dropbox não encontradas.")
        return

    print("☁️ Conectando ao Dropbox...")
    try:
        dbx = dropbox.Dropbox(app_key=app_key, app_secret=app_secret, oauth2_refresh_token=refresh_token)
        files = os.listdir(PASTA_DADOS)
        for f in files:
            filepath = os.path.join(PASTA_DADOS, f)
            if os.path.isfile(filepath):
                with open(filepath, 'rb') as file_data:
                    dbx.files_upload(file_data.read(), f"/{f}", mode=dropbox.files.WriteMode.overwrite)
                    print(f"✅ Sincronizado: {f}")
    except Exception as e:
        print(f"❌ Erro no Dropbox: {e}")

# ==============================================================================
# MASTER PROCESSOR (AGREGAÇÃO + TIME TRAVEL)
# ==============================================================================
def process_group(driver, symbol, asset_list):
    print(f"\n🔄 INICIANDO MACRO: {symbol}...")
    time.sleep(4) 
    
    df_master = pd.DataFrame()
    spot_master = 0
    
    # --- PASSO 1: RASPAR TODOS OS VENCIMENTOS (MACRO) ---
    for asset in asset_list:
        res, df = process(driver, symbol, asset["url"]) 
        if df is not None and not df.empty:
            df['strike'] = df['strike'] * asset['strike_mult']
            df['strike'] = (df['strike'] / 5).round() * 5
            for col in ['ng', 'nf', 'c_vol', 'p_vol', 'coi', 'poi']:
                df[col] = df[col] * asset['gex_correcao']
            
            df_master = pd.concat([df_master, df], ignore_index=True)
            
            if spot_master == 0:
                try: 
                    spot_master = get_price(driver, symbol) * asset['strike_mult']
                except: 
                    pass
                
    if df_master.empty: 
        return None, None
    
    df_agg = df_master.groupby('strike', as_index=False).sum().sort_values('strike')
    
    try:
        cw = df_agg.loc[df_agg['ng'].idxmax()]
        pw = df_agg.loc[df_agg['ng'].idxmin()]
        zg_idx = df_agg['ng'].abs().idxmin()
        zero_gamma = df_agg.loc[zg_idx]['strike']
        dp_strike = df_agg.loc[df_agg['c_vol'].idxmax()]['strike'] if 'c_vol' in df_agg.columns else cw['strike']
    except: 
        return None, None
        
    tot_gex = df_agg['ng'].sum()
    regime = "LONG GAMMA (Estavel/Suporte)" if tot_gex > 0 else "SHORT GAMMA (Volatil/Squeeze)"
    
    # --- PASSO 2: TIME TRAVEL (1DTE, 7DTE) ---
    print(" 🕵️ Iniciando Time Travel para fatias DTE...")
    base_url = asset_list[0]["url"]
    
    # Extrai o menu de datas do Barchart
    dates = extract_expiration_dates(driver)
    cw_0dte = cw['strike']
    pw_0dte = pw['strike']
    
    if dates:
        # Extrai 0DTE (Hoje)
        print(f"    ⏳ Lendo 0DTE real ({dates[0]})...")
        res_0dte, _ = process(driver, symbol, f"{base_url}&expirationDate={dates[0]}")
        if res_0dte:
            cw_0dte = res_0dte['CW']
            pw_0dte = res_0dte['PW']
            
        # Extrai 1DTE (Amanhã)
        if len(dates) > 1:
            print(f"    ⏳ Lendo 1DTE ({dates[1]})...")
            res_1dte, df_1dte = process(driver, symbol, f"{base_url}&expirationDate={dates[1]}")
            save(symbol, res_1dte, df_1dte, "_1DTE")
            
        # Extrai 7DTE (~Próxima Semana)
        if len(dates) > 5:
            idx_7 = min(7, len(dates)-1)
            print(f"    ⏳ Lendo 7DTE ({dates[idx_7]})...")
            res_7dte, df_7dte = process(driver, symbol, f"{base_url}&expirationDate={dates[idx_7]}")
            save(symbol, res_7dte, df_7dte, "_7DTE")

    # Monta o pacote final Macro
    res_agg = {
        "CW": cw['strike'], "CWM": format_money(cw['ng']),
        "PW": pw['strike'], "PWM": format_money(pw['ng']),
        "ZG": zero_gamma, "PG": cw['strike'], "NG": pw['strike'],
        "DP": dp_strike, "DPM": "$0",
        "MP": spot_master,
        "Rat": f"{(abs(df_agg['ng'][df_agg['ng']<0].sum()) / df_agg['ng'][df_agg['ng']>0].sum() if df_agg['ng'][df_agg['ng']>0].sum() > 0 else 0):.2f}",
        "FlowSig": "Bull" if df_agg.get('nf', pd.Series([0])).sum() > 0 else "Bear",
        "GexSig": "Bull" if tot_gex > 0 else "Bear",
        "FlowVal": format_money(df_agg.get('nf', pd.Series([0])).sum() * spot_master),
        "GexVal": format_money(tot_gex),
        "AlvoUp": f"{spot_master*1.005:.2f}",
        "AlvoDown": f"{spot_master*0.995:.2f}",
        "Regime": regime,
        "CW_0DTE": cw_0dte,
        "PW_0DTE": pw_0dte
    }
        
    print(f" 🌟 MURALHAS FINAIS -> CW:{res_agg['CW']} | PW:{res_agg['PW']} | ZG:{res_agg['ZG']:.2f}")
    return res_agg, df_agg

# ==============================================================================
# EXECUÇÃO PRINCIPAL
# ==============================================================================
if __name__ == "__main__":
    print("--- INICIANDO QUANT ENGINE V9 (HEATMAP & TIME TRAVEL) ---")
    
    # Dicionário de URLs Oficiais
    ATIVOS_AGREGADOS = {
        "ES": [
            {"url": "https://www.barchart.com/futures/quotes/ES*0/options?futuresOptionsView=split", "strike_mult": 1, "gex_correcao": 1},
            {"url": "https://www.barchart.com/stocks/quotes/$SPX/options?view=split", "strike_mult": 1, "gex_correcao": 2},
            {"url": "https://www.barchart.com/etfs-funds/quotes/SPY/options?view=split", "strike_mult": 10, "gex_correcao": 2}
        ],
        "NQ": [
            {"url": "https://www.barchart.com/futures/quotes/NQ*0/options?futuresOptionsView=split", "strike_mult": 1, "gex_correcao": 1},
            {"url": "https://www.barchart.com/etfs-funds/quotes/QQQ/options?view=split", "strike_mult": 40, "gex_correcao": 5}
        ],
        "GC": [
            {"url": "https://www.barchart.com/futures/quotes/GC*0/options?futuresOptionsView=split", "strike_mult": 1, "gex_correcao": 1}
        ],
        "CL": [
            {"url": "https://www.barchart.com/futures/quotes/CL*0/options?futuresOptionsView=split", "strike_mult": 1, "gex_correcao": 1}
        ],
        "ZB": [
            {"url": "https://www.barchart.com/futures/quotes/ZB*0/options?futuresOptionsView=split", "strike_mult": 1, "gex_correcao": 1}
        ],
        "ZN": [
            {"url": "https://www.barchart.com/futures/quotes/ZN*0/options?futuresOptionsView=split", "strike_mult": 1, "gex_correcao": 1}
        ],
        "YM": [
            {"url": "https://www.barchart.com/futures/quotes/YM*0/options?futuresOptionsView=split", "strike_mult": 1, "gex_correcao": 1},
            {"url": "https://www.barchart.com/etfs-funds/quotes/DIA/options?view=split", "strike_mult": 100, "gex_correcao": 1}
        ],
        "RTY": [
            {"url": "https://www.barchart.com/futures/quotes/RTY*0/options?futuresOptionsView=split", "strike_mult": 1, "gex_correcao": 1},
            {"url": "https://www.barchart.com/etfs-funds/quotes/IWM/options?view=split", "strike_mult": 10, "gex_correcao": 5}
        ],
        "NG": [
            {"url": "https://www.barchart.com/futures/quotes/NG*0/options?futuresOptionsView=split", "strike_mult": 1, "gex_correcao": 1}
        ]
    }

    d = iniciar_driver()
    if d:
        for s, urls in ATIVOS_AGREGADOS.items():
            r, f = process_group(d, s, urls)
            save(s, r, f)
        d.quit()
        
    upload_to_dropbox()
    print("✅ Ciclo de Engenharia Finalizado com Sucesso!")
