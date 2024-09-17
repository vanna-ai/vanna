# Contributing

## Setup
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

## Running the test on a Mac
```bash
tox -e mac
```

## Do this before you submit a PR:

Find the most relevant sample notebook and then replace the install command with:

```bash
%pip install 'git+https://github.com/vanna-ai/vanna@your-branch#egg=vanna[chromadb,snowflake,openai]'
```

Run the necessary cells and verify that it works as expected in a real-world scenario.
