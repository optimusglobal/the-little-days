@echo off
cd /d "%~dp0"
npx.cmd -y @playwright/mcp@latest --extension --host 127.0.0.1 --port 8931
