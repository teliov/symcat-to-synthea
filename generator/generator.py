import json
import os
from .basic_module_generator import BasicModuleGenerator
from .advanced_module_generator import AdvancedModuleGenerator


ADVANCED_MODULE_GENERATOR = 1
BASIC_MODULE_GENERATOR = 2


class GeneratorConfig(object):
    """
    Class for holding config options for the synthea module generator

    Attributes
    ----------
    symptom_file : str
        Path of the JSON file containing all the symptoms of the database
        with their related characteristics.
    conditions_file : str
        Path of the JSON file containing all the conditions of the database
        with their related characteristics.
    output_dir : str
        Path of the directory where the generatd JSON files will be saved.
    config_file : str
        path to the config file containing information related to the
        priors associated to age, race, sex categories
        as well as conditions and symptoms
        (default:"")
    num_history_years: int
        given the target age of a patient, this is the number of years from
        that target age from which pathologies are generated.
        (default: 1)
    min_symptoms: int
        Minimum number of symptoms to enforce at generation time.
        (default: 1)
    prefix: string
        prefix to be preppended to a module's output file name
    """
    symptom_file = None
    conditions_file = None
    output_dir = None
    config_file = ""
    num_history_years = 1
    min_symptoms = 1
    prefix = ""
    generator_mode = ADVANCED_MODULE_GENERATOR


class Generator(object):
    """
    A class for handling the generation of symcat-synthea modules

    Attributes
    ----------
    config: GeneratorConfig
        GeneratorConfig object that holds the configuration parameters for the generator
    """
    def __init__(self, config):
        """

        Parameters
        ----------
        config: GeneratorConfig
        """
        self.config = config

    def generate(self):
        with open(self.config.symptom_file) as fp:
            symptoms_data = json.load(fp)

        with open(self.config.conditions_file) as fp:
            conditions_data = json.load(fp)

        if not os.path.isdir(self.config.output_dir):
            os.mkdir(self.config.output_dir)

        if self.config.generator_mode == BASIC_MODULE_GENERATOR:
            module_generator = BasicModuleGenerator(config=self.config)
        else:
            module_generator = AdvancedModuleGenerator(config=self.config)

        module_generator.generate(conditions_data, symptoms_data)
