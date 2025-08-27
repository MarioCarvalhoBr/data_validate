from data_validate.common.utils.data_args import DataArgs
from data_validate.middleware.bootstrap import Bootstrap

from data_validate.common.locale.language_manager import LanguageManager

from data_validate.config.config import Config
from data_validate.common.utils.file_system_utils import FileSystemUtils
from data_validate.common.utils.logger_manager import LoggerManager

from data_validate.controller.context.general_context import GeneralContext
from data_validate.controller.processor import ProcessorSpreadsheet

if __name__ == "__main__":

    try:
        # Initialize and Configure the Data Arguments
        data_args = DataArgs()

        # Configure the Bootstrap
        bootstrap = Bootstrap(data_args)

        # Configure the Toolkit
        config: Config = Config(lm=LanguageManager())
        fs_utils: FileSystemUtils = FileSystemUtils(lm=LanguageManager())
        file_logger = LoggerManager(log_folder="data/output/logs", console_logger="console_logger", prefix="data_validate", logger_name="data_validate_file_logger").file_logger



        general_context = GeneralContext(config=config, fs_utils=fs_utils, data_args=data_args, logger=file_logger)

        # Bussiness Logic
        processor = ProcessorSpreadsheet(context=general_context)


    except ValueError as e:
        raise ValueError(f"ValueError: {e}. Please check your input arguments.")

    except Exception as e:
        raise Exception(f"An unexpected error occurred: {e}. Please contact support.")

# Example usage:
# python3 data_validate/main.py --l pt_BR --i data/input/data_ground_truth_01/ --o data/output --d