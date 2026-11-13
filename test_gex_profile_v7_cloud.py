import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pandas as pd

from gex_profile_v7_cloud import (
    _expiration_date,
    _futures_weekly_api_config,
    _time_to_expiry,
    apply_proxy_scaling,
    calculate_max_pain,
    effective_session_date,
    extract_equity_expiration_options,
    find_gex_flip,
    parse_barchart_option_payload,
    parse_futures_expiration_options,
    parse_option_tables,
    parse_treasury_price,
    process,
    process_group,
    save,
    select_expiration_for_dte,
    select_walls,
)


class GammaCalculationTests(unittest.TestCase):
    def test_parser_rejects_strike_values_misread_as_contract_counts(self):
        tables = [{
            "headers": [
                "Call Volume",
                "Call Open Interest",
                "Strike",
                "Put Volume",
                "Put Open Interest",
            ],
            "rows": [
                ["12", "34", "7500.0", "56", "78"],
                ["0", "0", "7503.5", "11", "7503.75"],
                ["7503.5", "0", "7503.75", "16", "0"],
            ],
        }]

        profile = parse_option_tables(tables, spot=7500, margin=1200)

        self.assertEqual(profile["strike"].tolist(), [7500.0])
        self.assertEqual(profile.iloc[0]["coi"], 34)
        self.assertEqual(profile.iloc[0]["poi"], 78)

    def test_barchart_grouped_api_payload_converts_call_put_contracts(self):
        table = parse_barchart_option_payload({
            "data": {
                "7,600.00": [
                    {
                        "optionType": "Call",
                        "volume": "20",
                        "openInterest": "5,737",
                        "strikePrice": "7,600.00",
                    },
                    {
                        "optionType": "Put",
                        "volume": "12",
                        "openInterest": "5,757",
                        "strikePrice": "7,600.00",
                    },
                ],
                "7,625.00": [
                    {
                        "optionType": "Call",
                        "volume": "N/A",
                        "openInterest": "0",
                        "strikePrice": "7,625.00",
                    },
                    {
                        "optionType": "Put",
                        "volume": "3",
                        "openInterest": "4",
                        "strikePrice": "7,625.00",
                    },
                ],
            }
        })

        profile = parse_option_tables([table], spot=7600, margin=1200)

        self.assertEqual(profile["strike"].tolist(), [7600.0, 7625.0])
        self.assertEqual(profile.iloc[0]["c_vol"], 20)
        self.assertEqual(profile.iloc[0]["coi"], 5737)
        self.assertEqual(profile.iloc[0]["p_vol"], 12)
        self.assertEqual(profile.iloc[0]["poi"], 5757)
        self.assertEqual(profile.iloc[1]["c_vol"], 0)
        self.assertEqual(profile.iloc[1]["poi"], 4)

    def test_barchart_payload_without_grouped_data_fails_explicitly(self):
        with self.assertRaisesRegex(ValueError, "não contém dados agrupados"):
            parse_barchart_option_payload({"data": []})

    def test_ng_weekly_route_normalizes_tenfold_barchart_strikes(self):
        payload = {
            "data": {
                "32.000": [
                    {
                        "optionType": "Call",
                        "volume": "N/A",
                        "openInterest": "3",
                        "strikePrice": "32.000",
                    },
                    {
                        "optionType": "Put",
                        "volume": "N/A",
                        "openInterest": "N/A",
                        "strikePrice": "32.000",
                    },
                ],
                "33.000": [
                    {
                        "optionType": "Call",
                        "volume": "N/A",
                        "openInterest": "3",
                        "strikePrice": "33.000",
                    },
                    {
                        "optionType": "Put",
                        "volume": "1",
                        "openInterest": "3",
                        "strikePrice": "33.000",
                    },
                ],
                "34.000": [
                    {
                        "optionType": "Call",
                        "volume": "N/A",
                        "openInterest": "3",
                        "strikePrice": "34.000",
                    },
                    {
                        "optionType": "Put",
                        "volume": "N/A",
                        "openInterest": "N/A",
                        "strikePrice": "34.000",
                    },
                ],
            }
        }

        class FakeDriver:
            def get(self, _url):
                pass

            def execute_script(self, _script):
                pass

            def execute_async_script(self, _script, *_args):
                return payload

        with (
            patch("gex_profile_v7_cloud.get_price", return_value=3.36),
            patch("gex_profile_v7_cloud.time.sleep"),
            patch("gex_profile_v7_cloud._time_to_expiry", return_value=1 / 365),
        ):
            result, profile = process(
                FakeDriver(),
                "NG",
                "https://www.barchart.com/futures/quotes/NGZ26/options/IN2X26"
                "?expirationDate=2026-11-13",
            )

        self.assertIsNotNone(result)
        self.assertEqual(profile["strike"].round(2).tolist(), [3.2, 3.3, 3.4])

    def test_weekly_futures_route_builds_api_config_without_page_settings(self):
        self.assertEqual(
            _futures_weekly_api_config(
                "https://www.barchart.com/futures/quotes/ESZ26/options/MI2X26"
                "?futuresOptionsView=split"
            ),
            {
                "method": "quotes",
                "symbol": "MI2X26",
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
            },
        )

    def test_monthly_futures_route_uses_page_settings(self):
        self.assertIsNone(
            _futures_weekly_api_config(
                "https://www.barchart.com/futures/quotes/ES*0/options"
                "?futuresOptionsView=split"
            )
        )

    def test_equity_expiration_options_accepts_barchart_suffixes_and_filters_past_dates(self):
        class FakeDriver:
            def get(self, url):
                self.url = url

            def execute_script(self, _script):
                return [
                    {
                        "value": "2026-11-10-w",
                        "url": "https://www.barchart.com/options?expiration=2026-11-10-w",
                    },
                    {
                        "value": "2026-11-11-w",
                        "url": "https://www.barchart.com/options?expiration=2026-11-11-w",
                    },
                    {
                        "value": "2026-11-12-w",
                        "url": "https://www.barchart.com/options?expiration=2026-11-12-w",
                    },
                ]

        with patch("gex_profile_v7_cloud.time.sleep"):
            expirations = extract_equity_expiration_options(
                FakeDriver(),
                "https://www.barchart.com/etfs-funds/quotes/IWM/options?view=split",
                date(2026, 11, 11),
            )

        self.assertEqual(
            expirations,
            [
                {
                    "date": date(2026, 11, 11),
                    "url": "https://www.barchart.com/options?expiration=2026-11-11-w",
                },
                {
                    "date": date(2026, 11, 12),
                    "url": "https://www.barchart.com/options?expiration=2026-11-12-w",
                },
            ],
        )

    def test_process_returns_profile_with_expiration_date(self):
        class FakeDriver:
            def get(self, _url):
                pass

            def execute_script(self, _script):
                pass

            def execute_async_script(self, _script, *_args):
                return {
                    "data": {
                        "100.00": [
                            {
                                "optionType": "Call",
                                "volume": "10",
                                "openInterest": "20",
                                "strikePrice": "100.00",
                            },
                            {
                                "optionType": "Put",
                                "volume": "5",
                                "openInterest": "15",
                                "strikePrice": "100.00",
                            },
                        ],
                    }
                }

        with (
            patch("gex_profile_v7_cloud.get_price", return_value=100.0),
            patch("gex_profile_v7_cloud.time.sleep"),
            patch("gex_profile_v7_cloud._time_to_expiry", return_value=1 / 365),
        ):
            result, profile = process(
                FakeDriver(),
                "ES",
                "https://www.barchart.com/futures/quotes/ES*0/options"
                "?expirationDate=2026-11-11",
            )

        self.assertIsNotNone(result)
        self.assertEqual(profile["expiration_date"].tolist(), ["2026-11-11"])
        self.assertEqual(result["DP"], 100.0)
        self.assertEqual(result["DPM"], "15")
        self.assertEqual(result["FlowSig"], "CALLS > PUTS")
        self.assertEqual(result["FlowVal"], "5")
        self.assertEqual(result["GexSig"], "POSITIVE")

    def test_process_selects_highest_combined_call_and_put_volume(self):
        class FakeDriver:
            def get(self, _url):
                pass

            def execute_script(self, _script):
                pass

            def execute_async_script(self, _script, *_args):
                return {
                    "data": {
                        "100.00": [
                            {
                                "optionType": "Call",
                                "volume": "100",
                                "openInterest": "20",
                                "strikePrice": "100.00",
                            },
                        ],
                        "110.00": [
                            {
                                "optionType": "Put",
                                "volume": "200",
                                "openInterest": "30",
                                "strikePrice": "110.00",
                            },
                        ],
                    }
                }

        with (
            patch("gex_profile_v7_cloud.get_price", return_value=100.0),
            patch("gex_profile_v7_cloud.time.sleep"),
            patch("gex_profile_v7_cloud._time_to_expiry", return_value=1 / 365),
        ):
            result, _profile = process(
                FakeDriver(),
                "ES",
                "https://www.barchart.com/futures/quotes/ES*0/options"
                "?expirationDate=2026-11-11",
            )

        self.assertIsNotNone(result)
        self.assertEqual(result["DP"], 110.0)
        self.assertEqual(result["DPM"], "200")
        self.assertEqual(result["FlowSig"], "PUTS > CALLS")
        self.assertEqual(result["FlowVal"], "-100")

    def test_flip_is_interpolated_at_total_exposure_sign_change(self):
        profile = pd.DataFrame([{
            "strike": 100.0,
            "base_strike": 100.0,
            "coi": 1.0,
            "poi": 0.0,
            "time_to_expiry": 1 / 365,
            "iv": 0.2,
            "contract_mult": 1.0,
            "strike_mult": 1.0,
        }])

        with patch(
            "gex_profile_v7_cloud.black_scholes_gamma",
            side_effect=lambda spot, strike, expiry, rate, iv: spot - 100,
        ):
            flip = find_gex_flip(profile, current_spot=100)

        self.assertAlmostEqual(flip, 100, places=8)

    def test_no_flip_returns_none_when_net_exposure_never_changes_sign(self):
        profile = pd.DataFrame([{
            "strike": 100.0,
            "base_strike": 100.0,
            "coi": 1.0,
            "poi": 0.0,
            "time_to_expiry": 1 / 365,
            "iv": 0.2,
            "contract_mult": 1.0,
            "strike_mult": 1.0,
        }])

        with patch(
            "gex_profile_v7_cloud.black_scholes_gamma",
            return_value=1.0,
        ):
            self.assertIsNone(find_gex_flip(profile, current_spot=100))

    def test_time_to_expiry_uses_expiration_close_and_timezone(self):
        now = datetime(2026, 11, 10, 15, 0, tzinfo=timezone.utc)

        with patch(
            "gex_profile_v7_cloud.ZoneInfo",
            return_value=timezone(timedelta(hours=-5)),
        ):
            remaining = _time_to_expiry(date(2026, 11, 11), now=now)

        self.assertGreater(remaining, 1 / 365)
        self.assertLess(remaining, 2 / 365)

    def test_expiration_date_reads_barchart_displayed_expiration(self):
        class FakeDriver:
            def execute_script(self, script):
                if "document.body.innerText" in script:
                    return "37 Days to expiration on 12/18/26"
                self.fail("A valid displayed expiration should not need a fallback.")

        self.assertEqual(
            _expiration_date(
                FakeDriver(),
                "https://www.barchart.com/futures/quotes/ES*0/options",
            ),
            date(2026, 12, 18),
        )

    def test_expiration_date_still_prefers_explicit_iso_query_parameter(self):
        class FakeDriver:
            def execute_script(self, _script):
                self.fail("An explicit expirationDate should not inspect the page.")

        self.assertEqual(
            _expiration_date(
                FakeDriver(),
                "https://www.barchart.com/options?expirationDate=2026-12-18",
            ),
            date(2026, 12, 18),
        )

    def test_expiration_date_parses_spx_weekly_query_parameter(self):
        class FakeDriver:
            def execute_script(self, _script):
                self.fail("A query expiration should not inspect the page.")

        self.assertEqual(
            _expiration_date(
                FakeDriver(),
                "https://www.barchart.com/stocks/quotes/$SPX/options"
                "?view=split&expiration=2026-11-11-w",
            ),
            date(2026, 11, 11),
        )

    def test_expiration_date_parses_spx_displayed_date(self):
        class FakeDriver:
            def execute_script(self, script):
                if "document.body.innerText" in script:
                    return "Exp: 2026-11-11 (1 DTE)"
                self.fail("A displayed expiration should not need a fallback.")

        self.assertEqual(
            _expiration_date(
                FakeDriver(),
                "https://www.barchart.com/stocks/quotes/$SPX/options?view=split",
            ),
            date(2026, 11, 11),
        )

    def test_futures_weekly_routes_are_mapped_to_calendar_expiration_dates(self):
        routes = parse_futures_expiration_options(
            [
                {
                    "weekday": "Wednesday Weekly Options",
                    "options": [
                        {
                            "label": "Week 2: Nov 2026",
                            "value": "/futures/quotes/ESZ26/options/MI2X26",
                        },
                        {
                            "label": "Week 3: Nov 2026",
                            "value": "/futures/quotes/ESZ26/options/MI3X26",
                        },
                        {
                            "label": "Week 1: Dec 2026",
                            "value": "/futures/quotes/ESZ26/options/MI1Z26",
                        },
                    ],
                },
                {
                    "weekday": "Thursday Weekly Options",
                    "options": [
                        {
                            "label": "Week 2: Nov 2026",
                            "value": "/futures/quotes/ESZ26/options/MV7X26",
                        },
                    ],
                },
            ],
            as_of=date(2026, 11, 11),
        )

        self.assertEqual(
            routes,
            [
                {
                    "date": date(2026, 11, 11),
                    "url": "/futures/quotes/ESZ26/options/MI2X26",
                },
                {
                    "date": date(2026, 11, 12),
                    "url": "/futures/quotes/ESZ26/options/MV7X26",
                },
                {
                    "date": date(2026, 11, 18),
                    "url": "/futures/quotes/ESZ26/options/MI3X26",
                },
                {
                    "date": date(2026, 12, 2),
                    "url": "/futures/quotes/ESZ26/options/MI1Z26",
                },
            ],
        )

    def test_dte_selection_uses_calendar_target_instead_of_list_position(self):
        expirations = [
            {"date": expiration, "url": expiration.isoformat()}
            for expiration in (
                date(2026, 11, 11),
                date(2026, 11, 12),
                date(2026, 11, 13),
                date(2026, 11, 16),
                date(2026, 11, 17),
                date(2026, 11, 18),
                date(2026, 11, 19),
                date(2026, 11, 23),
            )
        ]

        selected = select_expiration_for_dte(
            expirations,
            as_of=date(2026, 11, 11),
            dte=7,
        )

        self.assertEqual(selected["date"], date(2026, 11, 18))

    def test_dte_selection_requires_a_real_same_day_expiration_for_zero_dte(self):
        expirations = [
            {"date": date(2026, 11, 12), "url": "next-day"},
        ]

        with self.assertRaisesRegex(RuntimeError, "0DTE"):
            select_expiration_for_dte(
                expirations,
                as_of=date(2026, 11, 11),
                dte=0,
            )

    def test_dte_selection_chooses_nearest_expiration_and_prefers_future_on_tie(self):
        expirations = [
            {"date": date(2026, 11, 16), "url": "before-target"},
            {"date": date(2026, 11, 18), "url": "after-target"},
        ]

        selected = select_expiration_for_dte(
            expirations,
            as_of=date(2026, 11, 11),
            dte=6,
        )

        self.assertEqual(selected["url"], "after-target")

    def test_missing_same_day_expiration_keeps_macro_and_other_dte_outputs(self):
        macro_profile = pd.DataFrame({
            "strike": [100.0],
            "ng": [10.0],
            "nf": [2.0],
            "coi": [3.0],
            "poi": [1.0],
            "cgex": [10.0],
            "pgex": [1.0],
            "c_vol": [2.0],
            "p_vol": [1.0],
            "vol": [3.0],
            "toi": [4.0],
            "spot": [100.0],
            "base_strike": [100.0],
            "time_to_expiry": [1 / 365],
            "iv": [0.2],
            "contract_mult": [1.0],
            "strike_mult": [1.0],
            "expiration_date": ["2026-11-18"],
        })
        dte_expirations = [
            {"date": date(2026, 11, 12), "url": "next-day"},
            {"date": date(2026, 11, 13), "url": "two-day"},
            {"date": date(2026, 11, 18), "url": "seven-day"},
        ]
        process_results = [
            ({"CW": 100.0, "PW": 100.0}, macro_profile),
            *[
                (
                    {"CW": 101.0, "PW": 99.0},
                    pd.DataFrame({"expiration_date": [expiration.isoformat()]}),
                )
                for expiration in (
                    date(2026, 11, 12),
                    date(2026, 11, 13),
                    date(2026, 11, 18),
                )
            ],
        ]

        with (
            patch("gex_profile_v7_cloud.datetime") as datetime_mock,
            patch("gex_profile_v7_cloud.time.sleep"),
            patch(
                "gex_profile_v7_cloud.extract_futures_expiration_options",
                return_value=dte_expirations,
            ),
            patch("gex_profile_v7_cloud.process", side_effect=process_results) as process_mock,
            patch("gex_profile_v7_cloud.find_gex_flip", return_value=100.0),
            patch("gex_profile_v7_cloud.calculate_max_pain", return_value=100.0),
            patch("gex_profile_v7_cloud.save") as save_mock,
        ):
            datetime_mock.now.return_value = datetime(2026, 11, 11, 12, 0)
            result, profile = process_group(
                object(),
                "YM",
                [{
                    "url": "https://www.barchart.com/futures/quotes/YM*0/options",
                    "strike_mult": 1,
                    "gex_correcao": 1,
                }],
            )

        self.assertIsNotNone(result)
        self.assertIsNotNone(profile)
        self.assertIsNone(result["CW_0DTE"])
        self.assertIsNone(result["PW_0DTE"])
        self.assertEqual(result["DP"], 100.0)
        self.assertEqual(result["DPM"], "3")
        self.assertEqual(result["FlowSig"], "CALLS > PUTS")
        self.assertEqual(result["FlowVal"], "2")
        self.assertEqual(process_mock.call_count, 4)
        self.assertEqual(
            [call.args[3] for call in save_mock.call_args_list],
            ["_1DTE", "_2DTE", "_7DTE"],
        )

        with TemporaryDirectory() as output_dir:
            with patch("gex_profile_v7_cloud.PASTA_DADOS", output_dir):
                save("YM", result, profile)
            levels = (Path(output_dir) / "NiveisGamma_YM.csv").read_text()

        self.assertEqual(levels.split(",")[7:9], ["0", "0"])

    def test_rty_proxy_marks_outputs_and_processes_equity_dte_expirations(self):
        macro_profile = pd.DataFrame({
            "strike": [280.0],
            "ng": [10.0],
            "nf": [2.0],
            "coi": [3.0],
            "poi": [1.0],
            "cgex": [10.0],
            "pgex": [1.0],
            "c_vol": [2.0],
            "p_vol": [1.0],
            "vol": [3.0],
            "toi": [4.0],
            "spot": [280.0],
            "base_strike": [280.0],
            "time_to_expiry": [1 / 365],
            "iv": [0.2],
            "contract_mult": [50.0],
            "strike_mult": [10.0],
            "expiration_date": ["2026-11-11"],
        })
        expirations = [
            {"date": expiration, "url": f"iwm-{expiration.isoformat()}"}
            for expiration in (
                date(2026, 11, 11),
                date(2026, 11, 12),
                date(2026, 11, 13),
                date(2026, 11, 18),
            )
        ]
        process_results = [
            ({"CW": 2800.0, "PW": 2800.0}, macro_profile),
            *[
                (
                    {"CW": 2810.0, "PW": 2790.0},
                    pd.DataFrame({"expiration_date": [expiration.isoformat()]}),
                )
                for expiration in (
                    date(2026, 11, 11),
                    date(2026, 11, 12),
                    date(2026, 11, 13),
                    date(2026, 11, 18),
                )
            ],
        ]
        proxy_asset = {
            "url": "https://www.barchart.com/etfs-funds/quotes/IWM/options?view=split",
            "strike_mult": 10,
            "gex_correcao": 5,
            "source_label": "IWM proxy for RTY",
        }

        with (
            patch("gex_profile_v7_cloud.datetime") as datetime_mock,
            patch("gex_profile_v7_cloud.time.sleep"),
            patch(
                "gex_profile_v7_cloud.extract_equity_expiration_options",
                return_value=expirations,
            ) as equity_expirations_mock,
            patch("gex_profile_v7_cloud.extract_futures_expiration_options") as futures_expirations_mock,
            patch("gex_profile_v7_cloud.process", side_effect=process_results),
            patch("gex_profile_v7_cloud.find_gex_flip", return_value=2800.0),
            patch("gex_profile_v7_cloud.calculate_max_pain", return_value=2800.0),
            patch("gex_profile_v7_cloud.save") as save_mock,
        ):
            datetime_mock.now.return_value = datetime(2026, 11, 11, 12, 0)
            result, profile = process_group(object(), "RTY", [proxy_asset])

        self.assertIsNotNone(profile)
        self.assertEqual(result["Source"], "IWM proxy for RTY")
        self.assertEqual(result["IV"], 20.0)
        self.assertEqual(result["IVSource"], "IV base assumida")
        self.assertEqual(result["CW"], 2800.0)
        self.assertEqual(profile["strike"].tolist(), [2800.0])
        equity_expirations_mock.assert_called_once()
        futures_expirations_mock.assert_not_called()
        self.assertEqual(
            [call.args[3] for call in save_mock.call_args_list],
            ["_0DTE", "_1DTE", "_2DTE", "_7DTE"],
        )
        self.assertEqual(
            [call.args[1]["Source"] for call in save_mock.call_args_list],
            ["IWM proxy for RTY"] * 4,
        )

    def test_save_exports_actual_iv_basis_and_source_without_changing_existing_columns(self):
        result = {
            "CW": 2800.0,
            "PW": 2790.0,
            "ZG": 2810.0,
            "PG": 2800.0,
            "NG": 2790.0,
            "CWM": "$100",
            "PWM": "$100",
            "CW_0DTE": None,
            "PW_0DTE": None,
            "MP": 2800.0,
            "DP": 2800.0,
            "Rat": "1.00",
            "IV": 20.0,
            "IVSource": "IV base assumida",
            "FlowSig": "CALLS > PUTS",
            "GexSig": "POSITIVE",
            "DPM": "12",
            "FlowVal": "3",
            "GexVal": "$100",
            "AlvoUp": "2810",
            "AlvoDown": "2790",
            "Regime": "LONG GAMMA",
            "Source": "IWM proxy for RTY",
        }
        profile = pd.DataFrame({
            "strike": [2800.0],
            "ng": [1.0],
            "c_vol": [1.0],
            "p_vol": [0.0],
            "coi": [1.0],
            "poi": [0.0],
        })

        with TemporaryDirectory() as output_dir:
            with patch("gex_profile_v7_cloud.PASTA_DADOS", output_dir):
                save("RTY", result, profile)
            levels = (Path(output_dir) / "NiveisGamma_RTY.csv").read_text().split(",")
            targets = (Path(output_dir) / "AlvosVolatilidade_RTY.csv").read_text().split(",")

        self.assertEqual(levels[7:9], ["0", "0"])
        self.assertEqual(levels[2], "2810.00")
        self.assertEqual(levels[9], "IWM proxy for RTY")
        self.assertEqual(targets[3], "20.0")
        self.assertEqual(targets[11], "LONG GAMMA")
        self.assertEqual(targets[12], "IV base assumida")
        self.assertEqual(targets[13], "IWM proxy for RTY")

    def test_save_exports_missing_gex_flip_as_blank(self):
        result = {
            "CW": 100.0,
            "PW": 90.0,
            "ZG": None,
            "PG": 100.0,
            "NG": 90.0,
            "CWM": "$1",
            "PWM": "$1",
            "MP": 95.0,
            "DP": 100.0,
            "Rat": "1.00",
            "IV": 14.0,
            "IVSource": "IV base assumida",
            "FlowSig": "CALLS = PUTS",
            "GexSig": "NEUTRAL",
            "DPM": "12",
            "FlowVal": "0",
            "GexVal": "$0",
            "AlvoUp": "101",
            "AlvoDown": "99",
            "Regime": "NEUTRAL GAMMA",
        }

        with TemporaryDirectory() as output_dir:
            with patch("gex_profile_v7_cloud.PASTA_DADOS", output_dir):
                save("ES", result, None)
            levels = (Path(output_dir) / "NiveisGamma_ES.csv").read_text().split(",")

        self.assertEqual(levels[2], "")

    def test_max_pain_minimizes_total_option_payout(self):
        profile = pd.DataFrame({
            "strike": [90.0, 100.0, 110.0],
            "coi": [0.0, 10.0, 0.0],
            "poi": [0.0, 10.0, 0.0],
        })

        self.assertEqual(calculate_max_pain(profile), 100.0)

    def test_select_walls_uses_net_gamma_to_prevent_identical_atm_straddle_walls(self):
        # Strike central 7600 tem o maior cgex e pgex bruto (straddle ATM), mas
        # ng quase zero; 7650 é a verdadeira Call Wall líquida e 7550 a Put Wall.
        profile = pd.DataFrame({
            "strike": [7550.0, 7600.0, 7650.0],
            "cgex": [100.0, 1000.0, 600.0],
            "pgex": [700.0, 1050.0, 50.0],
            "ng": [-600.0, -50.0, 550.0],
        })

        cw, pw = select_walls(profile)

        self.assertEqual(cw["strike"], 7650.0)
        self.assertEqual(pw["strike"], 7550.0)
        self.assertNotEqual(cw["strike"], pw["strike"])

    def test_thursday_dte_selection_does_not_duplicate_friday_for_1dte_and_2dte(self):
        expirations = [
            {"date": expiration, "url": expiration.isoformat()}
            for expiration in (
                date(2026, 11, 12),  # quinta
                date(2026, 11, 13),  # sexta
                date(2026, 11, 16),  # segunda
                date(2026, 11, 17),  # terça
                date(2026, 11, 19),  # quinta seguinte
            )
        ]
        as_of = date(2026, 11, 12)
        used = set()
        exp_0dte = select_expiration_for_dte(expirations, as_of, 0, exclude=used)
        used.add(exp_0dte["date"])
        exp_1dte = select_expiration_for_dte(expirations, as_of, 1, exclude=used)
        used.add(exp_1dte["date"])
        exp_2dte = select_expiration_for_dte(expirations, as_of, 2, exclude=used)
        used.add(exp_2dte["date"])
        exp_7dte = select_expiration_for_dte(expirations, as_of, 7, exclude=used)

        self.assertEqual(exp_0dte["date"], date(2026, 11, 12))
        self.assertEqual(exp_1dte["date"], date(2026, 11, 13))
        self.assertEqual(exp_2dte["date"], date(2026, 11, 16))
        self.assertEqual(exp_7dte["date"], date(2026, 11, 19))

    def test_low_price_assets_preserve_natural_strikes_in_macro_aggregation(self):
        ng_profile = pd.DataFrame({
            "strike": [3.2, 3.3, 3.4],
            "ng": [-200.0, 50.0, 300.0],
            "nf": [-1.0, 0.0, 2.0],
            "coi": [1.0, 3.0, 5.0],
            "poi": [4.0, 2.0, 1.0],
            "cgex": [50.0, 150.0, 350.0],
            "pgex": [250.0, 100.0, 50.0],
            "c_vol": [1.0, 1.0, 3.0],
            "p_vol": [2.0, 1.0, 1.0],
            "vol": [3.0, 2.0, 4.0],
            "toi": [5.0, 5.0, 6.0],
            "spot": [3.3, 3.3, 3.3],
            "base_strike": [3.2, 3.3, 3.4],
            "time_to_expiry": [1 / 365] * 3,
            "iv": [0.4] * 3,
            "contract_mult": [10000.0] * 3,
            "strike_mult": [1.0] * 3,
            "expiration_date": ["2026-11-13"] * 3,
        })

        with (
            patch("gex_profile_v7_cloud.datetime") as datetime_mock,
            patch("gex_profile_v7_cloud.time.sleep"),
            patch("gex_profile_v7_cloud.extract_futures_expiration_options", return_value=[]),
            patch("gex_profile_v7_cloud.process", return_value=({"CW": 3.4, "PW": 3.2}, ng_profile)),
            patch("gex_profile_v7_cloud.find_gex_flip", return_value=3.28),
        ):
            datetime_mock.now.return_value = datetime(2026, 11, 12, 12, 0)
            result, agg = process_group(
                object(),
                "NG",
                [{"url": "https://www.barchart.com/futures/quotes/NG*0/options", "strike_mult": 1, "gex_correcao": 1}],
            )

        self.assertEqual(agg["strike"].tolist(), [3.2, 3.3, 3.4])
        self.assertEqual(result["CW"], 3.4)
        self.assertEqual(result["PW"], 3.2)

    def test_rty_dte_slices_scale_iwm_strikes_and_exposures(self):
        iwm_slice = pd.DataFrame({
            "strike": [235.0, 240.0, 245.0],
            "ng": [-500.0, 100.0, 800.0],
            "nf": [-5.0, 2.0, 10.0],
            "coi": [10.0, 20.0, 50.0],
            "poi": [40.0, 15.0, 5.0],
            "cgex": [100.0, 300.0, 900.0],
            "pgex": [600.0, 200.0, 100.0],
            "c_vol": [5.0, 12.0, 20.0],
            "p_vol": [10.0, 10.0, 10.0],
            "vol": [15.0, 22.0, 30.0],
            "toi": [50.0, 35.0, 55.0],
            "spot": [240.0, 240.0, 240.0],
            "base_strike": [235.0, 240.0, 245.0],
            "time_to_expiry": [1 / 365] * 3,
            "iv": [0.2] * 3,
            "contract_mult": [50.0] * 3,
            "strike_mult": [1.0] * 3,
            "expiration_date": ["2026-11-12"] * 3,
        })
        scaled = apply_proxy_scaling(iwm_slice, strike_mult=10, gex_correction=5)
        self.assertEqual(scaled["strike"].tolist(), [2350.0, 2400.0, 2450.0])
        self.assertEqual(scaled["ng"].tolist(), [-2500.0, 500.0, 4000.0])

    def test_after_market_close_session_date_advances_to_next_business_day(self):
        friday_after_close = datetime(2026, 11, 13, 16, 30)
        self.assertEqual(effective_session_date(friday_after_close), date(2026, 11, 16))

    def test_treasury_fractional_price_parses_half_thirty_seconds(self):
        self.assertAlmostEqual(parse_treasury_price("117-16"), 117.5)
        self.assertAlmostEqual(parse_treasury_price("110-085"), 110.0 + 8.5 / 32.0)


if __name__ == "__main__":
    unittest.main()
