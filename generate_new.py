from collections import OrderedDict
import hashlib
import json
import os

from configFileParser import load_config


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
    prior_condition_from_gender = sex_denom
    prior_condition = priors["Conditions"].get(
        condition.lower(), prior_condition_from_gender)

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


def generate_symtoms_for_sex_race_age(symptom, probability, distribution, next_state, priors, default_state="TerminalState"):
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

    if ((len(distribution.get("sex")) == 0) and (len(distribution.get("age")) == 0) and (len(distribution.get("race")) == 0)):
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

    # Prob (condition | risk factors)
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
                    condition_race = None
                    conditions = []
                    if condition_sex is not None:
                        conditions.append(condition_sex)
                    if condition_age is not None:
                        conditions.append(condition_age)
                    if condition_race is not None:
                        conditions.append(condition_race)

                    if len(conditions) > 1:
                        condition_node = {
                            "condition_type": "And",
                            "conditions": conditions
                        }
                    elif len(conditions) == 1:
                        condition_node = conditions[0]
                    else:
                        condition_node = None

                    p_symp_g_cond_sex_race_age = (
                        probability * sex_prob * age_prob * race_prob
                    ) / (age_denom * sex_denom * race_denom)

                    p_symp_g_cond_sex_race_age = round_val(
                        p_symp_g_cond_sex_race_age)

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

                    # saving transitions
                    transitions.append(a_transition)

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
                        for race_other in othersVal:
                            race_val, item = race_other
                            condition_race = {
                                "condition_type": "Race",
                                "race": item
                            }
                            # do stuff here
                            conditions = []
                            if condition_sex is not None:
                                conditions.append(condition_sex)
                            if condition_age is not None:
                                conditions.append(condition_age)
                            if condition_race is not None:
                                conditions.append(condition_race)

                            if len(conditions) > 1:
                                condition_node = {
                                    "condition_type": "And",
                                    "conditions": conditions
                                }
                            else:
                                condition_node = conditions[0]

                            p_symp_g_cond_sex_race_age = (
                                probability * sex_prob * age_prob * race_prob
                            ) / (age_denom * sex_denom * race_denom)

                            p_symp_g_cond_sex_race_age = round_val(
                                p_symp_g_cond_sex_race_age)

                            # saving transitions
                            transitions.append({
                                "condition": condition_node,
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
                            })

                    else:
                        condition_race = {
                            "condition_type": "Race",
                            "race": distribution.get("race").get(race_key).get("name")
                        }
                        conditions = []
                        if condition_sex is not None:
                            conditions.append(condition_sex)
                        if condition_age is not None:
                            conditions.append(condition_age)
                        if condition_race is not None:
                            conditions.append(condition_race)

                        if len(conditions) > 1:
                            condition_node = {
                                "condition_type": "And",
                                "conditions": conditions
                            }
                        else:
                            condition_node = conditions[0]

                        p_symp_g_cond_sex_race_age = (
                            probability * sex_prob * age_prob * race_prob
                        ) / (age_denom * sex_denom * race_denom)

                        p_symp_g_cond_sex_race_age = round_val(
                            p_symp_g_cond_sex_race_age)

                        # saving transitions
                        transitions.append({
                            "condition": condition_node,
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
                        })

    if default_flag:
        transitions.append({
            "transition": default_state
        })

    return transitions


def generate_synthea_module(symptom_dict, test_condition, priors, incidence_limit=3, noinfection_limit=3, min_delay_years=1, max_delay_years=10, min_symptoms=1):
    """Function for generating the PGM module for a given condition.

    Parameters
    ----------
    symptom_dict : dict
        Dictionnary containing all the symptoms of the database
        with their related characteristics.
    test_condition : dict
        Dictionnary containing information related to the condition
        for which the PGM is being generated.
    priors : dict
        Dictionnary containing information related to the 
        priors associated to age, race, sex categories 
        as well as conditions and symptoms
    incidence_limit: int
        maximum number of time a person can have the condition.
        (default: 3)
    noinfection_limit: int
        Terminate the module if there is `noinfection_limit` consecutive attempts 
        to assign the condition to a person without success.
        (default: 3)
    min_delay_years: int
        Minimum delay in years to wait for performing the next attempt 
        to assign the contion to a person.
        (default: 1)
    max_delay_years: int
        Maximum delay in years to wait for performing the next attempt 
        to assign the contion to a person.
        (default: 10)
    min_symptoms: int
        Minimum number of symptoms to enforce at generation time.
        (default: 1)

    Returns
    -------
    dict
        A ddictionnary describing the PGM of the provided condition.
    """

    # check that symptoms do exist for this module!?
    if not test_condition.get("symptoms"):
        return None

    condition_name = test_condition.get("condition_name")
    condition_slug = test_condition.get("condition_slug")

    potential_infection_transition = "Potential_Infection"
    incidence_counter_transition = "IncidenceCounter"
    incidence_attribute = "count_%s" % condition_slug
    num_symptom_attribute = "count_symptom_%s" % condition_slug
    noinfection_attribute = "noinf_cons_count_%s" % condition_slug
    incidence_limit = incidence_limit
    noinfection_limit = noinfection_limit
    node_infection_name = condition_name.replace(" ", "_") + "_Infection"

    states = OrderedDict()

    # add the initial onset
    states["Initial"] = {
        "type": "Initial",
        "direct_transition": "Init_Cons_NoInf_Counter"
    }

    # add Init_Cons_NoInf_Counter node
    states["Init_Cons_NoInf_Counter"] = {
        "type": "SetAttribute",
        "attribute": noinfection_attribute,
        "value": 0,
        "direct_transition": "Init_Incidence_Counter"
    }

    # add Init_Incidence_Counter node
    states["Init_Incidence_Counter"] = {
        "type": "SetAttribute",
        "attribute": incidence_attribute,
        "value": 0,
        "direct_transition": "Time_Delay"
    }

    # add Potential_Infection node
    states["Time_Delay"] = {
        "type": "Delay",
        "range": {
            "low": 0,
            "high": 60,
            "unit": "months"
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
        "type": "Counter",
        "attribute": noinfection_attribute,
        "action": "increment",
        "conditional_transition": [
            {
                "transition": "TerminalState",
                "condition": {
                    "condition_type": "Attribute",
                    "attribute": noinfection_attribute,
                    "operator": ">=",
                    "value": noinfection_limit
                }
            },
            {
                "transition": "No_Infection_Time_Delay"
            }
        ]
    }

    # add Potential_Infection node
    states["No_Infection_Time_Delay"] = {
        "type": "Delay",
        "range": {
            "low": min_delay_years,
            "high": max_delay_years,
            "unit": "years"
        },
        "direct_transition": potential_infection_transition
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
                "complex_transition": generate_symtoms_for_sex_race_age(
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
        "direct_transition": incidence_counter_transition,
        "condition_onset": node_infection_name
    }

    # let's wait for a year and redo the whole thing!
    states["TreatmentComplete"] = {
        "type": "Delay",
        "range": {
            "low": min_delay_years,
            "high": max_delay_years,
            "unit": "years"
        },
        "direct_transition": "Reset_Cons_NoInf_Counter"
    }

    # reset no infectin counter
    states["Reset_Cons_NoInf_Counter"] = {
        "type": "SetAttribute",
        "attribute": noinfection_attribute,
        "value": 0,
        "direct_transition": potential_infection_transition
    }

    # we won't allow the same patient to fall ill with the same condition more than three times.
    # after the third time, the module terminates
    states[incidence_counter_transition] = {
        "type": "Counter",
        "attribute": incidence_attribute,
        "action": "increment",
        "conditional_transition": [
            {
                "transition": "TerminalState",
                "condition": {
                    "condition_type": "Attribute",
                    "attribute": incidence_attribute,
                    "operator": ">=",
                    "value": incidence_limit
                }
            },
            {
                "transition": "TreatmentComplete"
            }
        ]
    }

    states["TerminalState"] = {
        "type": "Terminal"
    }

    return {
        "name": condition_name,
        "states": states
    }


def generate_synthea_modules(symptom_file, conditions_file, output_dir, config_file="", incidence_limit=3, noinfection_limit=3, min_delay_years=1, max_delay_years=10, min_symptoms=1):
    """Function for generating and save the PGM
    module as a JSON file for all the conditions.

    Parameters
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
    incidence_limit: int
        maximum number of time a person can have the condition.
        (default: 3)
    noinfection_limit: int
        Terminate the module if there is `noinfection_limit` consecutive attempts 
        to assign the condition to a person without success.
        (default: 3)
    min_delay_years: int
        Minimum delay in years to wait for performing the next attempt 
        to assign the contion to a person.
        (default: 1)
    max_delay_years: int
        Maximum delay in years to wait for performing the next attempt 
        to assign the contion to a person.
        (default: 10)
    min_symptoms: int
        Minimum number of symptoms to enforce at generation time.
        (default: 1)

    Returns
    -------
    bool
        True uf the generation process is well peformed otherwise False
    """
    with open(symptom_file) as fp:
        symptoms_data = json.load(fp)

    with open(conditions_file) as fp:
        conditions_data = json.load(fp)

    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)

    priors = load_config(config_file)

    for key, value in conditions_data.items():
        module = generate_synthea_module(
            symptoms_data, value, priors, incidence_limit,
            noinfection_limit, min_delay_years, max_delay_years, min_symptoms
        )
        if module is None:
            continue
        filename = os.path.join(output_dir, "%s.json" % key)

        with open(filename, "w") as fp:
            json.dump(module, fp, indent=4)
    return True