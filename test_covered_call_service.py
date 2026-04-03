#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from datetime import date

from covered_call import service


class CoveredCallServiceTests(unittest.TestCase):
    def test_classify_tradeability_returns_easy_for_tight_liquid_contract(self) -> None:
        result = service.classify_tradeability(
            bid=1.00,
            ask=1.04,
            open_interest=1200,
            volume=120,
        )
        self.assertEqual(result["grade"], "🟢 容易")
        self.assertIn("價差小", result["reason"])

    def test_classify_tradeability_returns_difficult_for_wide_illiquid_contract(self) -> None:
        result = service.classify_tradeability(
            bid=0.10,
            ask=0.30,
            open_interest=20,
            volume=2,
        )
        self.assertEqual(result["grade"], "🔴 困難")
        self.assertIn("流動性差", result["reason"])

    def test_pick_current_weekly_expiry_returns_same_week_expiry(self) -> None:
        expiry = service.pick_current_weekly_expiry(
            [
                "2026-04-02",  # Thursday, holiday-adjusted weekly expiry
                "2026-04-06",  # Monday
                "2026-04-08",  # Wednesday
                "2026-04-10",  # Friday
                "2026-04-17",  # Friday
            ],
            base_date=date(2026, 4, 2),
        )
        self.assertEqual(expiry, "2026-04-02")

    def test_pick_future_weekly_expiry_ignores_monday_and_wednesday(self) -> None:
        expiry = service.pick_future_weekly_expiry(
            [
                "2026-04-06",  # Monday
                "2026-04-08",  # Wednesday
                "2026-04-10",  # Friday
                "2026-04-17",  # Friday
            ],
            future_index=1,
            base_date=date(2026, 4, 3),
        )
        self.assertEqual(expiry, "2026-04-10")

    def test_pick_future_weekly_expiry_uses_thursday_for_holiday_week(self) -> None:
        expiry = service.pick_future_weekly_expiry(
            [
                "2026-04-02",  # Thursday, Good Friday week
                "2026-04-10",
                "2026-04-17",
            ],
            future_index=1,
            base_date=date(2026, 3, 30),
        )
        self.assertEqual(expiry, "2026-04-10")

    def test_pick_target_monthly_expiry_prefers_standard_monthly_over_quarter_end(self) -> None:
        expiry = service.pick_monthly_bucket_expiry(
            [
                "2026-05-15",  # monthly
                "2026-06-19",  # monthly
                "2026-06-30",  # quarter-end style special expiry
            ],
            month_offset=2,
            base_date=date(2026, 4, 3),
        )
        self.assertEqual(expiry, "2026-06-19")

    def test_pick_target_expiry_prefers_nearest_target_days(self) -> None:
        expiry = service.pick_target_expiry(
            ["2026-04-10", "2026-04-17", "2026-05-01"],
            target_days=14,
            base_date=date(2026, 4, 2),
        )
        self.assertEqual(expiry, "2026-04-17")

    def test_annualized_return_uses_premium_over_spot(self) -> None:
        result = service.calculate_annualized_return(
            premium=2.0,
            spot=100.0,
            dte=30,
        )
        self.assertAlmostEqual(result, 24.33, places=2)

    def test_pick_candidate_by_delta_band_prefers_high_oi_and_closest_delta(self) -> None:
        options = [
            {"strike": 110, "delta": 0.17, "openInterest": 500, "bid": 1.2, "ask": 1.4, "lastPrice": 1.3},
            {"strike": 112, "delta": 0.16, "openInterest": 1200, "bid": 1.0, "ask": 1.2, "lastPrice": 1.1},
        ]
        candidate = service.pick_candidate_by_style(options, "保守型")
        self.assertEqual(candidate["strike"], 112)

    def test_calculate_contract_metrics_returns_expected_fields(self) -> None:
        metrics = service.calculate_contract_metrics(
            spot=100.0,
            cost_basis=90.0,
            dte=30,
            strike=105.0,
            premium=2.0,
        )
        self.assertEqual(metrics["premium_income"], 200.0)
        self.assertAlmostEqual(metrics["max_profit"], 1700.0, places=2)

    def test_classify_covered_call_assessment_returns_green_for_rich_premium(self) -> None:
        bucket = {
            "target_expiry": "2026-05-01",
            "dte": 29,
            "iv_rv_spread_pct": 8.4,
            "iv_rv_ratio": 1.47,
            "call_yield_pct": 1.38,
        }
        result = service.classify_covered_call_assessment(bucket)
        self.assertEqual(result["grade"], "🟢 適合")
        self.assertIn("權利金偏貴", result["reason"])

    def test_classify_covered_call_assessment_returns_red_for_thin_premium(self) -> None:
        bucket = {
            "target_expiry": "2026-05-01",
            "dte": 29,
            "iv_rv_spread_pct": 1.2,
            "iv_rv_ratio": 1.05,
            "call_yield_pct": 0.22,
        }
        result = service.classify_covered_call_assessment(bucket)
        self.assertEqual(result["grade"], "🔴 不適合")
        self.assertIn("權利金不夠厚", result["reason"])

    def test_build_call_wall_style_summary_uses_call_wall_strike(self) -> None:
        summary = service.build_call_wall_style_summary(
            call_wall=270.0,
            spot=250.0,
            cost_basis=240.0,
            dte=30,
            premium=2.0,
            delta=0.3,
            open_interest=1234,
            volume=88,
        )
        self.assertEqual(summary["style"], "Call Wall")
        self.assertTrue(summary["available"])
        self.assertEqual(summary["strike"], 270.0)
        self.assertEqual(summary["premium_income"], 200.0)
        self.assertEqual(summary["open_interest"], 1234)
        self.assertIn("tradeability_grade", summary)
        self.assertIn("tradeability_reason", summary)


if __name__ == "__main__":
    unittest.main()
