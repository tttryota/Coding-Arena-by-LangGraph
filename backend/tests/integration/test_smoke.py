"""スモークテスト: テストインフラが正しく動作するか確認。"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient

    from tests.integration.stubs.scenario_llm_transport import ScenarioLlmTransport


class TestInfraSmoke:
    def test_client_can_reach_list_roadmaps(self, client: TestClient) -> None:
        """テスト対象: InfraSmoke の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        response = client.get("/roadmaps")

        assert response.status_code == 200

    def test_scenario_transport_is_wired(
        self,
        integration_container: object,
        scenario_transport: ScenarioLlmTransport,
    ) -> None:
        """テスト対象: InfraSmoke の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        assert integration_container.transport is scenario_transport  # type: ignore[attr-defined]

    def test_llm_clients_use_scenario_transport(
        self,
        integration_container: object,
        scenario_transport: ScenarioLlmTransport,
    ) -> None:
        """テスト対象: InfraSmoke の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        llm = integration_container.roadmap_generation_llm  # type: ignore[attr-defined]
        assert llm._transport is scenario_transport
