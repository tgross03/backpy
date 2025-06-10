from backpy import TOMLConfiguration, VariableLibrary


class BackupManager:
    def __init__(self):
        self._config: TOMLConfiguration = TOMLConfiguration(
            VariableLibrary().get_variable("config_path")
        )
