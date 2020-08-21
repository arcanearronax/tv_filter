### How to Set Up a Development Environment

This project is written in Python **(Python 3.8 or higher)** and uses `pip`.

**Clone the Project**
```bash
virtualenv venv
source venv/bin/activate
```

**Install the Requirements**
```bash
$ pip install -r requirements.txt
```

**Run the Test Server Locally**
```bash
python tvapi/manage.py runserver 0.0.0.0:8080
```


### Running tests
```bash
python -m pytest
```

### Linting checks
```bash
pylint *.py
```

### Formatting & code spell
```bash
black . && codespell --skip=".git,*.log,*.html,*.ico,*.css,demo-pics/,venv/"
```
