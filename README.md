## Description

The scripts in this project create valid [Synthea](https://github.com/synthetichealth/synthea) generic modules generated using disease and symptoms as defined
on [Symcat](http://www.symcat.com/)

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

There are other options available when generating synthea modules from parsed conditions and symptoms. What follows is a
brief explanation of these options 

**num_history_years**:

Given the target age of a patient (that is the maximum age he will live while being simulated in Synthea), this is the number of years from that target age moving backward from which pathologies are generated. In other words, if `age` is the target age and `num_history_years` is set to `n`, then the pathologies will only be generated when the patient's age is between [`age - n`, `àge`].
This allows the pathologies to be spread according to Synthea census data. To make it possible, there is a special `json` module file that is generated (`1_update_age_time_to_the_end.json`) which aims at updating the difference between the target age and the current age of a person being simulated. This module needs to run simultaneously with classic condition modules in Synthea for the simulation to work properly.

It is set to a default of 1.

**min_symptoms**:

This flag ensures that every condition has exactly `min_symptoms` number of symptoms. It avoids the scenario where a patient
contracts a condition but shows no symptoms.

**config_file**

The config file is a `.ini` file which can be used to specify probability priors for conditions and symptoms as well as distributions
for age, race and gender.
A sample file is included in the repo (see the `priors.ini` file).
If provided, the priors defined in the config file are used to adjust the probabilities which would eventually be expressed in the
generated modules. 