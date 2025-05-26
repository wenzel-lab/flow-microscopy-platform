# Create a Python Virtual Environment

```bash
python3 -m venv .venv
```

# Activate the environment

```bash
source .venv/bin/activate
```


# Install the required packages

```bash
pip install -r requirements.txt
```

# Run the application

```bash
flask --app webapp run --host 0.0.0.0 --port 5000
```