#! /usr/bin/env python3
import argparse
import json
import os

from generator.generator import  GeneratorConfig, Generator, ADVANCED_MODULE_GENERATOR
from parse import parse_symcat_conditions, parse_symcat_symptoms

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Symcat-to-Synthea')

    # generate modules
    parser.add_argument('--gen_modules', action='store_true')
    # parse symptoms
    parser.add_argument('--parse_symptoms', action='store_true')
    # parse conditions
    parser.add_argument('--parse_conditions', action='store_true')

    parser.add_argument('--symptoms_csv', help='Symcat CSV export')
    parser.add_argument('--conditions_csv', help='Conditions CSV export')

    parser.add_argument('--symptoms_json', help='Symcat json export')
    parser.add_argument('--conditions_json', help='Symcat conditions export')

    parser.add_argument(
        '--num_history_years', type=int, default=1,
        help='Given the target age of a patient, this is the number of years from '
             'that target year from which pathologoes are generated.'
    )
    parser.add_argument(
        '--min_symptoms', type=int, default=1,
        help='Minimum number of symptoms to enforce at each condition sampling.'
    )
    parser.add_argument(
        '--config_file', type=str, default="",
        help='path to the config file'
    )

    parser.add_argument(
        '--module_prefix', type=str, default="",
        help='Add a prefix to the name of generated modules'
    )

    parser.add_argument(
        '--generator_mode', type=int, default=ADVANCED_MODULE_GENERATOR,
        help="Select which method is to be used in generating the modules. Defaults to the advanced method"
    )

    parser.add_argument('--output', help="Output directory")

    args = parser.parse_args()

    if not args.output:
        output_dir = os.getcwd()
    else:
        output_dir = args.output

    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)

    if args.gen_modules:
        # we're generating modules
        config = GeneratorConfig()
        config.output_dir = output_dir
        config.symptom_file = args.symptoms_json
        config.conditions_file = args.conditions_json
        config.config_file = args.config_file
        config.num_history_years = args.num_history_years
        config.min_symptoms = args.min_symptoms
        config.prefix = args.module_prefix
        config.generator_mode = args.generator_mode

        if not args.symptoms_json or not args.conditions_json:
            raise ValueError(
                "You must supply both the parsed symptoms.json and conditions.json file"
            )
        generator = Generator(config)
        generator.generate()
    elif args.parse_symptoms:
        if not args.symptoms_csv:
            raise ValueError(
                "You must supply the symcat exported symptoms CSV file"
            )
        symptoms = parse_symcat_symptoms(args.symptoms_csv)
        with open(os.path.join(output_dir, "symptoms.json"), "w") as fp:
            json.dump(symptoms, fp, indent=4)
    elif args.parse_conditions:
        if not args.conditions_csv:
            raise ValueError(
                "You must supply the symcat exported conditions CSV file")
        conditions = parse_symcat_conditions(args.conditions_csv)
        with open(os.path.join(output_dir, "conditions.json"), "w") as fp:
            json.dump(conditions, fp, indent=4)
    else:
        raise ValueError(
            "You must either generate modules, parse symptoms or parse conditions"
        )
