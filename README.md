## Description

The scripts in this project create valid [Synthea]() generic modules generated using disease and symptoms as defined
on [Symcat]()

Sample output of the generated files and modules are included in the `sample_output` directory.

## Usage
This has been tested using Python3, so you would need that at a minimum to run this.

To see the help you should run:
```bash
./main.py -h
``` 

To generate a parsed version of the Symcat symptoms CSV export:
```bash
 ./main.py --parse_symptoms --symptoms_csv <path to symptoms csv file> --output <path_to_output_dir>
```

To generate a parsed version of the Symcat conditions CSV export:
```bash
 ./main.py --parse_conditions --conditions_csv <path to conditions csv file> --output <path_to_output_dir>
```

To generate valid Synthea modules using from previously parsed symptoms and conditions:
```bash
 ./main.py --gen_modules --symptoms_json <path to parsed symptoms> --conditions_json <path to parsed conditions> --output <path_to_output_dir>
```