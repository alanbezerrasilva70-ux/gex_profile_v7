import time
import os
import pandas as pd
import re
import math
from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions 
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# ==============================================================================
# CONFIGURAÇÕES V7 - COM MOTOR MATEMÁTICO BLACK-SCHOLES
# ==============================================================================
PASTA_DADOS = "./GEX_Data" 
HEADLESS_MODE = True 

ATIVOS = {
    "ES": "https://www.barchart.com/futures/quotes/ES*0/options?futuresOptionsView=split", 
    "NQ": "https://www.barchart.com/futures/quotes/NQ*0/options?futuresOptionsView=split", 
    "CL": "https://www.barchart.com/futures/quotes/CL*0/options?futuresOptionsView=split", 
    "GC": "https://www.barchart.com/futures/quotes/GC*0/options?futuresOptionsView=split",
    "ZB": "https://www.barchart.com/futures/quotes/ZB*0/options?futuresOptionsView=split",
    "ZN": "https://www.barchart.com/futures/quotes/ZN*0/options?futuresOptionsView=split"
}

# --- MOTOR MATEMÁTICO BLACK-SCHOLES (A MÁGICA ACONTECE AQUI) ---
def pdf(x):
    """Função de Densidade de Probabilidade Normal"""
    return math.exp(-x**2 / 2) / math.sqrt(2 * math.pi)

def black_scholes_gamma(S, K, T, r, sigma):
    """
    Calcula o GAMA de uma opção europeia.
    S: Preço Spot do Ativo
    K: Strike
    T: Tempo até vencimento (em anos)
    r: Taxa de juros livre de risco
    sigma: Volatilidade (IV)
    """
    try:
        if T <= 0 or sigma <= 0 or S <= 0: return 0.0
        d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        gamma = pdf(d1) / (S * sigma * math.sqrt(T))
        return gamma
    except:
        return 0.0
def iniciar_driver():
    print("👻 Iniciando Driver V7 com Stealth (Bypass Cloudflare)...")
    import undetected_chromedriver as uc
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    try:
        driver = uc.Chrome(options=options)
        print("✅ Driver Cloud iniciado com sucesso!")
        return driver
    except Exception as e:
        print(f"❌ ERRO: {e}")
        return None

def clean_float(val):
    s = str(val).replace(',', '').replace('N/A', '').strip()
    try: return float(s)
    except: return 0.0

def format_money(val):
    v = abs(val)
    s = "-" if val < 0 else ""
    if v >= 1e9: return f"{s}${v/1e9:.2f}B"
    if v >= 1e6: return f"{s}${v/1e6:.2f}M"
    return f"{s}${v:.0f}"

def get_price(driver, symbol):
    selectors = ["span.last-change", "div.price-change", ".quote-price"]
    txt = ""
    for sel in selectors:
        try:
            el = driver.find_element(By.CSS_SELECTOR, sel)
            txt = el.text.split()[0].strip()
            if txt and txt != "---": break
        except: continue
    if not txt: return 0.0
    
    # Tratamento especial para Bonds (ZB/ZN) que usam frações
    if symbol in ["ZB","ZN"] and "-" in txt:
        try: p=txt.split('-'); return float(p[0])+(float(p[1])/32.0)
        except: return 0.0
        
    try: return float(txt.replace(',',''))
    except: return 0.0

def process(driver, symbol, url):
    print(f" 🔎 {symbol}...", end="")
    try:
        driver.get(url)
        time.sleep(3)
        spot = get_price(driver, symbol)
        if spot == 0: 
            print(" ❌ Spot Zero (Site carregou?).")
            return None, None

        # Rolagem para carregar strikes OTM
        body = driver.find_element(By.TAG_NAME, "body")
        for _ in range(6):
            body.send_keys(Keys.PAGE_DOWN)
            time.sleep(0.3)
        
        # Extração de texto bruto (Rápido e sujo, mas funciona no Barchart)
        page_text = driver.find_element(By.TAG_NAME, "body").text
        tokens = page_text.split()
        
        data = []
        margin = spot * 0.15 # 15% de margem (Gama fora disso é zero mesmo)
        
        # --- PREMISSAS PARA CÁLCULO GEX (Fixas para Day Trade) ---
        T_years = 1.0 / 365.0  # 1 Dia (Foco tático)
        risk_free = 0.05       # 5% a.a.
        iv_avg = 0.14          # 14% Volatilidade (Estimativa média SP500)
        if symbol == "NQ": iv_avg = 0.18
        if symbol == "CL": iv_avg = 0.25
        
        for i in range(5, len(tokens)-5):
            t = tokens[i].replace(',', '')
            # Regex simples para achar Strikes
            if not re.match(r'^\d{1,5}(\.\d{1,4})?$', t): continue
            
            try: strike = float(t)
            except: continue

            if strike < (spot - margin) or strike > (spot + margin): continue
            
            try:
                # Tenta mapear as colunas baseadas na posição do Strike
                # Barchart Split View: Vol | OI | ... | Strike | ... | Vol | OI
                # Isso pode variar, mas mantendo sua lógica original:
                c_oi = clean_float(tokens[i-2])
                c_vol = clean_float(tokens[i-3])
                p_oi = clean_float(tokens[i+3])
                p_vol = clean_float(tokens[i+2])
                
                if c_oi==0 and p_oi==0 and c_vol==0 and p_vol==0: continue
                
                # --- AQUI É A CORREÇÃO REAL ---
                # Calcula o Gamma unitário para este strike
                gamma_unit = black_scholes_gamma(spot, strike, T_years, risk_free, iv_avg)
                
                # O Gama Total é: OI * GamaUnitario * 100 (tamanho do contrato)
                call_gex = c_oi * gamma_unit * 100 * spot 
                put_gex = p_oi * gamma_unit * 100 * spot
                
                # Net GEX: Positivo (Calls puxam) - Negativo (Puts puxam/repelem)
                net_gex_strike = call_gex - put_gex
                
                net_flow_strike = c_vol - p_vol
                total_vol = c_vol + p_vol
                total_oi = c_oi + p_oi 
                
                data.append({
                    "strike": strike, 
                    "ng": net_gex_strike,
                    "nf": net_flow_strike,
                    "coi": c_oi, "poi": p_oi, 
                    "vol": total_vol,
                    "toi": total_oi
                })
            except: continue
            
        if not data: return None, None
        
        df = pd.DataFrame(data).drop_duplicates('strike').sort_values('strike')
        
        # --- ANALYTICS ---
        
        # 1. Max Pain (Onde OI Call ~= OI Put, menor perda para vendedores)
        # Aproximação simples: Strike onde a soma do valor nocional das opções expira com menor valor
        try:
            mp_idx = df['toi'].idxmax() # Simplificado: Strike com mais interesse
            max_pain = df.loc[mp_idx]['strike']
        except: max_pain = spot

        # 2. Walls (Barreiras de GAMA, não só OI)
        # Call Wall: Maior GEX Positivo (Resistência)
        # Put Wall: Maior GEX Negativo (Suporte)
        try:
            cw = df.loc[df['ng'].idxmax()] # Maior Gama Positivo
            pw = df.loc[df['ng'].idxmin()] # Maior Gama Negativo (Puts)
        except:
            cw = df.iloc[-1]
            pw = df.iloc[0]

        # 3. Zero Gamma Flip (Ponto de inversão)
        # Onde o Gama Total cumulativo cruza zero? 
        # Ou simplesmente a média entre Call Wall e Put Wall como estimativa rápida
        zero_gamma = (cw['strike'] + pw['strike']) / 2
        
        # 4. Block Trade (Dark Pool Proxy - Maior Volume pontual)
        dp = df.loc[df['vol'].idxmax()]
        
        # Totais do Mercado
        tot_gex = df['ng'].sum()
        sig_gex = "Bull" if tot_gex > 0 else "Bear"
        
        tot_flow = df['nf'].sum()
        sig_flow = "Bull" if tot_flow > 0 else "Bear"
        
        res = {
            "CW": cw['strike'], "CWM": format_money(cw['ng']), # Agora mostra valor nocional GEX
            "PW": pw['strike'], "PWM": format_money(pw['ng']),
            "ZG": zero_gamma, 
            "PG": cw['strike'], # Pos Gex Max
            "NG": pw['strike'], # Neg Gex Max
            "DP": dp['strike'], "DPM": format_money(dp['vol']*spot*50),
            "MP": max_pain, 
            "Rat": f"{(abs(df['ng'][df['ng']<0].sum()) / df['ng'][df['ng']>0].sum() if df['ng'][df['ng']>0].sum() > 0 else 0):.2f}",
            "FlowSig": sig_flow,
            "GexSig": sig_gex,
            "FlowVal": format_money(tot_flow * spot * 50),
            "GexVal": format_money(tot_gex), # Já está nocional
            "AlvoUp": f"{spot*1.005:.2f}",
            "AlvoDown": f"{spot*0.995:.2f}"
        }
        
        print(f" ✅ P:{spot} | CW:{res['CW']} | PW:{res['PW']} | ZG:{res['ZG']:.2f}")
        return res, df
        
    except Exception as e: 
        print(f" ❌ Erro processamento: {e}")
        return None, None

def save(sym, res, df):
    if not os.path.exists(PASTA_DADOS): os.makedirs(PASTA_DADOS)
    if res:
        with open(f"{PASTA_DADOS}/NiveisGamma_{sym}.csv", "w") as f:
            f.write(f"{res['CW']},{res['PW']},{res['ZG']:.2f},{res['PG']},{res['NG']},{res['CWM']},{res['PWM']}")
        
        with open(f"{PASTA_DADOS}/AlvosVolatilidade_{sym}.csv", "w") as f:
            f.write(f"{res['MP']},{res['DP']},{res['Rat']},15.5,{res['FlowSig']},{res['GexSig']},{res['DPM']},{res['FlowVal']},{res['GexVal']},{res['AlvoUp']},{res['AlvoDown']}")
            
    if df is not None:
        df.to_csv(f"{PASTA_DADOS}/GammaProfile_{sym}.csv", index=False, columns=['strike','ng'])
if __name__ == "__main__":
    print("--- INICIANDO ROBÔ CLOUD DE GAMA ESTRUTURAL ---")
    d = iniciar_driver()
    if d:
        for s, u in ATIVOS.items():
            r, f = process(d, s, u)
            save(s, r, f)
        d.quit()
    print("✅ Ciclo finalizado! Partindo para o upload no Drive...")
