from computer_use_toolkit import CONTRACT_VERSION
from computer_use_toolkit.contracts import contract_doc_path, extraction_seams_doc_path
from computer_use_toolkit.mcp_server import get_contract_summary



def test_contract_smoke():
    summary = get_contract_summary()
    assert summary["contract_version"] == CONTRACT_VERSION
    assert "click" in summary["public_v1_tools"]
    assert "claim_pending_pointer_action" in summary["admin_v1_tools"]
    assert contract_doc_path().exists()
    assert extraction_seams_doc_path().exists()
