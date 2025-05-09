
# Adapta Parser

Adapta Parser is a Python-based project designed to provide a multilingual calculator and other utilities. This project includes features such as language selection, basic arithmetic operations, and JSON-based localization.

## Table of Contents
- [Installation](#installation)
- [Setting Up the Environment](#setting-up-the-environment)
- [Running the Project](#running-the-project)
- [Running Tests](#running-tests)
- [Generating Documentation](#generating-documentation)
- [Coverage](#coverage)
- [License](#license)

---

## Installation

To get started with Adapta Parser, clone the repository and navigate to the project directory:

```bash
git clone https://github.com/AdaptaBrasil/adapta-parser.git
cd adapta-parser
```

---

## Setting Up the Environment

Ensure you have Python 3.12 or higher installed. Follow these steps to set up the environment:

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

2. Install `poetry`:
   ```bash
   pip install poetry
   ```

3. Use `poetry` to install the project dependencies:
   ```bash
   poetry install
   ```

4. Activate the virtual environment managed by `poetry`:
   ```bash
   poetry shell
   ```

---

## Running the Project

To run the multilingual calculator, execute the following command:

Full arguments:
```bash
python3 -m adapta_parser.main --locale pt_BR --input_folder data/input --output_folder data/output --debug
```

Abbreviated arguments:
```bash
 python3 -m adapta_parser.main --l pt_BR --i data/input/data_ground_truth_01/ --o data/output --d
```

Follow the on-screen instructions to select a language and perform calculations.

---

## Running Tests

To run the test suite, use the following command:

```bash
pytest .
```

Ensure all tests pass before deploying or making changes.

---

## Generating Documentation

To generate project documentation, use `pdoc` with the following command:

```bash
pdoc ./adapta_parser/ -o ./docs --logo "https://avatars.githubusercontent.com/u/141270342?s=400&v=4"
```

The documentation will be available in the `docs` directory.

---

## Coverage

To measure test coverage, use the `coverage` tool. Run the following commands:

1. Run tests with coverage:
   ```bash
   coverage run -m pytest
   ```

2. Generate a coverage report in the terminal:
   ```bash
   coverage report
   ```

3. Generate an HTML coverage report:
   ```bash
   coverage html
   ```
4. (Optional) Generate an ALL coverage report:
   ```bash
   coverage run --source=adapta_parser/ -m pytest -v -s && coverage report -m
   ```

The HTML report will be available in the `htmlcov` directory. Open `htmlcov/index.html` in your browser to view the detailed coverage report.

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.
