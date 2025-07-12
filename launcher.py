import os
import sys
import types

# Настройка путей
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Создаем фейковые модули для относительных импортов
sys.modules['.config'] = types.ModuleType('config')
sys.modules['.database'] = types.ModuleType('database')
sys.modules['.commands'] = types.ModuleType('commands')

# Импортируем реальные модули
from config import Config as _Config
from database import init_db as _init_db
from commands import setup_commands as _setup_commands

# Заполняем фейковые модули реальными объектами
sys.modules['.config'].Config = _Config
sys.modules['.database'].init_db = _init_db
sys.modules['.commands'].setup_commands = _setup_commands

# Запускаем основной скрипт
