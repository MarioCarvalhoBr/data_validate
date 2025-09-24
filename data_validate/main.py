import data_validate
from data_validate.controllers import GeneralContext, ProcessorSpreadsheet
from data_validate.helpers.base import DataArgs
from data_validate.middleware import Bootstrap

print(f"{data_validate.__welcome__}\n")


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
# python3 data_validate/main.py --o data/output/temp/ --i data/input/data_ground_truth_01/
