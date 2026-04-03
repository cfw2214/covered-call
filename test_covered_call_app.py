#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tempfile
import unittest

import covered_call.app as covered_call_app

app = covered_call_app.app


class CoveredCallAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = app.test_client()

    def test_missing_ticker_returns_400(self) -> None:
        response = self.client.get("/api/covered-call")
        self.assertEqual(response.status_code, 400)

    def test_api_returns_json_shape(self) -> None:
        response = self.client.get("/api/covered-call?ticker=AAPL")
        self.assertIn(response.status_code, (200, 502))
        if response.status_code == 200:
            payload = response.get_json()
            self.assertIn("covered_call_assessment", payload)
            self.assertIn("covered_call_assessment_reason", payload)

    def test_index_page_contains_expected_labels(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Sell Covered Call 計算機", body)
        self.assertIn("Covered Call 評估", body)
        self.assertIn("若被履約總獲利（含權利金）", body)
        self.assertIn("履約價-成本價＋權利金＝總獲利", body)
        self.assertIn("OI未平倉量", body)
        self.assertIn("成交難易度", body)
        self.assertIn("保守型", body)
        self.assertIn("Call Wall", body)
        self.assertIn("中庸型", body)
        self.assertIn("激進型", body)
        self.assertIn("本週", body)
        self.assertIn("下週", body)
        self.assertIn("2週後", body)
        self.assertIn("3週後", body)
        self.assertIn("4週後", body)
        self.assertIn("2個月", body)
        self.assertIn("3個月", body)
        self.assertIn("Sell Covered Call 計算機 by我是黑叔 版本v1.2", body)
        self.assertIn('type="checkbox"', body)
        self.assertIn('value="保守型"', body)
        self.assertIn('value="Call Wall"', body)
        self.assertIn('value="中庸型"', body)
        self.assertIn('value="激進型"', body)
        self.assertNotIn('value="全部"', body)
        self.assertIn('value="保守型" checked', body)
        self.assertIn('id="bucket-filters"', body)
        self.assertIn('value="本週" checked', body)
        self.assertIn('value="下週" checked', body)
        self.assertIn('value="2週後" checked', body)
        self.assertIn('value="3週後" checked', body)
        self.assertIn('value="4週後" checked', body)
        self.assertNotIn('value="2個月" checked', body)
        self.assertNotIn('value="3個月" checked', body)
        self.assertIn("以 100 股為 1 單位 covered call 計算。", body)
        self.assertNotIn('type="radio"', body)
        self.assertNotIn("標的摘要", body)
        self.assertLess(body.find('id="summary"'), body.find("<h2>Covered Call 建議</h2>"))

    def test_index_page_contains_mobile_result_hooks(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('id="result-cards"', body)
        self.assertIn("@media (max-width: 767px)", body)

    def test_index_page_contains_mobile_card_labels(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("card-grid", body)
        self.assertIn("card-row", body)
        self.assertIn("成交難易度", body)

    def test_index_page_uses_compact_bucket_filter_group(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('id="bucket-filters"', body)
        self.assertIn("bucket-filter-list", body)
        self.assertIn(".bucket-filter-list { display: flex;", body)
        self.assertNotIn(".bucket-filter-list { display: grid;", body)
        self.assertNotIn("顯示本週有效結算日的 covered call 建議。", body)
        self.assertNotIn("顯示標準 monthly 2 個月 bucket 的 covered call 建議。", body)

    def test_index_page_uses_single_summary_strip(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('id="summary"', body)
        self.assertIn("summary-strip", body)
        self.assertIn("summary-item", body)
        self.assertIn(".summary-strip { display: flex; flex-wrap: wrap; gap: 8px;", body)
        self.assertNotIn("summary-card", body)
        self.assertNotIn("更新時間", body)

    def test_resolve_output_html_path_uses_custom_output_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = covered_call_app.resolve_output_html_path(tmpdir)
            self.assertEqual(output_path.parent.as_posix(), tmpdir)
            self.assertEqual(output_path.name, "covered_call.html")

    def test_api_includes_call_wall_basis_style_when_available(self) -> None:
        response = self.client.get("/api/covered-call?ticker=AAPL")
        self.assertIn(response.status_code, (200, 502))
        if response.status_code == 200:
            payload = response.get_json()
            first_bucket = payload["buckets"][0]
            style_names = [item["style"] for item in first_bucket["styles"]]
            self.assertIn("Call Wall", style_names)


if __name__ == "__main__":
    unittest.main()
