from common.utils.data_args import DataArgs

from common.utils.logger_manager import LoggerManager
from common.utils.file_system_utils import FileSystemUtils
from common.locale.language_manager import LanguageManager
from middleware.bootstrap import Bootstrap
from core.processor import ProcessadorPlanilhas

if __name__ == "__main__":

    try:
        # Initialize and Configure the Data Arguments
        data_args = DataArgs()

        # Configure the Bootstrap
        bootstrap = Bootstrap(data_args)

        # Configure the Toolkit
        language_manager = LanguageManager()
        file_logger = LoggerManager(log_folder="data/output/logs", console_logger="console_logger", prefix="adapta_parser", logger_name="adapta_parser_file_logger").file_logger
        fs_utils = FileSystemUtils(language_manager)

        # Bussiness Logic
        processador = ProcessadorPlanilhas(pasta_entrada=data_args.data_file.input_folder,pasta_saida=data_args.data_file.output_folder, logger=file_logger, language_manager=language_manager, fs_utils=fs_utils)


    except ValueError as e:
        raise ValueError(f"ValueError: {e}. Please check your input arguments.")

    except Exception as e:
        raise Exception(f"An unexpected error occurred: {e}. Please contact support.")

# Example usage:
# python3 adapta_parser/main.py.txt --locale pt_BR --input_folder data/input --output_folder data/output --debug