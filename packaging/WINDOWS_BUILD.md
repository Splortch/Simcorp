# Building the Windows desktop app

A Windows build is produced by the **Build SimCorp Windows EXE** GitHub Actions workflow.

1. Open the repository's **Actions** tab.
2. Select **Build SimCorp Windows EXE**.
3. Choose **Run workflow** to build the current main branch, or open a successful run triggered by a push or pull request.
4. Download the `SimCorp-Windows-x64` artifact. Extract the ZIP and run `SimCorp.exe` from the extracted `SimCorp` folder.

This is a portable folder-based build, not a single-file installer. Keep the other files next to `SimCorp.exe`; they contain the embedded Python runtime and dependencies. Save data is stored under `%LOCALAPPDATA%\SimCorp\simcorp.db`, so it persists across application updates.

The AI team connects to LM Studio at the URL and model configured in the in-app AI settings. LM Studio is optional for launching the game; model-backed decisions require a compatible local server and model.
