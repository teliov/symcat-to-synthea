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

**incidence_limit**:

This determines how many times a patient is allowed to contract a condition.
Increasing this value would result in more conditions (and as a result more data) being generated for the same number of patients.
However an increased value of the `incidence_limit` also means the generator takes much longer time to generate the same number of patients.
It is set to a default of 3.

**noinfection_limit**:

This determines the limit on how many times synthea's generator should attempt to assign a condition to a patient.
It is set to a default of 3.

**min_delay_years**:

Minimum delay in years to wait for performing the next attempt to assign the condition to a person. This option,
together with the `max_delay_years` option are used to make the condition onset age distribution more uniform across synthea's
age range.
A side effect of setting the `incidence_limit` - especially for conditions which have similar odds for the different age
distributions - is that it becomes highly likely that a generated patient reaches the incidence limit very early on in the life
cycle. This creates a situation where the condition onset age distribution is skewed more towards the young section.
Adjusting this value, together with `max_delay_years` reduces the number of attempts within a particular age distribution
and increases the chances that the condition age distribution is more uniformly spread.

It is set to a default of 1.

**max_delay_years**:

See `min_delay_years` above.
It is set to a default of 80.

**min_symptoms**:

This flag ensures that every condition has exactly `min_symptoms` number of symptoms. It avoids the scenario where a patient
contracts a condition but shows no symptoms.

**config_file**

The config file is a `.ini` file which can be used to specify probability priors for conditions and symptoms as well as distributions
for age, race and gender.
A sample file is included in the repo (see the `priors.ini` file).
If provided, the priors defined in the config file are used to adjust the probabilities which would eventually be expressed in the
generated modules. 