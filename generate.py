from collections import OrderedDict
import hashlib
import json
import os

from configFileParser import load_config


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


def generate_transition_for_sex_race_age(condition, distribution, next_state, priors, default_state="TerminalState"):
    """Function for defining age-based transitions in the generated PGM module

    Parameters
    ----------
    condition : str
        The name of the condition for which the PGM is being generated.
    distribution : dict
        Dictionnary containing the odd values associated to each age category, 
        race category, and sex category
    next_state : str
        The name of the node to transit in case we sample withing the
        provided distribution    
    priors : dict
        The priors associated to age, race, sex categories as well as conditions and symptoms
    default_state : str
        The name of the node to transit in case we do not sample withing the
        provided distribution (default: "TerminalState").

    Returns
    -------
    transitions: list
        the corresponding list of generated transitions
    """
    age_keys = [
        "age-1-years", "age-1-4-years", "age-5-14-years", "age-15-29-years",
        "age-30-44-years", "age-45-59-years", "age-60-74-years", "age-75-years"
    ]
    race_keys = [
        "race-ethnicity-black", "race-ethnicity-hispanic",
        "race-ethnicity-white", "race-ethnicity-other"
    ]
    race_prior_keys = [
        "race-ethnicity-black", "race-ethnicity-hispanic",
        "race-ethnicity-white", "race-ethnicity-other",
        "race-ethnicity-asian", "race-ethnicity-native",
    ]
    sex_keys = ["sex-male", "sex-female"]

    transitions = []

    # should I include default transition?
    default_flag = False

    # Prob (condition | risk factors)
    sex_denom = sum([
        prob_val(
            distribution.get("sex").get(sex_key).get("odds")
        ) * priors["Gender"][sex_key]
        for sex_key in sex_keys
    ])
    age_denom = sum([
        prob_val(
            distribution.get("age").get(age_key).get("odds")
        ) * priors["Age"][age_key]
        for age_key in age_keys
    ])
    race_denom = sum([
        prob_val(
            distribution.get("race").get(
                "race-ethnicity-other" if race_key in [
                    "race-ethnicity-asian", "race-ethnicity-native"] else race_key
            ).get("odds")
        ) * priors["Race"][race_key]
        for race_key in race_prior_keys
    ])

    # condition priors
    default_prior_condition = 0.5
    prior_condition = priors["Conditions"].get(
        condition.lower(), default_prior_condition)

    assert sex_denom > 0, "the sex denom probability must be greater than 0"
    assert age_denom > 0, "the age denom probability must be greater than 0"
    assert race_denom > 0, "the race denom probability must be greater than 0"

    for sex_key in sex_keys:
        sex_odds = distribution.get("sex").get(sex_key).get("odds")
        sex_prob = prob_val(sex_odds)
        if sex_prob <= 0:
            default_flag = True
            continue

        condition_sex = {
            "condition_type": "Gender",
            "gender": "M" if sex_key == "sex-male" else "F"
        }

        for age_key in age_keys:
            age_odds = distribution.get("age").get(age_key).get("odds")
            age_prob = prob_val(age_odds)
            if age_prob <= 0:
                default_flag = True
                continue

            if age_key == "age-1-years":
                condition_age = {
                    "condition_type": "Age",
                    "operator": "<",
                    "unit": "years",
                    "quantity": 1
                }
            elif age_key == "age-75-years":
                condition_age = {
                    "condition_type": "Age",
                    "operator": ">",
                    "unit": "years",
                    "quantity": 75
                }
            else:
                parts = age_key.split("-")
                age_lower = parts[1]
                age_upper = parts[2]
                condition_age = {
                    "condition_type": "And",
                    "conditions": [
                        {
                            "condition_type": "Age",
                            "operator": ">=",
                            "unit": "years",
                            "quantity": int(age_lower)
                        },
                        {
                            "condition_type": "Age",
                            "operator": "<=",
                            "unit": "years",
                            "quantity": int(age_upper)
                        }
                    ],
                }

            for race_key in race_keys:
                race_odds = distribution.get("race").get(race_key).get("odds")
                race_prob = prob_val(race_odds)
                if race_key == "race-ethnicity-other":
                    # split this into three for : NATIVE, "ASIAN" and "OTHER"
                    # according to synthea
                    othersVal = [
                        ("race-ethnicity-native", "Native"),
                        ("race-ethnicity-asian", "Asian"),
                        ("race-ethnicity-other", "Other"),
                    ]
                    for race_other in othersVal:
                        race_val, item = race_other
                        condition_race = {
                            "condition_type": "Race",
                            "race": item
                        }
                        # do stuff here
                        conditions = [
                            condition_sex, condition_age, condition_race
                        ]
                        condition_node = {
                            "condition_type": "And",
                            "conditions": conditions
                        }

                        p_sex_race_age = sex_prob * age_prob * race_prob
                        p_cond_g_sex_race_age = (p_sex_race_age * prior_condition) / (
                            (sex_denom * age_denom * race_denom)
                        )

                        p_cond_g_sex_race_age = round_val(
                            p_cond_g_sex_race_age)

                        # saving transitions
                        transitions.append({
                            "condition": condition_node,
                            "distributions": [
                                {
                                    "transition": next_state,
                                    "distribution": p_cond_g_sex_race_age
                                },
                                {
                                    "transition": default_state,
                                    "distribution": 1 - p_cond_g_sex_race_age
                                }
                            ]
                        })
                else:
                    condition_race = {
                        "condition_type": "Race",
                        "race": distribution.get("race").get(race_key).get("name")
                    }
                    conditions = [
                        condition_sex, condition_age, condition_race
                    ]
                    condition_node = {
                        "condition_type": "And",
                        "conditions": conditions
                    }

                    p_sex_race_age = sex_prob * age_prob * race_prob
                    p_cond_g_sex_race_age = (p_sex_race_age * prior_condition) / (
                        (sex_denom * age_denom * race_denom)
                    )

                    p_cond_g_sex_race_age = round_val(p_cond_g_sex_race_age)

                    # saving transitions
                    transitions.append({
                        "condition": condition_node,
                        "distributions": [
                            {
                                "transition": next_state,
                                "distribution": p_cond_g_sex_race_age
                            },
                            {
                                "transition": default_state,
                                "distribution": 1 - p_cond_g_sex_race_age
                            }
                        ]
                    })

    if default_flag:
        transitions.append({
            "transition": default_state
        })

    return transitions


def generate_symptoms_for_sex_race_age(symptom, probability, distribution, next_state, priors, default_state="TerminalState"):
    """Function for defining age-based transitions in the generated PGM module
    Parameters
    ----------
    symptom : str
        The name of the symptom for which the transitions is being generated.
    probability : float
        The absolute probablity value of the symtom given the cuurent condition.
    distribution : dict
        Dictionnary containing the odd values associated to each age category,
        race category, and sex category
    next_state : str
        The name of the node to transit in case we sample withing the
        provided distribution
    priors : dict
        The priors associated to age, race, sex categories as well as conditions and symptoms
    default_state : str
        The name of the node to transit in case we do not sample withing the
        provided distribution (default: "TerminalState").
    Returns
    -------
    transitions: list
        the corresponding list of generated transitions
    """
    age_keys = [
        "age-1-years", "age-1-4-years", "age-5-14-years", "age-15-29-years",
        "age-30-44-years", "age-45-59-years", "age-60-74-years", "age-75-years"
    ]

    race_prior_keys = [
        "race-ethnicity-black", "race-ethnicity-hispanic",
        "race-ethnicity-white", "race-ethnicity-other",
        "race-ethnicity-asian", "race-ethnicity-native",
    ]
    sex_keys = ["sex-male", "sex-female"]

    transitions = []

    if ((len(distribution.get("sex")) == 0) and (len(distribution.get("age")) == 0) and (
            len(distribution.get("race")) == 0)):
        probability = round_val(probability)
        transitions.append({
            "distributions": [
                {
                    "transition": next_state,
                    "distribution": probability
                },
                {
                    "transition": default_state,
                    "distribution": 1 - probability
                }
            ]
        })

        return transitions

    # should I include default transition?
    default_flag = False

    sex_dict = distribution.get("sex", {})
    race_dict = distribution.get("race", {})
    age_dict = distribution.get("age", {})

    # Prob (symptom | condition, risk factors)
    sex_denom = sum([
        prob_val(
            sex_dict.get(sex_key).get("odds")
        ) * priors["Gender"][sex_key]
        for sex_key in sex_keys
    ]) if len(sex_dict) > 0 else 1
    age_denom = sum([
        prob_val(
            age_dict.get(age_key).get("odds")
        ) * priors["Age"][age_key]
        for age_key in age_keys
    ]) if len(age_dict) > 0 else 1
    race_denom = sum([
        prob_val(
            race_dict.get(
                "race-ethnicity-other" if race_key in [
                    "race-ethnicity-asian", "race-ethnicity-native"] else race_key
            ).get("odds")
        ) * priors["Race"][race_key]
        for race_key in race_prior_keys
    ]) if len(race_dict) > 0 else 1

    assert sex_denom > 0, "the sex denom probability must be greater than 0"
    assert age_denom > 0, "the age denom probability must be greater than 0"
    assert race_denom > 0, "the race denom probability must be greater than 0"

    fake_sex_key = 'sex-none'
    fake_age_key = 'age-none'
    fake_race_key = 'race-none'

    if len(sex_dict) == 0:
        sex_dict[fake_sex_key] = 1.0

    if len(age_dict) == 0:
        age_dict[fake_age_key] = 1.0

    if len(race_dict) == 0:
        race_dict[fake_race_key] = 1.0

    for sex_key in sex_dict.keys():

        if sex_key == fake_sex_key:  # fake_dick
            sex_prob = 1
            condition_sex = None
        else:
            sex_odds = sex_dict.get(sex_key).get("odds")
            sex_prob = prob_val(sex_odds)
            if sex_prob <= 0:
                default_flag = True
                continue

            condition_sex = {
                "condition_type": "Gender",
                "gender": "M" if sex_key == "sex-male" else "F"
            }

        for age_key in age_dict.keys():
            if age_key == fake_age_key:  # fake_dict
                age_prob = 1
                condition_age = None
            else:

                age_odds = age_dict.get(age_key).get("odds")
                age_prob = prob_val(age_odds)
                if age_prob <= 0:
                    default_flag = True
                    continue

                if age_key == "age-1-years":
                    condition_age = {
                        "condition_type": "Age",
                        "operator": "<",
                        "unit": "years",
                        "quantity": 1
                    }
                elif age_key == "age-75-years":
                    condition_age = {
                        "condition_type": "Age",
                        "operator": ">",
                        "unit": "years",
                        "quantity": 75
                    }
                else:
                    parts = age_key.split("-")
                    age_lower = parts[1]
                    age_upper = parts[2]
                    condition_age = {
                        "condition_type": "And",
                        "conditions": [
                            {
                                "condition_type": "Age",
                                "operator": ">=",
                                "unit": "years",
                                "quantity": int(age_lower)
                            },
                            {
                                "condition_type": "Age",
                                "operator": "<=",
                                "unit": "years",
                                "quantity": int(age_upper)
                            }
                        ],
                    }

            for race_key in race_dict.keys():
                if race_key == fake_race_key:
                    race_prob = 1
                    condition_race = [None]
                else:
                    race_odds = race_dict.get(race_key).get("odds")
                    race_prob = prob_val(race_odds)

                    if race_key == "race-ethnicity-other":
                        # split this into three for : NATIVE, "ASIAN" and "OTHER"
                        # according to synthea
                        othersVal = [
                            ("race-ethnicity-native", "Native"),
                            ("race-ethnicity-asian", "Asian"),
                            ("race-ethnicity-other", "Other"),
                        ]
                        condition_race = []
                        for _, item in othersVal:
                            condition_race.append({
                                "condition_type": "Race",
                                "race": item
                            })
                    else:
                        condition_race = [{
                            "condition_type": "Race",
                            "race": distribution.get("race").get(race_key).get("name")
                        }]

                p_numerator = probability * sex_prob * age_prob * race_prob
                p_denominator = age_denom * sex_denom * race_denom
                p_symp_g_cond_sex_race_age = round_val(
                    p_numerator / p_denominator)

                num_repeat = len(condition_race)

                for idx in range(num_repeat):
                    conditions = []
                    if condition_sex is not None:
                        conditions.append(condition_sex)
                    if condition_age is not None:
                        conditions.append(condition_age)
                    current_condition_race = condition_race[idx]
                    if current_condition_race is not None:
                        conditions.append(current_condition_race)

                    if len(conditions) > 1:
                        condition_node = {
                            "condition_type": "And",
                            "conditions": conditions
                        }
                    elif len(conditions) == 1:
                        condition_node = conditions[0]
                    else:
                        condition_node = None

                    a_transition = {
                        "distributions": [
                            {
                                "transition": next_state,
                                "distribution": p_symp_g_cond_sex_race_age
                            },
                            {
                                "transition": default_state,
                                "distribution": 1 - p_symp_g_cond_sex_race_age
                            }
                        ]
                    }

                    if condition_node is not None:
                        a_transition["condition"] = condition_node

                    transitions.append(a_transition)

    if default_flag:
        transitions.append({
            "transition": default_state
        })

    return transitions


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
    time_keys = [
        "age-1-years", "age-1-5-years", "age-5-15-years", "age-15-30-years",
        "age-30-45-years", "age-45-60-years", "age-60-75-years", "age-75-years"
    ]

    transitions = []
    adjacent_states = {}
    for idx, key in enumerate(time_keys):
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


def generate_synthea_module(symptom_dict, test_condition, priors, config=None):
    """Function for generating the PGM module for a given condition.

    Parameters
    ----------
    symptom_dict : dict
        Dictionary containing all the symptoms of the database
        with their related characteristics.
    test_condition : dict
        Dictionary containing information related to the condition
        for which the PGM is being generated.
    priors : dict
        Dictionary containing information related to the
        priors associated to age, race, sex categories 
        as well as conditions and symptoms
    config: GeneratorConfig
        GeneratorConfig object that holds the configuration parameters for the generator

    Returns
    -------
    dict
        A dictionary describing the PGM of the provided condition.
    """

    # check that symptoms do exist for this module!?
    if not test_condition.get("symptoms"):
        return None

    if config is None:
        config = GeneratorConfig()

    num_history_years = config.num_history_years
    min_symptoms = config.min_symptoms

    condition_name = test_condition.get("condition_name")
    condition_slug = test_condition.get("condition_slug")

    potential_infection_transition = "Potential_Infection"
    incidence_counter_transition = "IncidenceCounter"
    num_symptom_attribute = "count_symptom_%s" % condition_slug
    # history_age_attribute = "history_age_%s" % condition_slug
    history_age_attribute = "age_time_to_the_end"
    node_infection_name = condition_name.replace(" ", "_") + "_Infection"

    states = OrderedDict()

    # add the initial onset
    states["Initial"] = {
        "type": "Initial",
        "direct_transition": "Check_History_Age_Attribute"
    }

    # check if the time history is verified
    states["Check_History_Age_Attribute"] = {
        "type": "Guard",
        "allow": {
            "condition_type": "Attribute",
            "attribute": history_age_attribute,
            "operator": "<=",
            "value": 0
        },
        "direct_transition": potential_infection_transition
    }

    # Add potential infection
    states[potential_infection_transition] = {
        "type": "Simple",
        "complex_transition": generate_transition_for_sex_race_age(
            condition_name, test_condition, node_infection_name, priors, "No_Infection"
        )
    }

    # add No_Infection node
    # we will end this module if a patient does not catch the condition n
    # consecutive times.
    states["No_Infection"] = {
        "type": "Simple",
        "direct_transition": "TerminalState"
    }

    # add the Condition state (a ConditionOnset) stage
    condition_hash = hashlib.sha224(test_condition.get(
        "condition_slug").encode("utf-8")).hexdigest()
    condition_code = {
        "system": "sha224",
        "code": condition_hash,
        "display": condition_name
    }
    next_stage = "Simple_Transition_1"
    if min_symptoms > 0:
        states["Init_Symptom_Counter"] = {
            "type": "SetAttribute",
            "attribute": num_symptom_attribute,
            "value": 0,
            "direct_transition": next_stage
        }
        next_stage = "Init_Symptom_Counter"

    states[node_infection_name] = {
        "type": "ConditionOnset",
        "codes": [condition_code],
        "target_encounter": "Doctor_Visit",
        "remarks": [
            test_condition.get("condition_description"),
            test_condition.get("condition_remarks")
        ],
        "direct_transition": next_stage
    }

    # now we start to model the symptoms, we use
    condition_symptoms = test_condition.get("symptoms")
    keys = [
        [k, float(condition_symptoms.get(k).get("probability")) * 1 / 100]
        for k in condition_symptoms.keys()
    ]

    for idx, key in enumerate(keys):
        key.append(idx)

    # sort symptoms in the ascending order
    keys = sorted(keys, key=lambda x: x[1])

    if len(keys) > 0:
        if min_symptoms > 0:
            states["Init_Symptom_Counter"][
                "direct_transition"] = "Simple_Transition_%d" % (keys[0][2] + 1)
        else:
            states[node_infection_name][
                "direct_transition"] = "Simple_Transition_%d" % (keys[0][2] + 1)

    for idx in range(len(keys)):
        curr_symptom = condition_symptoms.get(keys[idx][0])
        probability = keys[idx][1]
        index = keys[idx][2]
        slug = curr_symptom.get("slug")
        check_on_num_symptoms = False
        if min_symptoms > 0:
            remaining = len(keys) - idx
            if remaining <= min_symptoms:
                check_on_num_symptoms = True

        symptom_definition = symptom_dict.get(slug, None)

        if idx == len(keys) - 1:
            next_target = "Doctor_Visit"
        else:
            next_index = keys[idx + 1][2]
            next_target = "Simple_Transition_%d" % (next_index + 1)

        simple_transition_name = "Simple_Transition_%d" % (index + 1)
        symptom_transition_name = "Symptom_%d" % (index + 1)

        next_stage = next_target
        if min_symptoms > 0:
            inc_symptom = "Inc_Symptom_%d" % (index + 1)
            states[inc_symptom] = {
                "type": "Counter",
                "attribute": num_symptom_attribute,
                "action": "increment",
                "direct_transition": next_stage
            }
            next_stage = inc_symptom

        next_point = next_target
        if check_on_num_symptoms:
            check_symptom = "Check_Symptom_%d" % (index + 1)
            states[check_symptom] = {
                "type": "Simple",
                "conditional_transition": [
                    {
                        "condition": {
                            "condition_type": "Attribute",
                            "attribute": num_symptom_attribute,
                            "operator": "<",
                            "value": min_symptoms
                        },
                        "transition": symptom_transition_name
                    },
                    {
                        "transition": next_point
                    }
                ]
            }
            next_point = check_symptom

        if symptom_definition is None:
            # a symptom which we dont have a definition for?
            slug_hash = hashlib.sha224(slug.encode("utf-8")).hexdigest()
            symptom_transition = {
                "type": "Symptom",
                "symptom": slug,
                "range": {
                    "low": 25,
                    "high": 50
                },
                "condition_codes": [condition_code],
                "symptom_code": {
                    "system": "sha224",
                    "code": slug_hash,
                    "display": slug
                },
                "value_code": {
                    "system": "sha224",
                    "code": slug,
                    "display": "%s (finding)" % slug
                },
                "remarks": [],
                "direct_transition": next_stage
            }
            simple_transition = {
                "type": "Simple",
                "distributed_transition": [
                    {
                        "distribution": probability,
                        "transition": symptom_transition_name
                    },
                    {
                        "distribution": 1 - probability,
                        "transition": next_point
                    }
                ]
            }
        else:
            symptom_transition = {
                "type": "Symptom",
                "symptom": symptom_definition.get("name"),
                "range": {
                    "low": 25,
                    "high": 50
                },
                "condition_codes": [condition_code],
                "symptom_code": {
                    "system": "sha224",
                    "code": symptom_definition.get("hash"),
                    "display": symptom_definition.get("name")
                },
                "value_code": {
                    "system": "sha224",
                    "code": symptom_definition.get("hash"),
                    "display": "%s (finding)" % symptom_definition.get("name")
                },
                "remarks": [
                    symptom_definition.get("description")
                ],
                "direct_transition": next_stage
            }

            simple_transition = {
                "type": "Simple",
                "complex_transition": generate_symptoms_for_sex_race_age(
                    symptom_transition["symptom"], probability,
                    symptom_definition, symptom_transition_name,
                    priors, next_point
                )
            }

        states[simple_transition_name] = simple_transition
        states[symptom_transition_name] = symptom_transition

    # add the encounter state and the Delay state
    states["Doctor_Visit"] = {
        "type": "Encounter",
        "encounter_class": "ambulatory",
        "reason": "%s_Infection" % condition_name,
        "codes": [
            {
                "system": "SNOMED-CT",
                "code": "185345009",
                "display": "Encounter for symptom"
            }
        ],
        "direct_transition": "End_Doctor_Visit"
    }

    # always end the encounter
    states["End_Doctor_Visit"] = {
        "type": "EncounterEnd",
        "direct_transition": "ConditionEnds"
    }

    states["ConditionEnds"] = {
        "type": "ConditionEnd",
        "direct_transition": "TerminalState",
        "condition_onset": node_infection_name
    }

    states["TerminalState"] = {
        "type": "Terminal"
    }

    return {
        "name": condition_name,
        "states": states
    }


def generate_synthea_modules(config):
    """Function for generating and save the PGM
    module as a JSON file for all the conditions.

    Parameters
    ----------
    config : GeneratorConfig
        GeneratorConfig object that holds the configuration parameters for the generator

    Returns
    -------
    bool
        True if the generation process is well performed otherwise an Error would have been raised
    """

    with open(config.symptom_file) as fp:
        symptoms_data = json.load(fp)

    with open(config.conditions_file) as fp:
        conditions_data = json.load(fp)

    if not os.path.isdir(config.output_dir):
        os.mkdir(config.output_dir)

    priors = load_config(config.config_file)

    for key, value in conditions_data.items():
        module = generate_synthea_module(
            symptoms_data, value, priors, config
        )
        if module is None:
            continue
        filename = os.path.join(
            config.output_dir,
            "%s%s.json" % (config.prefix, key)
        )
        with open(filename, "w") as fp:
            json.dump(module, fp, indent=4)

    module = generate_synthea_common_history_module(
        config.num_history_years
    )
    filename = os.path.join(
        config.output_dir,
        "%s%s.json" % (config.prefix, "1_" + module["name"])
    )
    with open(filename, "w") as fp:
        json.dump(module, fp, indent=4)

    return True
