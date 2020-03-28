import configparser


def normalize_priors(priors):
    sumProba = 0.0
    numNone = 0
    for k in priors.keys():
        val = priors[k]
        if val is not None:
            assert val >= 0, "priors should be positive"
            sumProba += val
        else:
            numNone += 1
    if numNone == 0:
        if sumProba != 1.0:
            if sumProba > 0:
                for k in priors.keys():
                    priors[k] /= sumProba
            else:
                remainderProb = remainder / len(priors.keys())
                for k in priors.keys():
                    priors[k] = remainderProb
    else:
        assert sumProba <= 1, "expressed priors should be sum to maximum 1"
        remainder = 1.0 - sumProba
        remainderProb = remainder / numNone
        for k in priors.keys():
            if priors[k] is None:
                priors[k] = remainderProb

    return priors


def convert_to_float(val):
    if (val is None) or (val.strip() == ""):
        return None
    return float(val)


def load_config(filename):
    config = configparser.ConfigParser()
    if (filename is not None) and (filename != ""):
        config.read(filename)

    priors = {}
    priors['Age'] = {
        'age-1-years': None,
        'age-1-4-years': None,
        'age-5-14-years': None,
        'age-15-29-years': None,
        'age-30-44-years': None,
        'age-45-59-years': None,
        'age-60-74-years': None,
        'age-75-years': None,
    }
    priors['Gender'] = {
        'sex-male': None,
        'sex-female': None,
    }
    priors['Race'] = {
        'race-ethnicity-black': None,
        'race-ethnicity-hispanic': None,
        'race-ethnicity-white': None,
        'race-ethnicity-other': None,
        'race-ethnicity-asian': None,
        'race-ethnicity-native': None,
    }
    priors['Conditions'] = {}
    priors['Symptoms'] = {}

    if 'Age' in config:
        for k in priors['Age'].keys():
            priors['Age'][k] = convert_to_float(config['Age'].get(k, None))
    # Normalize prior
    priors['Age'] = normalize_priors(priors['Age'])

    if 'Gender' in config:
        for k in priors['Gender'].keys():
            priors['Gender'][k] = convert_to_float(
                config['Gender'].get(k, None))
    # Normalize prior
    priors['Gender'] = normalize_priors(priors['Gender'])

    if 'Race' in config:
        for k in priors['Race'].keys():
            priors['Race'][k] = convert_to_float(config['Race'].get(k, None))
    # Normalize prior
    priors['Race'] = normalize_priors(priors['Race'])

    if 'Conditions' in config:
        for k in config['Conditions']:
            priors['Conditions'][k.lower()] = convert_to_float(
                config['Conditions'].get(k, '0.5')
            )
            assert (priors['Conditions'][k.lower()] >=
                    0 and priors['Conditions'][k.lower()] <= 1)

    if 'Symptoms' in config:
        for k in config['Symptoms']:
            priors['Symptoms'][k.lower()] = convert_to_float(
                config['Symptoms'].get(k, '0.5')
            )
            assert (priors['Symptoms'][k.lower()] >=
                    0 and priors['Symptoms'][k.lower()] <= 1)

    return priors
