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
    # [CORREÇÃO EXTRA] GC, ZB e ZN caíam no padrão genérico de 14%. Para títulos
    # (vol. implícita típica de 5-10% a.a.) isso alargava demais a curva gamma e
    # deslocava o GEX Flip. Valores base mais próximos do histórico de cada ativo:
    "GC": 0.18,
    "ZB": 0.09,
    "ZN": 0.06,
}

# [CORREÇÃO 5] Arredondamento de strikes no agregado (modo ALL) apenas para
# índices de pontuação alta, onde proxies (SPY x10, QQQ x40, DIA x100, IWM x10)
# precisam cair na mesma grade dos futuros. CL, GC, ZB, ZN e NG preservam a grade
# natural (ex.: NG 3.25, CL 61.5, ZN 110.25), evitando que tudo colapse em 0/5/60.
STRIKE_ROUNDING = {"ES": 5, "NQ": 5, "YM": 5, "RTY": 5}

# [CORREÇÃO 7] Piso de tempo até o vencimento. Após 16h NY (ou nos minutos finais
# de um 0DTE) T tendia a zero e o script abortava com ValueError / gamma infinito.
SECONDS_PER_YEAR = 365.0 * 24.0 * 60.0 * 60.0
MIN_TIME_TO_EXPIRY_SECONDS = 300.0
NEW_YORK_CLOSE = datetime_time(16, 0)

# [CORREÇÃO 7] Orçamento de tempo do ciclo: se estourar, para de raspar e faz o
# upload do que já foi coletado (o job do GitHub Actions tem timeout de 35 min).
MAX_RUN_SECONDS = 27 * 60
PAGE_LOAD_TIMEOUT_SECONDS = 45

# Erros não fatais do ciclo (ativo/DTE que falhou). Exibidos no resumo final e
# como ::warning:: no GitHub Actions, sem abortar o upload para o Dropbox.
RUN_ERRORS = []


def registrar_erro(mensagem):
    RUN_ERRORS.append(mensagem)
    print(f" ❌ {mensagem}")

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


def parse_option_tables(tables, spot, margin, strike_scales=(1.0,)):
    # Antes, os valores eram lidos por posicoes em um texto achatado; uma celula
    # ausente podia deslocar OI/volume e fazer um strike virar contagem.
    # Agora, preservamos linhas e colunas da tabela e aceitamos apenas contagens validas.
    for strike_scale in strike_scales:
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
                    strike = float(strike_text) * strike_scale
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

        if best_rows:
            if strike_scale != 1.0:
                print(
                    f" ⚠️ Escala de strike do Barchart normalizada por "
                    f"{strike_scale:g} para corresponder ao spot."
                )
            return (
                pd.DataFrame(best_rows)
                .groupby("strike", as_index=False)
                .sum()
                .sort_values("strike")
            )

    raise ValueError(
        "Nenhuma linha válida de opções encontrada. "
        "A tabela não apresentou colunas de Calls/Strike/Puts reconhecíveis."
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
    return max(seconds_remaining, 0.0) / SECONDS_PER_YEAR


def effective_session_date(now_new_york):
    """[CORREÇÃO 7] Data de pregão usada para escolher vencimentos.

    Após o fechamento de 16h NY o vencimento do dia já expirou; a seleção DTE
    passa a considerar o próximo dia útil (o mesmo vale para fins de semana).
    Assim as execuções do fim da tarde não tentam ler um 0DTE vencido.
    """
    session = now_new_york.date()
    if now_new_york.time() >= NEW_YORK_CLOSE:
        session += timedelta(days=1)
    while session.weekday() >= 5:
        session += timedelta(days=1)
    return session


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


def _dte_target_date(as_of, dte):
    """[CORREÇÃO 2] Data-alvo de um DTE.

    Antes: alvo = as_of + dte dias corridos e escolha do vencimento "mais
    próximo". Numa quinta (12/11) o 2DTE caía no sábado 14/11 e o mais próximo
    era a sexta 13/11 — a mesma data do 1DTE, gerando _1DTE e _2DTE idênticos.

    Agora: DTEs curtos (< 5) contam pregões (dias úteis); DTEs semanais (>= 5)
    contam dias corridos (7DTE = mesmo dia da semana seguinte). Alvos que caem
    em fim de semana são empurrados para a segunda-feira.
    """
    if dte >= 5:
        target = as_of + timedelta(days=dte)
    else:
        target = as_of
        remaining = dte
        while remaining > 0:
            target += timedelta(days=1)
            if target.weekday() < 5:
                remaining -= 1
    while target.weekday() >= 5:
        target += timedelta(days=1)
    return target


def select_expiration_for_dte(expirations, as_of, dte, exclude=()):
    if dte < 0:
        raise ValueError("DTE não pode ser negativo.")
    if dte == 0:
        for expiration in expirations:
            if expiration["date"] == as_of:
                return expiration
        raise RuntimeError(
            f"Não há vencimento Futures disponível para 0DTE em {as_of}."
        )

    # [CORREÇÃO 2] Apenas vencimentos FUTUROS (> as_of) e ainda não usados por
    # outra fatia DTE (exclude), para que 0DTE/1DTE/2DTE/7DTE nunca repitam a
    # mesma data quando houver vencimentos distintos disponíveis.
    excluded = set(exclude)
    future_expirations = sorted(
        (expiration for expiration in expirations if expiration["date"] > as_of),
        key=lambda expiration: expiration["date"],
    )
    candidates = [
        expiration
        for expiration in future_expirations
        if expiration["date"] not in excluded
    ]
    if not candidates:
        # Fallback apenas se a corretora/Barchart listar menos vencimentos futuros
        # do que a quantidade de fatias DTE solicitadas.
        candidates = future_expirations or sorted(
            (expiration for expiration in expirations if expiration["date"] >= as_of),
            key=lambda expiration: expiration["date"],
        )
    if not candidates:
        raise RuntimeError(
            f"Não há vencimentos Futures disponíveis para selecionar {dte}DTE."
        )

    target_date = _dte_target_date(as_of, dte)
    on_or_after_target = [
        expiration for expiration in candidates if expiration["date"] >= target_date
    ]
    if on_or_after_target:
        # Primeiro vencimento a partir do alvo (nunca volta para uma data anterior).
        return on_or_after_target[0]
    # Nenhum vencimento chega ao alvo: usa o mais longo disponível.
    return candidates[-1]


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


def select_walls(df):
    """[CORREÇÃO 1] Call Wall / Put Wall pelo GEX LÍQUIDO (ng = cgex - pgex).

    Antes: cw = cgex.idxmax() e pw = pgex.idxmax(). O strike ATM redondo
    (7600 no ES, 27600 no NQ, 85 no CL) concentra straddles institucionais com
    OI alto nos dois lados, então o máximo bruto de calls e o de puts caíam no
    MESMO strike e os dois cards mostravam o mesmo preço.

    Agora:
      * Call Wall = strike com maior exposição líquida POSITIVA (ng > 0);
        fallback para cgex.idxmax() só se não houver strike positivo.
      * Put Wall  = strike com maior exposição líquida NEGATIVA (ng < 0);
        fallback para pgex.idxmax() só se não houver strike negativo.
    Como os conjuntos ng > 0 e ng < 0 são disjuntos, as paredes nunca coincidem
    quando existem os dois sinais; nos fallbacks o strike repetido é excluído.
    """
    if df.empty:
        raise ValueError("Perfil vazio: impossível calcular Call/Put Wall.")
    positive = df[df["ng"] > 0]
    negative = df[df["ng"] < 0]
    cw_index = positive["ng"].idxmax() if not positive.empty else df["cgex"].idxmax()
    pw_index = negative["ng"].idxmin() if not negative.empty else df["pgex"].idxmax()

    same_strike = df.loc[cw_index, "strike"] == df.loc[pw_index, "strike"]
    if same_strike and df["strike"].nunique() > 1:
        if positive.empty:
            others = df[df["strike"] != df.loc[pw_index, "strike"]]
            cw_index = others["cgex"].idxmax()
        else:
            others = df[df["strike"] != df.loc[cw_index, "strike"]]
            pw_index = others["pgex"].idxmax()
    return df.loc[cw_index], df.loc[pw_index]


def apply_proxy_scaling(df, strike_mult, gex_correction):
    """[CORREÇÃO 6] Converte uma cadeia de proxy (ex.: IWM -> RTY) para a escala do futuro.

    Antes isso só era feito no agregado (ALL); as fatias 0DTE/1DTE/2DTE/7DTE do
    RTY saíam em strikes do IWM (~240) e exposições sem correção.
    Agora a mesma função é usada no macro e em todas as fatias DTE:
      * strike (e spot) multiplicados por strike_mult; base_strike preserva o
        strike original da proxy para o cálculo Black-Scholes do GEX Flip;
      * contagens e exposições multiplicadas por gex_correcao — inclusive
        volumes (c_vol, p_vol, vol, toi), que antes ficavam sem correção enquanto
        nf (c_vol - p_vol) era corrigido, deixando DPM e FlowVal em escalas
        diferentes.
    """
    scaled = df.copy()
    scaled["base_strike"] = scaled["strike"]
    scaled["strike"] = (scaled["strike"] * strike_mult).round(6)
    scaled["strike_mult"] = strike_mult
    if "spot" in scaled:
        scaled["spot"] = scaled["spot"] * strike_mult
    for column in ("ng", "nf", "coi", "poi", "cgex", "pgex", "c_vol", "p_vol", "vol", "toi"):
        if column in scaled:
            scaled[column] = scaled[column] * gex_correction
    return scaled


def compute_levels(df_levels, spot, symbol, flip_df=None):
    """Calcula todos os níveis (CW, PW, ZG, DP, MP, ratio, regime...) de um perfil.

    Usado pela cadeia individual (process), pelo agregado (process_group) e pelas
    fatias DTE escaladas de proxies, garantindo a mesma definição em todos os
    arquivos. flip_df permite calcular o GEX Flip sobre as linhas não agregadas
    (cada uma com seu T, IV, multiplicador e strike original).
    """
    max_pain = calculate_max_pain(df_levels)
    cw, pw = select_walls(df_levels)
    dp = df_levels.loc[df_levels["vol"].idxmax()]
    zero_gamma = find_gex_flip(
        flip_df if flip_df is not None else df_levels, spot, steps=601
    )

    tot_gex = df_levels["ng"].sum()
    tot_flow = df_levels["nf"].sum()
    if tot_gex > 0:
        regime = "LONG GAMMA (Estavel/Suporte)"
        gex_signal = "POSITIVE"
    elif tot_gex < 0:
        regime = "SHORT GAMMA (Volatil/Squeeze)"
        gex_signal = "NEGATIVE"
    else:
        regime = "NEUTRAL GAMMA"
        gex_signal = "NEUTRAL"
    flow_signal = (
        "CALLS > PUTS" if tot_flow > 0
        else "PUTS > CALLS" if tot_flow < 0
        else "CALLS = PUTS"
    )
    positive_gex = df_levels["ng"][df_levels["ng"] > 0].sum()
    negative_gex = abs(df_levels["ng"][df_levels["ng"] < 0].sum())
    ratio = negative_gex / positive_gex if positive_gex > 0 else 0

    iv_base = IV_BASE_POR_ATIVO.get(symbol, 0.14)
    return {
        # CWM/PWM agora exibem o GEX líquido da parede (coerente com a nova definição).
        "CW": cw["strike"], "CWM": format_money(cw["ng"]),
        "PW": pw["strike"], "PWM": format_money(pw["ng"]),
        "ZG": zero_gamma,
        # PG/NG = picos de gamma positivo/negativo líquido (mesmos strikes das paredes).
        "PG": cw["strike"],
        "NG": pw["strike"],
        "DP": dp["strike"], "DPM": f"{dp['vol']:.0f}",
        "MP": max_pain,
        "Rat": f"{ratio:.2f}",
        "FlowSig": flow_signal,
        "GexSig": gex_signal,
        "FlowVal": f"{tot_flow:.0f}",
        "GexVal": format_money(tot_gex),
        "AlvoUp": f"{spot*1.005:.2f}",
        "AlvoDown": f"{spot*0.995:.2f}",
        "Regime": regime,
        "IV": iv_base * 100,
        "IVSource": "IV base assumida",
    }

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
        # [CORREÇÃO 7] Sem timeout, um carregamento travado do Barchart prendia o
        # job até o GitHub Actions cancelar tudo antes do upload para o Dropbox.
        driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT_SECONDS)
        driver.set_script_timeout(PAGE_LOAD_TIMEOUT_SECONDS)
        print("✅ Driver Cloud iniciado com sucesso!")
        return driver
    except Exception as e:
        print(f"❌ ERRO ao iniciar driver: {e}")
        return None 


def driver_ativo(driver):
    """Verifica se a sessão do Selenium ainda responde (para recriá-la após crash)."""
    try:
        driver.execute_script("return 1;")
        return True
    except Exception:
        return False

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
def parse_treasury_price(text):
    """[CORREÇÃO EXTRA] Converte cotações fracionárias de ZB/ZN em decimal.

    ZB: "117-16"  -> 117 + 16/32       = 117.5
    ZN: "110-085" -> 110 + 8.5/32      = 110.265625 (3º dígito = fração de 1/32)
    Antes "110-085" virava 110 + 85/32 = 112.66 (preço errado em ~2.4 pontos).
    """
    txt = str(text).strip().replace(",", "")
    match = re.fullmatch(r"(\d+)['\-](\d{2,3})", txt)
    if not match:
        return float(txt)
    whole, fraction = match.groups()
    if len(fraction) == 2:
        thirty_seconds = int(fraction)
    else:
        quarter_map = {"0": 0.0, "2": 0.25, "5": 0.5, "7": 0.75}
        thirty_seconds = int(fraction[:2]) + quarter_map.get(
            fraction[2], int(fraction[2]) / 10.0
        )
    return int(whole) + thirty_seconds / 32.0


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
                    if symbol in ["ZB","ZN"] and ("-" in txt or "'" in txt):
                        try: 
                            return parse_treasury_price(txt)
                        except Exception: 
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


def extract_equity_expiration_options(driver, url, as_of):
    driver.get(url)
    time.sleep(5)
    options = driver.execute_script("""
        return Array.from(document.querySelectorAll('select option'))
            .filter(option => /^\\d{4}-\\d{2}-\\d{2}(?:-[A-Za-z])?$/.test(option.value))
            .map(option => {
                const route = new URL(location.href);
                route.searchParams.set('expiration', option.value);
                return {value: option.value, url: route.href};
            });
    """)
    expiration_routes = {}
    for option in options or []:
        match = re.fullmatch(
            r"(\d{4}-\d{2}-\d{2})(?:-[A-Za-z])?",
            str(option.get("value", "")),
        )
        if not match:
            continue
        try:
            expiration = date.fromisoformat(match.group(1))
        except ValueError:
            continue
        if expiration >= as_of:
            expiration_routes.setdefault(expiration, option["url"])
    if not expiration_routes:
        raise RuntimeError(
            f"Nenhum vencimento de opções disponível em {url} a partir de {as_of}."
        )
    return [
        {"date": expiration, "url": route}
        for expiration, route in sorted(expiration_routes.items())
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
        # [CORREÇÃO 7] Antes: `if T_years <= 0: raise ValueError(...)`, o que
        # abortava as execuções após 16h NY. Agora aplicamos um piso mínimo de
        # 300 s (também evita gamma "infinito" nos minutos finais de um 0DTE).
        min_T_years = MIN_TIME_TO_EXPIRY_SECONDS / SECONDS_PER_YEAR
        if T_years < min_T_years:
            print(
                f" ⚠️ Vencimento {expiration_date} encerrado/prestes a encerrar em NY; "
                f"usando piso de {MIN_TIME_TO_EXPIRY_SECONDS:.0f}s para T."
            )
            T_years = min_T_years
        risk_free = 0.05       
        
        # Hipótese do modelo: não é uma IV observada por contrato.
        iv_avg = IV_BASE_POR_ATIVO.get(symbol, 0.14)
        print(f" IV base assumida para {symbol}: {iv_avg:.0%} (não individual por contrato)")
        
        mult = MULTIPLIADORES.get(symbol, 100)
        strike_scales = (
            (1.0, 0.1)
            if symbol == "NG" and fallback_api is not None
            else (1.0,)
        )
        df = parse_option_tables(tables, spot, margin, strike_scales)
        # Remove ruído de ponto flutuante (ex.: 33 * 0.1 = 3.3000000000000003 no NG).
        df["strike"] = df["strike"].round(6)
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

        # [CORREÇÃO 1] Paredes, flip, max pain, regime etc. calculados por uma
        # única função (compute_levels -> select_walls usa o GEX líquido).
        res = compute_levels(df, spot, symbol)
        res["Expiration"] = expiration_date.isoformat()
        zero_gamma = res["ZG"]
        
        if zero_gamma is None:
            print(" ⚠️ Nenhum cruzamento de GEX encontrado na faixa analisada.")
        else:
            print(f" ✅ GEX Flip estimado:{zero_gamma:.2f}")
        return res, df
        
    except Exception as e: 
        print(f" ❌ Erro processamento: {e}")
        return None, None

# ==============================================================================
# SALVAR ARQUIVOS COM SUPORTE AO SUFIXO (_0DTE, _1DTE, _2DTE, _7DTE)
# ==============================================================================
def _csv_field(value):
    """Evita que vírgulas/quebras de linha em textos livres desloquem as colunas
    lidas por índice no NinjaTrader e no dashboard."""
    return str(value if value is not None else "").replace(",", ";").replace("\n", " ").strip()


def _level(value):
    """Strike de nível sem ruído de ponto flutuante (mantém o formato 7600.0)."""
    if value is None:
        return ""
    try:
        return round(float(value), 6)
    except (TypeError, ValueError):
        return value


def save(sym, res, df, suffix=""):
    if not os.path.exists(PASTA_DADOS): 
        os.makedirs(PASTA_DADOS)
    if res:
        file_niveis = os.path.join(PASTA_DADOS, f"NiveisGamma_{sym}{suffix}.csv")
        with open(file_niveis, "w", encoding="utf-8", newline="") as f:
            zero_gamma = f"{res['ZG']:.2f}" if res["ZG"] is not None else ""
            # Coluna 11 (índice 10) NOVA: data do vencimento da fatia, para o
            # dashboard comprovar que 0DTE/1DTE/2DTE/7DTE são datas distintas.
            # Leitores antigos (NinjaTrader) ignoram colunas extras.
            f.write(
                f"{_level(res['CW'])},{_level(res['PW'])},{zero_gamma},"
                f"{_level(res['PG'])},{_level(res['NG'])},{res['CWM']},{res['PWM']},"
                f"{_level(res.get('CW_0DTE')) or 0},{_level(res.get('PW_0DTE')) or 0},"
                f"{_csv_field(res.get('Source', ''))},{_csv_field(res.get('Expiration', ''))}"
            )
        
        file_alvos = os.path.join(PASTA_DADOS, f"AlvosVolatilidade_{sym}{suffix}.csv")
        with open(file_alvos, "w", encoding="utf-8", newline="") as f:
            f.write(f"{_level(res['MP'])},{_level(res['DP'])},{res['Rat']},{res.get('IV', 15.5)},{res['FlowSig']},{res['GexSig']},{res['DPM']},{res['FlowVal']},{res['GexVal']},{res['AlvoUp']},{res['AlvoDown']},{_csv_field(res['Regime'])},{_csv_field(res.get('IVSource', 'IV base assumida'))},{_csv_field(res.get('Source', ''))}")
            
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

    if not os.path.isdir(PASTA_DADOS):
        print("⚠️ Nenhum arquivo gerado para enviar ao Dropbox.")
        return

    print("☁️ Conectando ao Dropbox...")
    dbx = dropbox.Dropbox(app_key=app_key, app_secret=app_secret, oauth2_refresh_token=refresh_token)
    # [CORREÇÃO 7] Upload arquivo a arquivo: uma falha isolada não impede o envio
    # dos demais. Só falha no final, depois de tentar todos.
    falhas = []
    for f in sorted(os.listdir(PASTA_DADOS)):
        filepath = os.path.join(PASTA_DADOS, f)
        if not os.path.isfile(filepath):
            continue
        try:
            with open(filepath, 'rb') as file_data:
                dbx.files_upload(file_data.read(), f"/{f}", mode=dropbox.files.WriteMode.overwrite)
            print(f"✅ Sincronizado: {f}")
        except Exception as e:
            falhas.append(f)
            print(f"❌ Erro no Dropbox ao enviar {f}: {e}")
    if falhas:
        raise RuntimeError(f"Falha ao sincronizar {len(falhas)} arquivo(s) no Dropbox: {', '.join(falhas)}")


# ==============================================================================
# MASTER PROCESSOR (AGREGAÇÃO + TIME TRAVEL)
# ==============================================================================
def process_group(driver, symbol, asset_list):
    print(f"\n🔄 INICIANDO MACRO: {symbol}...")
    time.sleep(4) 
    
    df_master = pd.DataFrame()
    spot_master = 0
    rounding_step = STRIKE_ROUNDING.get(symbol)
    
    # --- PASSO 1: RASPAR TODOS OS VENCIMENTOS (MACRO) ---
    for asset in asset_list:
        try:
            res, df = process(driver, symbol, asset["url"])
        except Exception as e:
            registrar_erro(f"Erro ao extrair {symbol} ({asset['url']}): {e}")
            continue
        if res is None or df is None or df.empty:
            registrar_erro(f"Falha ao extrair a cadeia de opções de {symbol}: {asset['url']}")
            continue
        strike_mult = asset["strike_mult"]
        gex_correction = asset["gex_correcao"]
        # [CORREÇÃO 5 e 6] Escala de proxy centralizada e arredondamento de 5 pts
        # restrito aos índices de pontuação alta (ES, NQ, YM, RTY). CL, GC, ZB,
        # ZN e NG preservam sua grade natural de strikes.
        df = apply_proxy_scaling(df, strike_mult, gex_correction)
        if rounding_step:
            df["strike"] = (df["strike"] / rounding_step).round() * rounding_step

        df_master = pd.concat([df_master, df], ignore_index=True)

        if spot_master == 0:
            spot_master = float(df["spot"].iloc[0])

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
        # [CORREÇÃO 1] Paredes pelo GEX líquido positivo/negativo (select_walls).
        res_agg = compute_levels(df_agg, spot_master, symbol, flip_df=df_master)
    except Exception as e:
        registrar_erro(f"Erro ao consolidar níveis macro de {symbol}: {e}")
        return None, None
    
    # --- PASSO 2: TIME TRAVEL (0DTE, 1DTE, 2DTE, 7DTE) ---
    print(" 🕵️ Iniciando Time Travel para fatias DTE...")
    base_asset = asset_list[0]
    base_url = base_asset["url"]
    dte_strike_mult = base_asset.get("strike_mult", 1)
    dte_gex_correction = base_asset.get("gex_correcao", 1)
    
    now_new_york = datetime.now(ZoneInfo("America/New_York"))
    today_new_york = effective_session_date(now_new_york)
    expirations = []
    try:
        if urlparse(base_url).path.startswith("/etfs-funds/"):
            expirations = extract_equity_expiration_options(
                driver, base_url, today_new_york
            )
        else:
            expirations = extract_futures_expiration_options(
                driver, base_url, today_new_york
            )
    except Exception as e:
        registrar_erro(f"Falha ao listar vencimentos DTE de {symbol}: {e}")

    source_label = next(
        (asset["source_label"] for asset in asset_list if asset.get("source_label")),
        "",
    )
    cw_0dte = None
    pw_0dte = None
    used_expirations = set()
    
    def process_dte(dte, label, suffix=None):
        expiration = select_expiration_for_dte(
            expirations, today_new_york, dte, exclude=used_expirations
        )
        used_expirations.add(expiration["date"])
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
        # [CORREÇÃO 6] Quando a fatia DTE vem de um proxy (ex.: RTY via IWM com
        # strike_mult=10 e gex_correcao=5), aplica a conversão de escala tanto
        # no DataFrame de profile quanto nos níveis (CW, PW, ZG, DP, MP, Alvos).
        if dte_strike_mult != 1 or dte_gex_correction != 1:
            required_cols = {"strike", "ng", "cgex", "pgex", "vol", "coi", "poi"}
            if required_cols.issubset(profile.columns):
                profile = apply_proxy_scaling(
                    profile, dte_strike_mult, dte_gex_correction
                )
                if rounding_step:
                    profile["strike"] = (
                        (profile["strike"] / rounding_step).round() * rounding_step
                    )
                dte_spot = (
                    float(profile["spot"].iloc[0])
                    if "spot" in profile.columns
                    else spot_master
                )
                result = compute_levels(profile, dte_spot, symbol)
            else:
                for key in ("CW", "PW", "ZG", "PG", "NG", "DP", "MP"):
                    if result.get(key) is not None and result[key] < 1000:
                        result[key] = result[key] * dte_strike_mult
        result["Expiration"] = actual_expiration
        result["Source"] = source_label
        if suffix:
            save(symbol, result, profile, suffix)
        return result, profile

    if expirations:
        if any(expiration["date"] == today_new_york for expiration in expirations):
            try:
                # [CORREÇÃO 3] Salva também os arquivos dedicados _0DTE.csv
                res_0dte, _ = process_dte(0, "0DTE", "_0DTE")
                cw_0dte = res_0dte["CW"]
                pw_0dte = res_0dte["PW"]
            except Exception as e:
                registrar_erro(f"Falha no 0DTE de {symbol}: {e}")
        else:
            print(
                f" ⚠️ {symbol} não tem vencimento Futures em {today_new_york}; "
                "0DTE será omitido. O macro e as outras fatias DTE continuarão."
            )
        for dte_days, dte_label, dte_suffix in (
            (1, "1DTE", "_1DTE"),
            (2, "2DTE", "_2DTE"),
            (7, "7DTE", "_7DTE"),
        ):
            try:
                process_dte(dte_days, dte_label, dte_suffix)
            except Exception as e:
                registrar_erro(f"Falha no {dte_label} de {symbol}: {e}")

    res_agg["Source"] = source_label
    res_agg["CW_0DTE"] = cw_0dte
    res_agg["PW_0DTE"] = pw_0dte
    zero_gamma = res_agg["ZG"]
        
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
    inicio_ciclo = time.monotonic()
    
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
            {
                "url": "https://www.barchart.com/etfs-funds/quotes/IWM/options?view=split",
                "strike_mult": 10,
                "gex_correcao": 5,
                "source_label": "IWM proxy for RTY",
            }
        ],
        "NG": [
            {"url": "https://www.barchart.com/futures/quotes/NG*0/options?futuresOptionsView=split", "strike_mult": 1, "gex_correcao": 1}
        ]
    }

    sucessos = []
    d = iniciar_driver()
    if d:
        try:
            for s, urls in ATIVOS_AGREGADOS.items():
                decorrido = time.monotonic() - inicio_ciclo
                if decorrido > MAX_RUN_SECONDS:
                    registrar_erro(
                        f"Orçamento de tempo ({MAX_RUN_SECONDS // 60} min) atingido antes de {s}; "
                        "prosseguindo para o upload no Dropbox com os ativos já coletados."
                    )
                    break
                if not driver_ativo(d):
                    print(" 🔄 Reiniciando sessão do navegador...")
                    try:
                        d.quit()
                    except Exception:
                        pass
                    d = iniciar_driver()
                    if not d:
                        registrar_erro(f"Não foi possível reiniciar o navegador em {s}.")
                        break
                try:
                    r, f = process_group(d, s, urls)
                    if r is None or f is None:
                        registrar_erro(f"Não foi possível gerar os dados completos de {s}.")
                        continue
                    save(s, r, f)
                    sucessos.append(s)
                except Exception as e:
                    registrar_erro(f"Exceção inesperada ao processar {s}: {e}")
        finally:
            try:
                if d:
                    d.quit()
            except Exception:
                pass
    else:
        raise RuntimeError("Não foi possível iniciar o navegador para coletar as opções.")

    if not sucessos:
        raise RuntimeError("Nenhum ativo pôde ser coletado com sucesso neste ciclo.")

    upload_to_dropbox()
    if RUN_ERRORS:
        print(f"⚠️ Ciclo concluído com {len(RUN_ERRORS)} alerta(s) parcial(is):")
        for err in RUN_ERRORS:
            print(f"::warning::{err}")
    print(f"✅ Ciclo de Engenharia Finalizado com Sucesso! Ativos sincronizados: {', '.join(sucessos)}")
