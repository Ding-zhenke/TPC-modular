"""Cross-package handler registration test; run with cst-automation installed."""

import pytest


pytestmark = pytest.mark.integration


def test_topology_handlers_register_and_dispatch_with_fake_backend(tmp_path):
    from tpc_service import RunService
    from tpc_service.backends.fake import FakeBackend

    from topo_service import register_topology_handlers

    source = tmp_path / "sample.cst"
    source.write_bytes(b"offline fake project")
    service = RunService(str(tmp_path / "service"), backend=FakeBackend())
    try:
        register_topology_handlers(service)
        project = service.open_project(str(source), copy=False)
        submitted = service.submit(
            "solve", project_id=project["project_id"], params={"run_id": 1})
        finished = service.wait(submitted["job_id"], timeout=10)
        assert finished["status"] == "succeeded"
        result = service.result(submitted["job_id"])
        assert result["status"] == "succeeded"
        assert result["run_identity"]["run_token"].startswith("fake-")
        summary = result["result_summary"]
        assert ("topology_s_parameters" in summary
                or "topology_readback_error" in summary)
    finally:
        service.shutdown(wait=True, timeout=10)
