import unittest
from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch

import pandas as pd

from gex_profile_v7_cloud import (
    _expiration_date,
    _futures_weekly_api_config,
    _time_to_expiry,
    calculate_max_pain,
    find_gex_flip,
    parse_barchart_option_payload,
    parse_futures_expiration_options,
    parse_option_tables,
    process,
    select_expiration_for_dte,
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

    def test_max_pain_minimizes_total_option_payout(self):
        profile = pd.DataFrame({
            "strike": [90.0, 100.0, 110.0],
            "coi": [0.0, 10.0, 0.0],
            "poi": [0.0, 10.0, 0.0],
        })

        self.assertEqual(calculate_max_pain(profile), 100.0)


if __name__ == "__main__":
    unittest.main()
