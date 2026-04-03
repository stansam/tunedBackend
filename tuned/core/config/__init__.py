import os
from dotenv import load_dotenv

from tuned.core.config.dev import DevelopmentConfig
from tuned.core.config.prod import ProductionConfig
from tuned.core.config.test import TestingConfig

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
