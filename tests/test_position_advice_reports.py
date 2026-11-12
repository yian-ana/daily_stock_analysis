"""Regression coverage for malformed LLM position advice blocking reports."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from tests.test_notification import AnalysisResult, NotificationService, _make_config
from src.services.history_service import HistoryService


class PositionAdviceReportsTest(unittest.TestCase):
    def make_result(self, advice):
        return AnalysisResult(
            code="UAMY", name="Antimony", sentiment_score=49,
            trend_prediction="震荡", operation_advice="观望",
            analysis_summary="等待确认", report_language="zh",
            dashboard={"core_conclusion": {
                "one_sentence": "等待确认", "position_advice": advice,
            }},
        )

    @patch("src.notification.get_config")
    def test_malformed_advice_does_not_block_report_paths(self, get_config):
        get_config.return_value = _make_config(report_renderer_enabled=False)
        service = NotificationService()
        history = HistoryService.__new__(HistoryService)
        for advice in ("模型返回了普通文本", ["观望"], True, 42, None):
            with self.subTest(advice=advice):
                result = self.make_result(advice)
                sibling = self.make_result({"no_position": "等待入场", "has_position": "控制风险"})
                sibling.code = "SPCX"
                report = service.generate_dashboard_report([result, sibling])
                self.assertIn("UAMY", report)
                self.assertIn("SPCX", report)
                self.assertIn("控制风险", report)
                self.assertIn("UAMY", service.generate_single_stock_report(result))
                self.assertIn("UAMY", service.generate_wechat_dashboard([result]))
                self.assertIn("UAMY", history._generate_single_stock_markdown(
                    result, SimpleNamespace(created_at=None)))
                self.assertEqual(result.get_position_advice(), "观望")
                self.assertEqual(result.get_position_advice(True), "观望")

    @patch("src.notification.get_config")
    def test_valid_advice_is_preserved(self, get_config):
        get_config.return_value = _make_config(report_renderer_enabled=False)
        result = self.make_result({"no_position": "等待入场", "has_position": "控制风险"})
        report = NotificationService().generate_dashboard_report([result])
        self.assertIn("等待入场", report)
        self.assertIn("控制风险", report)
        self.assertEqual(result.get_position_advice(), "等待入场")
        self.assertEqual(result.get_position_advice(True), "控制风险")
