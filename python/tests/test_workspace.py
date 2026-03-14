from geoclt import Workspace


def test_workspace_create(tmp_path):
    ws = Workspace.create(tmp_path / "ws")
    assert ws.root.exists()
    assert ws.registry_path.exists()
