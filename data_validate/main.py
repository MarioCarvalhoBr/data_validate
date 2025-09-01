import time

from helpers.base.data_args import DataArgs
from data_validate.middleware.bootstrap import Bootstrap

from data_validate.helpers.tools.locale.language_manager import LanguageManager
from data_validate.config.config import Config
from helpers.base.file_system_utils import FileSystemUtils
from helpers.base.logger_manager import LoggerManager

from data_validate.controllers.context.general_context import GeneralContext
from data_validate.controllers.processor import ProcessorSpreadsheet


def main():
    # Initialize and Configure the Data Arguments
    data_args = DataArgs()

    # Configure the Bootstrap
    Bootstrap(data_args)

    # Configure the Toolkit
    config: Config = Config(lm=LanguageManager())
    fs_utils: FileSystemUtils = FileSystemUtils(lm=LanguageManager())
    logger_manager = LoggerManager(
        log_folder="data/output/logs",
        console_logger="console_logger",
        prefix="data_validate",
        logger_name="data_validate_file_logger",
    )
    file_logger = logger_manager.file_logger
    if not data_args.data_action.debug:
        file_logger.disabled = True

    general_context = GeneralContext(
        config=config, fs_utils=fs_utils, data_args=data_args, logger=file_logger
    )

    # Start time measurement
    start_time = time.time()

    # Bussiness Logic
    ProcessorSpreadsheet(context=general_context)

    if not data_args.data_action.no_time:
        print(
            "Tempo total de execução: "
            + str(round(time.time() - start_time, 1))
            + " segundos"
        )

    # Remove log file if not in debug mode
    if not data_args.data_action.debug:
        fs_utils.remove_file(logger_manager.log_file)
    else:
        print("\nLog file created at:", logger_manager.log_file)


if __name__ == "__main__":
    main()

# Example usage:
# python3 data_validate/main.py --l pt_BR --o data/output/temp/ --d --i data/input/data_ground_truth_01/
# python3 data_validate/main.py --l en_US --o data/output/temp/ --d --i data/input/data_ground_truth_01/
