### Create .env file with one of the following API keys:
# Please visit https://platform.openai.com/settings/organization/api-keys for OPENAI_API_KEY
OPENAI_API_KEY=
# Please visit https://platform.claude.com/settings/keys for ANTHROPIC_API_KEY
ANTHROPIC_API_KEY=

### Run all example on Windows ###
for /r src %f in (*.py) do uv run python "%f"

### Run all example on Linux ###
ls src/*/*.py | % { uv run python $_ }
