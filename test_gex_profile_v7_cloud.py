import unittest
from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch

import pandas as pd

from gex_profile_v7_cloud import (
    _time_to_expiry,
    calculate_max_pain,
    find_gex_flip,
    parse_option_tables,
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

    def test_max_pain_minimizes_total_option_payout(self):
        profile = pd.DataFrame({
            "strike": [90.0, 100.0, 110.0],
            "coi": [0.0, 10.0, 0.0],
            "poi": [0.0, 10.0, 0.0],
        })

        self.assertEqual(calculate_max_pain(profile), 100.0)


if __name__ == "__main__":
    unittest.main()
