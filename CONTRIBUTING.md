## Contributing
```bash
git clone https://github.com/vanna-ai/vanna.git
cd vanna/

python3 -m venv venv 
source venv/bin/activate

# install package in editable mode
pip install -e '.[all]' tox pre-commit

# Setup pre-commit hooks
pre-commit install

# List dev targets
tox list

# Run tests
tox -e py310
```
