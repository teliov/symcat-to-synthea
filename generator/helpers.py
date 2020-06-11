from collections import OrderedDict
import configparser


def prob_val(x, ndigits=4):
    """Function for converting odd ratio into probability.

    Parameters
    ----------
    x : float
        the odd ratio value.
    ndigits : int
        Number of decimal places to round to (default: 4).

    Returns
    -------
    float
        the probability value with the corresponding number of decimals.
    """
    assert (x is not None) and (x >= 0)
    return round_val(x / (1 + x), ndigits)


def round_val(x, ndigits=4):
    return round(x, ndigits)


def generate_transition_for_history_attribute(attribute_name, next_state):
    """Function for defining age-based transitions in the generated PGM module
    Parameters
    ----------
    attribute_name : str
        The name of the attribute for testing purposes.
    next_state : str
        The name of the node to transit in case we sample withing the
        provided distribution
    default_state : str
        The name of the node to transit in case we do not sample withing the
        provided distribution (default: "TerminalState").
    Returns
    -------
    transitions: list
        the corresponding list of generated transitions
    nodes: dict
        the associated nodes to the transition being generated.
        These nodes will later be used to update the state dictionnary
        of the current PGM.
    """
    transitions = []
    adjacent_states = {}
    for idx, key in enumerate(AttrKeys.TIME_KEYS):
        if key == "age-1-years":
            next_node_name = "End_Time_LessOrEqual_1"
            curr_transition = {
                "condition": {
                    "condition_type": "Attribute",
                    "attribute": attribute_name,
                    "operator": "<=",
                    "value": 1
                },
                "transition": next_node_name
            }
            state = {
                "type": "Delay",
                "exact": {
                    "quantity": 1,
                    "unit": "months"
                },
                "direct_transition": next_state
            }
        elif key == "age-75-years":
            next_node_name = "End_Time_Greater_75"
            curr_transition = {
                "condition": {
                    "condition_type": "Attribute",
                    "attribute": attribute_name,
                    "operator": ">",
                    "value": 75
                },
                "transition": next_node_name
            }
            state = {
                "type": "Delay",
                "exact": {
                    "quantity": 75,
                    "unit": "years"
                },
                "direct_transition": next_state
            }
        else:
            parts = key.split("-")
            age_lower = parts[1]
            age_upper = parts[2]
            next_node_name = "End_Time_{}_{}".format(age_lower, age_upper)
            curr_transition = {
                "condition": {
                    "condition_type": "And",
                    "conditions": [
                        {
                            "condition_type": "Attribute",
                            "attribute": attribute_name,
                            "operator": ">",
                            "value": int(age_lower)
                        },
                        {
                            "condition_type": "Attribute",
                            "attribute": attribute_name,
                            "operator": "<=",
                            "value": int(age_upper)
                        }
                    ],
                },
                "transition": next_node_name
            }
            state = {
                "type": "Delay",
                "exact": {
                    "quantity": int(age_lower),
                    "unit": "years"
                },
                "direct_transition": next_state
            }
        transitions.append(curr_transition)
        adjacent_states[next_node_name] = state

    return transitions, adjacent_states


def generate_synthea_common_history_module(num_history_years=1):
    """Function for generating the PGM module which aims at setting the attribute
    `age_time_to_the_end` for a given person as a function of his current_age and target_age
    that is: `age_time_to_the_end = target_age - current_age`.

    Parameters
    ----------
    num_history_years: int
        given the target age of a patient, this is the number of years from
        that target year from which pathologoes are generated.
        (default: 1)

    Returns
    -------
    dict
        A ddictionnary describing the PGM of the correspondinf module.
    """
    history_age_attribute = "age_time_to_the_end"

    states = OrderedDict()

    # add the initial onset
    states["Initial"] = {
        "type": "Initial",
        "direct_transition": "History_Age_Attribute"
    }

    # set attrbute based on target age
    states["History_Age_Attribute"] = {
        "type": "SetAttribute",
        "attribute": history_age_attribute,
        "expression": "#{target_age} - #{age} - " + str(num_history_years)
    }

    # time states
    time_conditional_transition, time_states = generate_transition_for_history_attribute(
        history_age_attribute, "Check_Exit"
    )
    states["History_Age_Attribute"][
        "conditional_transition"] = time_conditional_transition
    states.update(time_states)

    # check if the time history is verified
    states["Check_Exit"] = {
        "type": "Simple",
        "conditional_transition": [
            {
                "condition": {
                    "condition_type": "False",
                },
                "transition": "TerminalState"
            },
            {
                "transition": "History_Age_Attribute"
            }
        ]
    }

    states["TerminalState"] = {
        "type": "Terminal"
    }

    return {
        "name": "update_age_time_to_the_end",
        "states": states
    }



class AttrKeys:
    AGE_KEYS = [
            "age-1-years", "age-1-4-years", "age-5-14-years", "age-15-29-years",
            "age-30-44-years", "age-45-59-years", "age-60-74-years", "age-75-years"
    ]
    RACE_KEYS = [
            "race-ethnicity-black", "race-ethnicity-hispanic",
            "race-ethnicity-white", "race-ethnicity-other"
    ]
    RACE_PRIOR_KEYS = [
            "race-ethnicity-black", "race-ethnicity-hispanic",
            "race-ethnicity-white", "race-ethnicity-other",
            "race-ethnicity-asian", "race-ethnicity-native",
    ]
    SEX_KEYS = ["sex-male", "sex-female"]
    TIME_KEYS = [
            "age-1-years", "age-1-5-years", "age-5-15-years", "age-15-30-years",
            "age-30-45-years", "age-45-60-years", "age-60-75-years", "age-75-years"
    ]


class TransitionStates:
    TERMINAL_STATE = "TerminalState"
    NO_INFECTION = "No_Infection"
    TARGET_ENCOUNTER_START = "Doctor_Visit"
    TARGET_ENCOUNTER_END = "End_Doctor_Visit"
    POTENTIAL_INFECTION = "Potential_Infection"


def normalize_priors(priors):
    # normalize the proba values so that they sum to 1
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
                remainderProb = 1.0 / len(priors.keys())
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
    # create an empty config data structure.
    config = configparser.ConfigParser()
    if (filename is not None) and (filename != ""):
        config.read(filename)

    priors = {}
    priors['Age'] = { key: None for key in AttrKeys.AGE_KEYS }
    priors['Gender'] = {key: None for key in AttrKeys.SEX_KEYS }
    priors['Race'] = {key: None for key in AttrKeys.RACE_PRIOR_KEYS }
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
            val = config['Conditions'].get(k, None)
            if (val is None) or val == "":
                val = "0.5"
            priors['Conditions'][k.lower()] = convert_to_float(val)
            assert (priors['Conditions'][k.lower()] >=
                    0 and priors['Conditions'][k.lower()] <= 1)

    if 'Symptoms' in config:
        for k in config['Symptoms']:
            val = config['Symptoms'].get(k, None)
            if (val is None) or val == "":
                val = "0.5"
            priors['Symptoms'][k.lower()] = convert_to_float(val)
            assert (priors['Symptoms'][k.lower()] >=
                    0 and priors['Symptoms'][k.lower()] <= 1)

    return priors
