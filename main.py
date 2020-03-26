#! /usr/bin/env python3
import argparse
import json
import os

from generate import generate_synthea_modules
from parse import parse_symcat_conditions, parse_symcat_symptoms

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Symcat-to-Synthea')

    parser.add_argument('--gen_modules', action='store_true')  # generate modules
    parser.add_argument('--parse_symptoms', action='store_true')  # parse symptoms
    parser.add_argument('--parse_conditions', action='store_true')  # parse conditions

    parser.add_argument('--symptoms_csv', help='Symcat CSV export')
    parser.add_argument('--conditions_csv', help='Conditions CSV export')

    parser.add_argument('--symptoms_json', help='Symcat json export')
    parser.add_argument('--conditions_json', help='Symcat conditions export')

    parser.add_argument('--incidence_limit', type=int, default=3,
        help='Number of time a patient may have a condition'
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
        if not args.symptoms_json or not args.conditions_json:
            raise ValueError("You must supply both the parsed symptoms.json and conditions.json file")
        generate_synthea_modules(args.symptoms_json, args.conditions_json, output_dir, args.incidence_limit)
    elif args.parse_symptoms:
        if not args.symptoms_csv:
            raise ValueError("You must supply the symcat exported symptoms CSV file")
        symptoms = parse_symcat_symptoms(args.symptoms_csv)
        with open(os.path.join(output_dir, "symptoms.json"), "w") as fp:
            json.dump(symptoms, fp, indent=4)
    elif args.parse_conditions:
        if not args.conditions_csv:
            raise ValueError("You must supply the symcat exported conditions CSV file")
        conditions = parse_symcat_conditions(args.conditions_csv)
        with open(os.path.join(output_dir, "conditions.json"), "w") as fp:
            json.dump(conditions, fp, indent=4)
    else:
        raise ValueError("You must either generate modules, parse symptoms or parse conditions")

