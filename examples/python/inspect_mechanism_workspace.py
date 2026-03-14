from geoclt import Workspace


ws = Workspace.create("runs/demo")
print({"root": str(ws.root), "metadata": ws.metadata})
