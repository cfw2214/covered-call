#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import math
from datetime import date, datetime
from typing import Iterable, Optional

import yfinance as yf


TARGET_BUCKETS = [
    ("1週", 7),
    ("2週", 14),
    ("3週", 21),
    ("4週", 28),
    ("2個月", 60),
    ("3個月", 90),
]

STYLE_RULES = {
    "保守型": {"min": 0.10, "max": 0.20, "mid": 0.15},
    "中庸型": {"min": 0.25, "max": 0.35, "mid": 0.30},
    "激進型": {"min": 0.40, "max": 0.55, "mid": 0.475},
}

RISK_FREE_RATE = 0.04


def pick_target_expiry(expiries: Iterable[str], target_days: int, base_date: date) -> Optional[str]:
    valid = []
    for expiry in expiries:
        expiry_date = datetime.strptime(expiry, "%Y-%m-%d").date()
        dte = (expiry_date - base_date).days
        if dte > 0:
            valid.append((abs(dte - target_days), dte, expiry))
    if not valid:
        return None
    valid.sort(key=lambda item: (item[0], item[1]))
    return valid[0][2]


def calculate_annualized_return(premium: float, spot: float, dte: int) -> float:
    if spot <= 0 or dte <= 0:
        return 0.0
    return round((premium / spot) * (365 / dte) * 100, 2)


def option_mid(row: dict) -> float:
    bid = float(row.get("bid") or 0.0)
    ask = float(row.get("ask") or 0.0)
    last_price = float(row.get("lastPrice") or row.get("last_price") or 0.0)
    if bid > 0 and ask > 0:
        return round((bid + ask) / 2.0, 4)
    if last_price > 0:
        return round(last_price, 4)
    return 0.0


def _normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _normal_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def approximate_call_delta(spot: float, strike: float, dte: int, iv: float, rate: float = 0.04) -> float:
    if spot <= 0 or strike <= 0 or dte <= 0:
        return 0.0
    vol = float(iv or 0.0)
    if vol <= 0:
        return 0.0
    t = dte / 365.0
    if t <= 0:
        return 0.0
    try:
        d1 = (math.log(spot / strike) + (rate + 0.5 * vol * vol) * t) / (vol * math.sqrt(t))
    except (ValueError, ZeroDivisionError):
        return 0.0
    return round(_normal_cdf(d1), 4)


def approximate_call_gamma(spot: float, strike: float, dte: int, iv: float, rate: float = RISK_FREE_RATE) -> float:
    if spot <= 0 or strike <= 0 or dte <= 0:
        return 0.0
    vol = float(iv or 0.0)
    if vol <= 0:
        return 0.0
    t = dte / 365.0
    if t <= 0:
        return 0.0
    try:
        d1 = (math.log(spot / strike) + (rate + 0.5 * vol * vol) * t) / (vol * math.sqrt(t))
    except (ValueError, ZeroDivisionError):
        return 0.0
    return _normal_pdf(d1) / (spot * vol * math.sqrt(t))


def pick_candidate_by_style(options: list[dict], style: str) -> Optional[dict]:
    rule = STYLE_RULES[style]
    eligible = [
        option for option in options
        if rule["min"] <= float(option.get("delta") or 0.0) <= rule["max"]
    ]
    if not eligible:
        return None
    eligible.sort(
        key=lambda option: (
            abs(float(option.get("delta") or 0.0) - rule["mid"]),
            -float(option.get("openInterest") or option.get("open_interest") or 0.0),
        )
    )
    return eligible[0]


def calculate_contract_metrics(spot: float, cost_basis: float, dte: int, strike: float, premium: float) -> dict:
    premium_income = round(premium * 100, 2)
    annualized_return = calculate_annualized_return(premium, spot, dte)
    stock_gain = round((strike - cost_basis) * 100, 2)
    max_profit = round(stock_gain + premium_income, 2)
    return {
        "premium_income": premium_income,
        "annualized_return": annualized_return,
        "stock_gain": stock_gain,
        "max_profit": max_profit,
    }


def build_call_wall_style_summary(
    call_wall: float,
    spot: float,
    cost_basis: float,
    dte: int,
    premium: float,
    delta: float,
    open_interest: float = 0.0,
    spread_pct: Optional[float] = None,
) -> dict:
    metrics = calculate_contract_metrics(
        spot=spot,
        cost_basis=cost_basis,
        dte=dte,
        strike=float(call_wall),
        premium=float(premium),
    )
    return {
        "style": "Call Wall基準",
        "available": True,
        "strike": round(float(call_wall), 2),
        "delta": round(float(delta), 3),
        "premium": round(float(premium), 2),
        "suggested_price": round(float(premium), 2),
        "premium_income": metrics["premium_income"],
        "annualized_return": metrics["annualized_return"],
        "max_profit": metrics["max_profit"],
        "open_interest": int(round(float(open_interest or 0.0))),
        "spread_pct": spread_pct,
    }


def _build_unavailable_call_wall_summary(message: str) -> dict:
    return {
        "style": "Call Wall基準",
        "available": False,
        "message": message,
    }


def pick_assessment_bucket(buckets: list[dict]) -> Optional[dict]:
    eligible = [bucket for bucket in buckets if bucket.get("dte")]
    if not eligible:
        return None
    month_like = [bucket for bucket in eligible if 25 <= int(bucket["dte"]) <= 40]
    candidates = month_like or eligible
    return min(candidates, key=lambda bucket: abs(int(bucket["dte"]) - 30))


def classify_covered_call_assessment(bucket: Optional[dict]) -> dict:
    if not bucket:
        return {
            "grade": "🔴 不適合",
            "reason": "查無合適 1 個月資料，暫不建議據此賣出",
        }

    iv_rv_spread = bucket.get("iv_rv_spread_pct")
    iv_rv_ratio = bucket.get("iv_rv_ratio")
    call_yield = bucket.get("call_yield_pct")

    if call_yield is None or iv_rv_spread is None or iv_rv_ratio is None:
        return {
            "grade": "🔴 不適合",
            "reason": "資料不足，暫無法確認收租優勢",
        }

    score = 0
    if iv_rv_spread >= 6.0:
        score += 1
    if iv_rv_ratio >= 1.30:
        score += 1
    if call_yield >= 0.80:
        score += 1

    if score >= 3:
        return {
            "grade": "🟢 適合",
            "reason": "權利金偏貴，收租條件較佳",
        }
    if score >= 2:
        return {
            "grade": "🟡 普通",
            "reason": "權利金尚可，適合保守收租",
        }
    return {
        "grade": "🔴 不適合",
        "reason": "權利金不夠厚，現在賣出吸引力有限",
    }


def _realized_volatility(hist) -> Optional[float]:
    if hist is None or len(hist) < 20:
        return None
    closes = hist["Close"].astype(float)
    returns = (closes / closes.shift(1)).apply(math.log).dropna()
    if returns.empty:
        return None
    daily_std = returns.tail(20).std()
    if daily_std is None or math.isnan(daily_std):
        return None
    return float(daily_std * math.sqrt(252.0))


def _build_option_rows(chain, spot: float, dte: int) -> list[dict]:
    rows = []
    if chain is None or chain.empty:
        return rows
    for _, row in chain.iterrows():
        strike = float(row.get("strike") or 0.0)
        iv = float(row.get("impliedVolatility") or 0.0)
        delta = approximate_call_delta(spot=spot, strike=strike, dte=dte, iv=iv)
        rows.append(
            {
                "strike": strike,
                "bid": float(row.get("bid") or 0.0),
                "ask": float(row.get("ask") or 0.0),
                "lastPrice": float(row.get("lastPrice") or 0.0),
                "openInterest": float(row.get("openInterest") or 0.0),
                "impliedVolatility": iv,
                "delta": delta,
            }
        )
    return rows


def _pick_atm_call_iv(call_rows: list[dict], spot: float) -> Optional[float]:
    if not call_rows:
        return None
    atm = min(call_rows, key=lambda row: abs(float(row["strike"]) - spot))
    iv = float(atm.get("impliedVolatility") or 0.0)
    return iv if iv > 0 else None


def _pick_atm_premium(option_rows: list[dict], spot: float) -> Optional[float]:
    if not option_rows:
        return None
    atm = min(option_rows, key=lambda row: abs(float(row["strike"]) - spot))
    premium = option_mid(atm)
    return premium if premium > 0 else None


def _build_candidate_summary(style: str, candidate: Optional[dict], spot: float, cost_basis: float, dte: int) -> dict:
    if not candidate:
        return {
            "style": style,
            "available": False,
            "message": "暫無合適合約",
        }
    premium = option_mid(candidate)
    metrics = calculate_contract_metrics(
        spot=spot,
        cost_basis=cost_basis,
        dte=dte,
        strike=float(candidate["strike"]),
        premium=premium,
    )
    spread_pct = None
    ask = float(candidate.get("ask") or 0.0)
    bid = float(candidate.get("bid") or 0.0)
    if ask > 0 and bid > 0 and ask >= bid:
        mid = (bid + ask) / 2.0
        if mid > 0:
            spread_pct = round(((ask - bid) / mid) * 100, 2)

    return {
        "style": style,
        "available": True,
        "strike": round(float(candidate["strike"]), 2),
        "delta": round(float(candidate["delta"]), 3),
        "premium": round(premium, 2),
        "suggested_price": round(premium, 2),
        "premium_income": metrics["premium_income"],
        "annualized_return": metrics["annualized_return"],
        "max_profit": metrics["max_profit"],
        "open_interest": int(round(float(candidate.get("openInterest") or 0.0))),
        "spread_pct": spread_pct,
    }


def pick_otm_call_wall_candidate(call_rows: list[dict], spot: float, dte: int) -> Optional[dict]:
    best_row = None
    best_gex = None
    lower = spot * 0.8
    upper = spot * 1.2
    for row in call_rows:
        strike = float(row.get("strike") or 0.0)
        if strike <= spot or strike < lower or strike > upper:
            continue
        oi = float(row.get("openInterest") or 0.0)
        iv = float(row.get("impliedVolatility") or 0.0)
        if oi <= 0 or iv <= 0:
            continue
        gamma = approximate_call_gamma(spot=spot, strike=strike, dte=dte, iv=iv)
        gex = gamma * oi * 100 * spot * spot * 0.01
        if best_gex is None or gex > best_gex:
            best_gex = gex
            best_row = row
    return best_row


def fetch_covered_call_report(ticker: str, cost_basis: Optional[float] = None) -> dict:
    symbol = ticker.strip().upper()
    if not symbol:
        raise ValueError("ticker is required")

    tk = yf.Ticker(symbol)
    hist = tk.history(period="3mo", interval="1d", auto_adjust=False)
    if hist is None or hist.empty:
        raise ValueError("無法取得股價資料")

    spot = float(hist["Close"].dropna().iloc[-1])
    expiries = list(tk.options or [])
    if not expiries:
        raise ValueError("抓不到可用期權到期日")

    base_date = hist.index[-1].date()
    realized_vol = _realized_volatility(hist)
    normalized_cost_basis = float(cost_basis) if cost_basis and cost_basis > 0 else spot

    buckets = []
    for label, target_days in TARGET_BUCKETS:
        expiry = pick_target_expiry(expiries, target_days=target_days, base_date=base_date)
        if not expiry:
            buckets.append(
                {
                    "label": label,
                    "target_expiry": None,
                    "dte": None,
                    "message": "查無合適到期日",
                    "styles": [],
                }
            )
            continue

        expiry_date = datetime.strptime(expiry, "%Y-%m-%d").date()
        dte = max((expiry_date - base_date).days, 1)
        option_chain = tk.option_chain(expiry)
        call_rows = _build_option_rows(option_chain.calls, spot=spot, dte=dte)
        put_rows = _build_option_rows(option_chain.puts, spot=spot, dte=dte)

        atm_iv = _pick_atm_call_iv(call_rows, spot=spot)
        iv_rv_spread = round(((atm_iv - realized_vol) * 100), 2) if atm_iv is not None and realized_vol is not None else None
        iv_rv_ratio = round((atm_iv / realized_vol), 2) if atm_iv is not None and realized_vol not in (None, 0) else None
        put_cost = _pick_atm_premium(put_rows, spot=spot)

        styles = []
        for style in STYLE_RULES:
            candidate = pick_candidate_by_style(call_rows, style)
            styles.append(_build_candidate_summary(style, candidate, spot=spot, cost_basis=normalized_cost_basis, dte=dte))

        call_wall_candidate = pick_otm_call_wall_candidate(call_rows, spot=spot, dte=dte)
        if call_wall_candidate:
            wall_spread_pct = None
            ask = float(call_wall_candidate.get("ask") or 0.0)
            bid = float(call_wall_candidate.get("bid") or 0.0)
            if ask > 0 and bid > 0 and ask >= bid:
                mid = (bid + ask) / 2.0
                if mid > 0:
                    wall_spread_pct = round(((ask - bid) / mid) * 100, 2)
            styles.insert(
                1,
                build_call_wall_style_summary(
                    call_wall=float(call_wall_candidate["strike"]),
                    spot=spot,
                    cost_basis=normalized_cost_basis,
                    dte=dte,
                    premium=option_mid(call_wall_candidate),
                    delta=float(call_wall_candidate.get("delta") or 0.0),
                    open_interest=float(call_wall_candidate.get("openInterest") or 0.0),
                    spread_pct=wall_spread_pct,
                ),
            )
        else:
            styles.insert(1, _build_unavailable_call_wall_summary("暫無合適 Call Wall"))

        conservative = next((row for row in styles if row["style"] == "保守型" and row["available"]), None)
        call_yield = round((float(conservative["premium"]) / spot) * 100, 2) if conservative else None
        put_cost_pct = round((float(put_cost) / spot) * 100, 2) if put_cost else None

        buckets.append(
            {
                "label": label,
                "target_expiry": expiry,
                "dte": dte,
                "iv_rv_spread_pct": iv_rv_spread,
                "iv_rv_ratio": iv_rv_ratio,
                "call_yield_pct": call_yield,
                "put_cost_pct": put_cost_pct,
                "styles": styles,
            }
        )

    assessment = classify_covered_call_assessment(pick_assessment_bucket(buckets))

    return {
        "ticker": symbol,
        "spot": round(spot, 2),
        "cost_basis": round(normalized_cost_basis, 2),
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "buckets": buckets,
        "covered_call_assessment": assessment["grade"],
        "covered_call_assessment_reason": assessment["reason"],
    }
