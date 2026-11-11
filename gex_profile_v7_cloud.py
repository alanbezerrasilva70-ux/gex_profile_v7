import time
import os
import pandas as pd
import re
import math
from datetime import date, datetime, time as datetime_time, timedelta, timezone
from urllib.parse import parse_qs, urljoin, urlparse
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# ==============================================================================
# CONFIGURAÇÕES V9 - QUANT ENGINE (HEATMAP + TIME TRAVEL 1DTE/2DTE/7DTE)
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

IV_BASE_POR_ATIVO = {
    "ES": 0.14,
    "NQ": 0.18,
    "CL": 0.25,
    "YM": 0.12,
    "RTY": 0.20,
    "NG": 0.40,
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


def _normalize_header(value):
    return re.sub(r"[^a-z]", "", value.lower())


def _parse_contract_count(value):
    text = str(value).strip().replace(",", "").upper()
    if text in {"", "-", "--", "—", "–", "N/A"}:
        return 0.0
    multiplier = 1.0
    if text.endswith("K"):
        multiplier = 1_000.0
        text = text[:-1]
    elif text.endswith("M"):
        multiplier = 1_000_000.0
        text = text[:-1]
    try:
        count = float(text) * multiplier
    except ValueError:
        return None
    if not math.isfinite(count) or count < 0 or not count.is_integer():
        return None
    return count


def parse_barchart_option_payload(payload):
    option_data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(option_data, dict):
        raise ValueError("A resposta da API de opções do Barchart não contém dados agrupados.")

    rows = []
    for strike_label, contracts in option_data.items():
        if not isinstance(contracts, list):
            continue
        call = next(
            (
                contract for contract in contracts
                if str(contract.get("optionType", "")).lower() == "call"
            ),
            None,
        )
        put = next(
            (
                contract for contract in contracts
                if str(contract.get("optionType", "")).lower() == "put"
            ),
            None,
        )
        if call is None and put is None:
            continue
        strike = (
            (call or {}).get("strikePrice")
            or (put or {}).get("strikePrice")
            or strike_label
        )
        rows.append([
            (call or {}).get("volume", "N/A"),
            (call or {}).get("openInterest", "N/A"),
            strike,
            (put or {}).get("volume", "N/A"),
            (put or {}).get("openInterest", "N/A"),
        ])

    if not rows:
        raise ValueError("A API do Barchart não retornou contratos Call/Put reconhecíveis.")
    return {
        "headers": [
            "Call Volume",
            "Call Open Interest",
            "Strike",
            "Put Volume",
            "Put Open Interest",
        ],
        "rows": rows,
    }


def _futures_weekly_api_config(url):
    match = re.match(
        r"^/futures/quotes/[^/]+/options/([^/]+)/?$",
        urlparse(url).path,
    )
    if not match:
        return None
    return {
        "method": "quotes",
        "symbol": match.group(1),
        "list": "futures.options",
        "fields": (
            "optionType,lastPrice,volume,openInterest,premium,strikePrice,"
            "longSymbol,symbolName,symbolType"
        ),
        "groupBy": "strikePrice",
        "meta": "field.shortName,field.description,field.type",
        "orderBy": "strikePrice",
        "orderDir": "asc",
        "raw": 1,
    }


def parse_option_tables(tables, spot, margin):
    # Antes, os valores eram lidos por posicoes em um texto achatado; uma celula
    # ausente podia deslocar OI/volume e fazer um strike virar contagem.
    # Agora, preservamos linhas e colunas da tabela e aceitamos apenas contagens validas.
    best_rows = []
    for table in tables:
        parsed_table = []
        headers = [_normalize_header(header) for header in table.get("headers", [])]
        strike_columns = [i for i, header in enumerate(headers) if "strike" in header]
        if not strike_columns:
            continue
        strike_index = strike_columns[0]
        volume_columns = [
            i for i, header in enumerate(headers)
            if "volume" in header or header.endswith("vol")
        ]
        oi_columns = [
            i for i, header in enumerate(headers)
            if "openinterest" in header or "openint" in header
        ]
        call_volume = [i for i in volume_columns if i < strike_index]
        put_volume = [i for i in volume_columns if i > strike_index]
        call_oi = [i for i in oi_columns if i < strike_index]
        put_oi = [i for i in oi_columns if i > strike_index]
        if not call_volume or not put_volume or not call_oi or not put_oi:
            continue
        indices = (call_volume[-1], call_oi[-1], strike_index, put_volume[0], put_oi[0])

        for cells in table.get("rows", []):
            if len(cells) <= max(indices):
                continue
            strike_text = str(cells[strike_index]).strip().replace(",", "")
            try:
                strike = float(strike_text)
            except ValueError:
                continue
            if not math.isfinite(strike) or not (spot - margin <= strike <= spot + margin):
                continue

            c_vol, c_oi, _, p_vol, p_oi = (
                _parse_contract_count(cells[index]) for index in indices
            )
            if None in (c_vol, c_oi, p_vol, p_oi):
                continue
            if c_vol == 0 and c_oi == 0 and p_vol == 0 and p_oi == 0:
                continue
            parsed_table.append({
                "strike": strike,
                "c_vol": c_vol,
                "p_vol": p_vol,
                "coi": c_oi,
                "poi": p_oi,
            })
        if len(parsed_table) > len(best_rows):
            best_rows = parsed_table

    if not best_rows:
        raise ValueError(
            "Nenhuma linha válida de opções encontrada. "
            "A tabela não apresentou colunas de Calls/Strike/Puts reconhecíveis."
        )
    return (
        pd.DataFrame(best_rows)
        .groupby("strike", as_index=False)
        .sum()
        .sort_values("strike")
    )


def _expiration_date(driver, url):
    query = parse_qs(urlparse(url).query)
    query_date = query.get("expirationDate") or query.get("expiration", [])
    if query_date:
        expiration_match = re.fullmatch(
            r"(\d{4}-\d{2}-\d{2})(?:-[A-Za-z])?",
            query_date[0],
        )
        if not expiration_match:
            raise ValueError(
                f"Data de vencimento inválida na URL: {query_date[0]!r}"
            )
        try:
            return date.fromisoformat(expiration_match.group(1))
        except ValueError as exc:
            raise ValueError(
                f"Data de vencimento inválida na URL: {query_date[0]!r}"
            ) from exc

    page_text = driver.execute_script("return document.body.innerText;") or ""
    expiration_match = re.search(
        r"\bto expiration on\s+(\d{1,2}/\d{1,2}/\d{2,4})",
        page_text,
        flags=re.IGNORECASE,
    )
    if expiration_match:
        expiration_text = expiration_match.group(1)
        for date_format in ("%m/%d/%y", "%m/%d/%Y"):
            try:
                return datetime.strptime(expiration_text, date_format).date()
            except ValueError:
                continue
        raise ValueError(
            f"Data de vencimento exibida pelo Barchart inválida: {expiration_text!r}"
        )

    expiration_match = re.search(
        r"\bExp\s*:\s*(\d{4}-\d{2}-\d{2})",
        page_text,
        flags=re.IGNORECASE,
    )
    if expiration_match:
        try:
            return date.fromisoformat(expiration_match.group(1))
        except ValueError as exc:
            raise ValueError(
                "Data de vencimento exibida pelo Barchart inválida: "
                f"{expiration_match.group(1)!r}"
            ) from exc

    selected_date = driver.execute_script("""
        return Array.from(document.querySelectorAll('select'))
            .flatMap(select => Array.from(select.selectedOptions).map(option => option.value))
            .map(value => value.match(/^(\\d{4}-\\d{2}-\\d{2})(?:-[A-Za-z])?$/))
            .find(match => match) || null;
    """)
    try:
        selected_expiration = (
            date.fromisoformat(selected_date[1]) if selected_date else None
        )
    except ValueError:
        selected_expiration = None
    if selected_expiration is None:
        dates = extract_expiration_dates(driver)
        selected_expiration = date.fromisoformat(dates[0]) if dates else None
    if selected_expiration is None:
        raise ValueError("Não foi possível identificar a data de vencimento selecionada.")
    return selected_expiration


def _time_to_expiry(expiration_date, now=None):
    try:
        # Barchart supplies the date, not the contract-specific expiration time.
        expiry = datetime.combine(
            expiration_date,
            datetime_time(16, 0),
            tzinfo=ZoneInfo("America/New_York"),
        )
    except ZoneInfoNotFoundError as exc:
        raise RuntimeError(
            "Fuso America/New_York indisponível. Instale o pacote tzdata."
        ) from exc
    current_time = now or datetime.now(timezone.utc)
    if current_time.tzinfo is None:
        raise ValueError("O horário de referência precisa incluir fuso horário.")
    seconds_remaining = (expiry.astimezone(timezone.utc) - current_time.astimezone(timezone.utc)).total_seconds()
    return max(seconds_remaining, 0.0) / (365.0 * 24.0 * 60.0 * 60.0)


def parse_futures_expiration_options(option_groups, as_of):
    weekday_numbers = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
    }
    expiration_routes = {}
    for group in option_groups or []:
        weekday_match = re.match(
            r"(\w+)\s+Weekly Options",
            str(group.get("weekday", "")),
            flags=re.IGNORECASE,
        )
        if not weekday_match:
            continue
        weekday = weekday_numbers.get(weekday_match.group(1).lower())
        if weekday is None:
            continue

        for option in group.get("options", []):
            label_match = re.fullmatch(
                r"Week\s+(\d+):\s+([A-Za-z]{3})\s+(\d{4})",
                str(option.get("label", "")).strip(),
                flags=re.IGNORECASE,
            )
            route = option.get("value")
            if not label_match or not route:
                continue
            week_number = int(label_match.group(1))
            if week_number < 1:
                continue
            try:
                month_start = datetime.strptime(
                    f"{label_match.group(2)} {label_match.group(3)}",
                    "%b %Y",
                ).date().replace(day=1)
            except ValueError:
                continue
            first_weekday = month_start + timedelta(
                days=(weekday - month_start.weekday()) % 7
            )
            expiration = first_weekday + timedelta(days=(week_number - 1) * 7)
            if expiration.month != month_start.month or expiration < as_of:
                continue
            expiration_routes.setdefault(expiration, route)

    return [
        {"date": expiration, "url": route}
        for expiration, route in sorted(expiration_routes.items())
    ]


def select_expiration_for_dte(expirations, as_of, dte):
    if dte < 0:
        raise ValueError("DTE não pode ser negativo.")
    if dte == 0:
        for expiration in expirations:
            if expiration["date"] == as_of:
                return expiration
        raise RuntimeError(
            f"Não há vencimento Futures disponível para 0DTE em {as_of}."
        )

    candidates = [
        expiration
        for expiration in expirations
        if expiration["date"] >= as_of
    ]
    if not candidates:
        raise RuntimeError(
            f"Não há vencimentos Futures disponíveis para selecionar {dte}DTE."
        )

    target_date = as_of + timedelta(days=dte)
    return min(
        candidates,
        key=lambda expiration: (
            abs((expiration["date"] - target_date).days),
            expiration["date"] < target_date,
            expiration["date"],
        ),
    )


def total_gex_at_spot(df, candidate_spot, risk_free=0.05):
    total = 0.0
    for row in df.itertuples(index=False):
        strike_mult = getattr(row, "strike_mult", 1.0)
        source_spot = candidate_spot / strike_mult
        source_strike = getattr(row, "base_strike", None)
        if source_strike is None:
            source_strike = row.strike / strike_mult
        gamma = black_scholes_gamma(
            source_spot,
            source_strike,
            row.time_to_expiry,
            risk_free,
            row.iv,
        )
        total += (
            (row.coi - row.poi)
            * gamma
            * row.contract_mult
            * source_spot
        )
    return total


def find_gex_flip(df, current_spot, steps=601):
    # Antes, "Zero Gamma" era o strike com ng por strike mais perto de zero.
    # Agora, buscamos onde o GEX total do modelo troca de sinal ao variar o spot.
    if df.empty or current_spot <= 0 or steps < 2:
        return None
    lower = current_spot * 0.85
    upper = current_spot * 1.15
    samples = (
        (price, total_gex_at_spot(df, price))
        for price in (
            lower + (upper - lower) * index / (steps - 1)
            for index in range(steps)
        )
    )
    crossings = []
    previous = None
    for price, exposure in samples:
        if not math.isfinite(exposure) or exposure == 0:
            continue
        if previous is not None:
            previous_price, previous_exposure = previous
            if (previous_exposure < 0 < exposure) or (exposure < 0 < previous_exposure):
                low_price, low_exposure = previous_price, previous_exposure
                high_price = price
                for _ in range(50):
                    middle_price = (low_price + high_price) / 2
                    middle_exposure = total_gex_at_spot(df, middle_price)
                    if middle_exposure == 0:
                        low_price = high_price = middle_price
                        break
                    if (low_exposure < 0 < middle_exposure) or (
                        middle_exposure < 0 < low_exposure
                    ):
                        high_price = middle_price
                    else:
                        low_price, low_exposure = middle_price, middle_exposure
                crossings.append((low_price + high_price) / 2)
        previous = (price, exposure)
    return min(crossings, key=lambda value: abs(value - current_spot)) if crossings else None


def calculate_max_pain(df):
    strikes = sorted(df["strike"].unique())
    if not strikes:
        return None
    payouts = []
    for settlement in strikes:
        call_payout = ((settlement - df["strike"]).clip(lower=0) * df["coi"]).sum()
        put_payout = ((df["strike"] - settlement).clip(lower=0) * df["poi"]).sum()
        payouts.append((call_payout + put_payout, settlement))
    return min(payouts, key=lambda payout: payout[0])[1]

# ==============================================================================
# INICIALIZAÇÃO DO NAVEGADOR
# ==============================================================================
def iniciar_driver():
    print("👻 Iniciando Driver V9 (Time Travel e Heatmap Ativados)...")
    from selenium import webdriver
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
    from selenium.webdriver.common.by import By
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
def extract_expiration_dates(driver, url=None):
    try:
        if url:
            driver.get(url)
            time.sleep(5)
        script = """
            return Array.from(document.querySelectorAll('select option'))
                .map(option => option.value)
                .filter(value => /^\\d{4}-\\d{2}-\\d{2}$/.test(value));
        """
        values = driver.execute_script(script)
        dates = set()
        for value in values or []:
            try:
                parsed_date = date.fromisoformat(value)
            except (TypeError, ValueError):
                continue
            if parsed_date.isoformat() == value:
                dates.add(parsed_date)
        return [expiration.isoformat() for expiration in sorted(dates)]
    except Exception as e:
        print(f"Erro ao extrair datas: {e}")
        return []


def extract_futures_expiration_options(driver, url, as_of):
    driver.get(url)
    time.sleep(5)
    option_groups = driver.execute_async_script("""
        const done = arguments[arguments.length - 1];
        (async () => {
            const types = Array.from(
                document.querySelectorAll('#bc-options-toolbar__dropdown-type option')
            ).filter(option => /Weekly Options/i.test(option.textContent || ''));
            if (!types.length) {
                throw new Error('A página não listou opções semanais de Futures.');
            }
            const groups = await Promise.all(types.map(async option => {
                const route = new URL(option.value, location.origin);
                route.searchParams.set('futuresOptionsView', 'split');
                const response = await fetch(route.href, {credentials: 'same-origin'});
                if (!response.ok) {
                    throw new Error(
                        'Falha ao carregar o calendário de vencimentos: HTTP ' +
                        response.status
                    );
                }
                const html = await response.text();
                const page = new DOMParser().parseFromString(html, 'text/html');
                const monthSelect = page.querySelector(
                    '#bc-options-toolbar__dropdown-month'
                );
                if (!monthSelect) {
                    throw new Error(
                        'Calendário de vencimentos semanais não encontrado.'
                    );
                }
                return {
                    weekday: option.textContent.trim(),
                    options: Array.from(monthSelect.options).map(expiration => ({
                        label: expiration.textContent.trim(),
                        value: expiration.value
                    }))
                };
            }));
            done(groups);
        })().catch(error => done({scrapeError: error.message}));
    """)
    if isinstance(option_groups, dict) and option_groups.get("scrapeError"):
        raise RuntimeError(
            "Falha ao obter vencimentos semanais do Barchart: "
            f"{option_groups['scrapeError']}"
        )
    return [
        {"date": expiration["date"], "url": urljoin(url, expiration["url"])}
        for expiration in parse_futures_expiration_options(option_groups, as_of)
    ]


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

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1)
        fallback_api = _futures_weekly_api_config(url)
        payload = driver.execute_async_script("""
            const fallbackApi = arguments[0];
            const done = arguments[arguments.length - 1];
            (async () => {
                const container = document.querySelector(
                    '.bc-futures-options-quotes__columns, .bc-options-quotes__columns'
                );
                let api;
                if (container) {
                    const config = JSON.parse(container.getAttribute('data-settings'));
                    const settings = config.settings || config;
                    api = settings.api;
                } else if (fallbackApi) {
                    api = fallbackApi;
                } else {
                    throw new Error('Configuração da cadeia de opções não encontrada na página.');
                }
                if (!api || !api.method) {
                    throw new Error('Configuração da API de opções do Barchart ausente.');
                }
                const endpoint = api.method.startsWith('/')
                    ? '/proxies/core-api/v1' + api.method
                    : '/proxies/core-api/v1/' + api.method + '/get';
                const params = new URLSearchParams();
                Object.entries(api).forEach(([key, value]) => {
                    if (key !== 'method' && value !== undefined && value !== null) {
                        params.append(key, String(value));
                    }
                });
                const response = await fetch(endpoint + '?' + params.toString(), {
                    credentials: 'same-origin'
                });
                if (!response.ok) {
                    throw new Error('API do Barchart respondeu HTTP ' + response.status);
                }
                done(await response.json());
            })().catch(error => done({ scrapeError: error.message }));
        """, fallback_api)
        if isinstance(payload, dict) and payload.get("scrapeError"):
            raise RuntimeError(f"Falha ao consultar API de opções do Barchart: {payload['scrapeError']}")
        tables = [parse_barchart_option_payload(payload)]
        margin = spot * 0.15
        expiration_date = _expiration_date(driver, url)
        T_years = _time_to_expiry(expiration_date)
        if T_years <= 0:
            raise ValueError(f"O vencimento {expiration_date} já expirou no horário de Nova York.")
        risk_free = 0.05       
        
        # Hipótese do modelo: não é uma IV observada por contrato.
        iv_avg = IV_BASE_POR_ATIVO.get(symbol, 0.14)
        print(f" IV base assumida para {symbol}: {iv_avg:.0%} (não individual por contrato)")
        
        mult = MULTIPLIADORES.get(symbol, 100)
        df = parse_option_tables(tables, spot, margin)
        df["expiration_date"] = expiration_date.isoformat()
        df["nf"] = df["c_vol"] - df["p_vol"]
        df["vol"] = df["c_vol"] + df["p_vol"]
        df["toi"] = df["coi"] + df["poi"]
        df["time_to_expiry"] = T_years
        df["iv"] = iv_avg
        df["contract_mult"] = mult
        df["strike_mult"] = 1.0
        df["spot"] = spot
        df["base_strike"] = df["strike"]
        gamma_by_strike = df["strike"].map(
            lambda strike: black_scholes_gamma(spot, strike, T_years, risk_free, iv_avg)
        )
        df["cgex"] = df["coi"] * gamma_by_strike * mult * spot
        df["pgex"] = df["poi"] * gamma_by_strike * mult * spot
        df["ng"] = df["cgex"] - df["pgex"]
        
        max_pain = calculate_max_pain(df)

        # Antes, as paredes eram o maximo/minimo do GEX liquido.
        # Agora, Call e Put Wall sao maximos separados das exposicoes de calls e puts.
        cw = df.loc[df["cgex"].idxmax()]
        pw = df.loc[df["pgex"].idxmax()]
        zero_gamma = find_gex_flip(df, spot, steps=601)

        dp = df.loc[df['vol'].idxmax()]
        
        tot_gex = df['ng'].sum()
        tot_flow = df['nf'].sum()
        
        if tot_gex > 0:
            regime = "LONG GAMMA (Estavel/Suporte)"
        else:
            regime = "SHORT GAMMA (Volatil/Squeeze)"
            
        res = {
            "CW": cw['strike'], "CWM": format_money(cw['cgex']),
            "PW": pw['strike'], "PWM": format_money(-pw['pgex']),
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
        
        if zero_gamma is None:
            print(" ⚠️ Nenhum cruzamento de GEX encontrado na faixa analisada.")
        else:
            print(f" ✅ GEX Flip estimado:{zero_gamma:.2f}")
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
            zero_gamma = res["ZG"] if res["ZG"] is not None else 0
            f.write(f"{res['CW']},{res['PW']},{zero_gamma:.2f},{res['PG']},{res['NG']},{res['CWM']},{res['PWM']},{res.get('CW_0DTE') or 0},{res.get('PW_0DTE') or 0}")
        
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
        raise RuntimeError("Credenciais DBX_SECRET/DBX_REFRESH do Dropbox não encontradas.")

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
        raise

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
        if res is None or df is None or df.empty:
            raise RuntimeError(f"Falha ao extrair a cadeia de opções de {symbol}: {asset['url']}")
        strike_mult = asset["strike_mult"]
        gex_correction = asset["gex_correcao"]
        df['base_strike'] = df['strike']
        df['strike'] = df['strike'] * strike_mult
        df['strike'] = (df['strike'] / 5).round() * 5
        df["strike_mult"] = strike_mult
        for col in ['ng', 'nf', 'coi', 'poi', 'cgex', 'pgex']:
            df[col] = df[col] * gex_correction

        df_master = pd.concat([df_master, df], ignore_index=True)

        if spot_master == 0:
            spot_master = float(df["spot"].iloc[0]) * strike_mult

    if df_master.empty: 
        return None, None
    
    summed_columns = [
        "ng", "nf", "c_vol", "p_vol", "coi", "poi", "vol", "toi", "cgex", "pgex"
    ]
    df_agg = (
        df_master.groupby("strike", as_index=False)[summed_columns]
        .sum()
        .sort_values("strike")
    )
    
    try:
        # Mantem a mesma definicao de paredes separadas no agregado multi-ativo.
        cw = df_agg.loc[df_agg["cgex"].idxmax()]
        pw = df_agg.loc[df_agg["pgex"].idxmax()]
        dp_strike = df_agg.loc[df_agg['c_vol'].idxmax()]['strike'] if 'c_vol' in df_agg.columns else cw['strike']
    except: 
        return None, None
        
    tot_gex = df_agg['ng'].sum()
    zero_gamma = find_gex_flip(df_master, spot_master, steps=601)
    max_pain = calculate_max_pain(df_agg)
    regime = "LONG GAMMA (Estavel/Suporte)" if tot_gex > 0 else "SHORT GAMMA (Volatil/Squeeze)"
    
    # --- PASSO 2: TIME TRAVEL (1DTE, 7DTE) ---
    print(" 🕵️ Iniciando Time Travel para fatias DTE...")
    base_url = asset_list[0]["url"]
    
    today_new_york = datetime.now(ZoneInfo("America/New_York")).date()
    expirations = extract_futures_expiration_options(driver, base_url, today_new_york)
    cw_0dte = None
    pw_0dte = None
    
    def process_dte(dte, label, suffix=None):
        expiration = select_expiration_for_dte(expirations, today_new_york, dte)
        expiration_text = expiration["date"].isoformat()
        print(f"    ⏳ Lendo {label} ({expiration_text})...")
        result, profile = process(driver, symbol, expiration["url"])
        if result is None or profile is None or profile.empty:
            raise RuntimeError(
                f"Falha ao extrair {label} de {symbol} ({expiration_text})."
            )
        actual_expiration = profile["expiration_date"].iloc[0]
        if actual_expiration != expiration_text:
            raise RuntimeError(
                f"O Barchart carregou {actual_expiration} para {label} de {symbol}; "
                f"era esperado {expiration_text}. Nenhum nível DTE será salvo."
            )
        if suffix:
            save(symbol, result, profile, suffix)
        return result, profile

    if any(expiration["date"] == today_new_york for expiration in expirations):
        res_0dte, _ = process_dte(0, "0DTE")
        cw_0dte = res_0dte["CW"]
        pw_0dte = res_0dte["PW"]
    else:
        print(
            f" ⚠️ {symbol} não tem vencimento Futures em {today_new_york}; "
            "0DTE será omitido. O macro e as outras fatias DTE continuarão."
        )
    process_dte(1, "1DTE", "_1DTE")
    process_dte(2, "2DTE", "_2DTE")
    process_dte(7, "7DTE", "_7DTE")

    # Monta o pacote final Macro
    res_agg = {
        "CW": cw['strike'], "CWM": format_money(cw['cgex']),
        "PW": pw['strike'], "PWM": format_money(-pw['pgex']),
        "ZG": zero_gamma, "PG": cw['strike'], "NG": pw['strike'],
        "DP": dp_strike, "DPM": "$0",
        "MP": max_pain,
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
        
    if zero_gamma is None:
        print(f" 🌟 MURALHAS FINAIS -> CW:{res_agg['CW']} | PW:{res_agg['PW']} | GEX Flip: sem cruzamento")
    else:
        print(f" 🌟 MURALHAS FINAIS -> CW:{res_agg['CW']} | PW:{res_agg['PW']} | GEX Flip estimado:{zero_gamma:.2f}")
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
        try:
            for s, urls in ATIVOS_AGREGADOS.items():
                r, f = process_group(d, s, urls)
                if r is None or f is None:
                    raise RuntimeError(f"Não foi possível gerar os dados completos de {s}.")
                save(s, r, f)
        finally:
            d.quit()
    else:
        raise RuntimeError("Não foi possível iniciar o navegador para coletar as opções.")
        
    upload_to_dropbox()
    print("✅ Ciclo de Engenharia Finalizado com Sucesso!")
