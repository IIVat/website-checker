from . import logger

import configparser


class Config:
    def __init__(self, config_file: str = "config.conf") -> None:
        self.config_file = config_file
        self.polling_interval: float = 10.0
        self.time_window: float = 5.0
        self.batch_size: int = 10

    def load_config(self) -> None:
        config = configparser.ConfigParser()
        try:
            config.read(self.config_file)
            self.polling_interval = self._get_float(config, "stream_settings", "polling_interval", 10.0, 5.0, 300.0)
            self.time_window = self._get_float(config, "stream_settings", "time_window", 5.0, 1.0, None)
            self.batch_size = self._get_int(config, "stream_settings", "batch_size", 10, 1, None)
        except (configparser.Error, ValueError) as e:
            raise ValueError(f"Error loading configuration: {e}")

    def _get_float(self, config, section, option, default, min_value=None, max_value=None):
        try:
            value = config.getfloat(section, option)
            if min_value is not None and value < min_value:
                value = min_value
            if max_value is not None and value > max_value:
                value = max_value
        except (configparser.NoOptionError, configparser.NoSectionError) as err:
            logger.error(f"Error was raised: {err.message}")
            value = default
            logger.info(f"Fallback to default: {option} = {value}")
        return value

    def _get_int(self, config, section, option, default, min_value=None, max_value=None):
        try:
            value = config.getint(section, option)
            if min_value is not None and value < min_value:
                value = min_value
            if max_value is not None and value > max_value:
                value = max_value
        except (configparser.NoOptionError, configparser.NoSectionError):
            value = default
        return value


if __name__ == "__main__":
    # Create an instance of Config
    _config = Config()

    # Load the configuration from config.cfg
    _config.load_config()

    # Access the configuration values
    print(f"Polling Interval: {_config.polling_interval} seconds")
    print(f"Time Window: {_config.time_window} seconds")
    print(f"Batch Size: {_config.batch_size}")
