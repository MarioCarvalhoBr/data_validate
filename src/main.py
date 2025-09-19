import src
from src.middleware import Bootstrap
from src.helpers.base import DataArgs
from src.controllers import GeneralContext, ProcessorSpreadsheet

print(f"{src.__welcome__}\n")


def main():
    # Initialize and Configure the Data Arguments
    data_args = DataArgs()

    # Configure the Bootstrap
    Bootstrap(data_args)

    general_context = GeneralContext(data_args=data_args)

    # Bussiness Logic
    ProcessorSpreadsheet(context=general_context)

    # Finalize the General Context
    general_context.finalize()


if __name__ == "__main__":
    main()

# Example usage:
# python3 src/main.py --l pt_BR --o data/output/temp/ --i data/input/data_ground_truth_01/
