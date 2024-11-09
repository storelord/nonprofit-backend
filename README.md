# Backend Server FastAPi

## Installation

1. Install poetry
2. Cd into /server
3. Create a file called `.env` and insert the following: 
   1. `API_KEY=<RANDOMKEY>`. for dev purposes, this random key is expected in the header '`api-key` of request in order to pass security checks.
   2. `OPENAI_API_KEY=sk-...` for access to openai

4. `pyenv install 3.11.9` may be needed
4. `pyenv local 3.11.9` may be needed
4. `python3 -m venv .venv` may be needed
4. `source ./.venv/bin/activate` may be needed
4. (Optional) Configure poetry to install the virtual environment in the directory. Then you can more easily point vscode interpreter settings to this folder for better syntax highlighing `poetry config virtualenvs.in-project true`
5. Install dependancies with `poetry install`
6. Start a shell in the virtual environment with `poetry shell`
7. Run the app `poetry run start` (this doesn't work for some reason)
8. Or run it directly with `poetry run uvicorn main:app --reload`