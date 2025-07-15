from common.locale.language_manager import LanguageManager
from common.utils.data_args import DataArgs
from common.utils.file_system_utils import FileSystemUtils
from common.utils.logger_manager import LoggerManager
from core.processor import ProcessorSpreadsheet
from middleware.bootstrap import Bootstrap

if __name__ == "__main__":

    try:
        # Initialize and Configure the Data Arguments
        data_args = DataArgs()

        # Configure the Bootstrap
        bootstrap = Bootstrap(data_args)

        # Configure the Toolkit
        language_manager = LanguageManager()
        file_logger = LoggerManager(log_folder="data/output/logs", console_logger="console_logger", prefix="data_validate", logger_name="data_validate_file_logger").file_logger
        fs_utils = FileSystemUtils(language_manager)

        # Bussiness Logic
        processador = ProcessorSpreadsheet(data_args=data_args, logger=file_logger, fs_utils=fs_utils)


    except ValueError as e:
        raise ValueError(f"ValueError: {e}. Please check your input arguments.")

    except Exception as e:
        raise Exception(f"An unexpected error occurred: {e}. Please contact support.")

# Example usage:
# python3 data_validate/main.py --locale pt_BR --input_folder data/input/data_errors/ --output_folder data/output --debug