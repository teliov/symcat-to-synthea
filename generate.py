from collections import OrderedDict
import hashlib
import json
import os


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
    return round(x / (1 + x), ndigits)


def generate_transition_for_age(condition, age_distribution, next_state, default_state="TerminalState"):
    """Function for defining age-based transitions in the generated PGM module

    Parameters
    ----------
    condition : str
        The name of the condition for which the PGM is being generated.
    age_distribution : dict
        Dictionnary containing the odd values associated to each age category.
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
    age_keys = [
        "age-1-years", "age-1-4-years", "age-5-14-years", "age-15-29-years",
        "age-30-44-years", "age-45-59-years", "age-60-74-years", "age-75-years"
    ]

    transitions = []
    adjacent_states = {}
    # should I include default transition?
    default_flag = False
    for idx, key in enumerate(age_keys):
        odds = age_distribution.get(key).get("odds")
        prob = prob_val(odds)

        if prob <= 0:
            default_flag = True
        else:
            if key == "age-1-years":
                next_node_name = "Ages_Less_1"
                curr_transition = {
                    "condition": {
                        "condition_type": "Age",
                        "operator": "<",
                        "unit": "years",
                        "quantity": 1
                    },
                    "transition": next_node_name
                }
                state = {
                    "type": "Simple",
                    "distributed_transition": [
                        {
                            "transition": next_state,
                            "distribution": prob
                        },
                        {
                            "transition": default_state,
                            "distribution": 1 - prob
                        }
                    ],
                    "remarks": [
                        "{} have an approx lifetime risk of {} of {}%.".format(
                            "People with less than 1 year",
                            condition,
                            prob * 100
                        )
                    ]
                }
            elif key == "age-75-years":
                next_node_name = "Ages_75_More"
                curr_transition = {
                    "condition": {
                        "condition_type": "Age",
                        "operator": ">=",
                        "unit": "years",
                        "quantity": 75
                    },
                    "transition": next_node_name
                }
                state = {
                    "type": "Simple",
                    "distributed_transition": [
                        {
                            "transition": next_state,
                            "distribution": prob
                        },
                        {
                            "transition": default_state,
                            "distribution": 1 - prob
                        }
                    ],
                    "remarks": [
                        "{} have an approx lifetime risk of {} of {}%.".format(
                            "People with 75 years or more",
                            condition,
                            prob * 100
                        )
                    ]
                }
            else:
                parts = key.split("-")
                age_lower = parts[1]
                age_upper = parts[2]
                next_node_name = "Ages_{}_{}".format(age_lower, age_upper)
                curr_transition = {
                    "condition": {
                        "condition_type": "And",
                        "conditions": [
                            {
                                "condition_type": "Age",
                                "operator": ">=",
                                "unit": "years",
                                "quantity": age_lower
                            },
                            {
                                "condition_type": "Age",
                                "operator": "<=",
                                "unit": "years",
                                "quantity": age_upper
                            }
                        ],
                    },
                    "transition": next_node_name
                }
                state = {
                    "type": "Simple",
                    "distributed_transition": [
                        {
                            "transition": next_state,
                            "distribution": prob
                        },
                        {
                            "transition": default_state,
                            "distribution": 1 - prob
                        }
                    ],
                    "remarks": [
                        "People with age between {} and {} years have an approx lifetime risk of {} of {}%.".format(
                            age_lower,
                            age_upper,
                            condition,
                            prob * 100
                        )
                    ]
                }
            transitions.append(curr_transition)
            adjacent_states[next_node_name] = state

        if (idx == len(age_keys) - 1) and default_flag:
            transitions.append({
                "transition": default_state
            })

    return transitions, adjacent_states


def generate_transition_for_sex(condition, sex_distribution, next_state, default_state="TerminalState"):
    """Function for defining sex-based transitions in the generated PGM module

    Parameters
    ----------
    condition : str
        The name of the condition for which the PGM is being generated.
    sex_distribution : dict
        Dictionnary containing the odd values associated to each sex category.
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
    male_odds = float(sex_distribution.get("sex-male").get("odds"))
    female_odds = float(sex_distribution.get("sex-female").get("odds"))

    male_prob = prob_val(male_odds)
    female_prob = prob_val(female_odds)

    probabilities = [male_prob, female_prob]

    transition = []
    adjacent_states = {}
    # should I include default transition?
    default_flag = False
    for idx in range(len(probabilities)):
        if probabilities[idx] > 0:
            next_node_name = "Male" if idx == 0 else "Female"
            transition.append({
                "condition": {
                    "condition_type": "Gender",
                    "gender": "M" if idx == 0 else "F"
                },
                "transition": next_node_name
            })

            state = {
                "type": "Simple",
                "distributed_transition": [
                    {
                        "distribution": probabilities[idx],
                        "transition": next_state
                    },
                    {
                        "distribution": 1 - probabilities[idx],
                        "transition": default_state
                    }
                ],
                "remarks": [
                    "{} have an approx lifetime risk of {} of {}%.".format(
                        "Men" if idx == 0 else "Women",
                        condition,
                        probabilities[idx] * 100
                    )
                ]
            }
            adjacent_states[next_node_name] = state
        else:
            default_flag = True

        if (idx == len(probabilities) - 1) and default_flag:
            transition.append({
                "transition": default_state
            })

    return transition, adjacent_states


def generate_transition_for_race(condition, race_distribution, next_state, default_state="TerminalState"):
    """Function for defining race-based transitions in the generated PGM module

    Parameters
    ----------
    condition : str
        The name of the condition for which the PGM is being generated.
    race_distribution : dict
        Dictionnary containing the odd values associated to each race category.
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
    race_keys = ["race-ethnicity-black", "race-ethnicity-hispanic",
                 "race-ethnicity-white", "race-ethnicity-other"]

    transitions = []
    adjacent_states = {}

    for key in race_keys:
        odds = float(race_distribution.get(key).get("odds"))
        prob = prob_val(odds)

        if key == "race-ethnicity-other":
            # split this into three for : NATIVE, "ASIAN" and "OTHER" according
            # to synthea
            for idx, item in enumerate(["Native", "Asian", "Other"]):
                next_node_name = "Race_{}".format(item)
                curr_transition = {
                    "condition": {
                        "condition_type": "Race",
                        "race": item
                    },
                    "transition": next_node_name
                }
                transitions.append(curr_transition)

                state = {
                    "type": "Simple",
                    "distributed_transition": [
                        {
                            "transition": next_state,
                            "distribution": prob
                        },
                        {
                            "transition": default_state,
                            "distribution": 1 - prob
                        }
                    ],
                    "remarks": [
                        "{} have an approx lifetime risk of {} of {}%.".format(
                            item + " people" if item != "Other" else "People from other races",
                            condition,
                            prob * 100
                        )
                    ]
                }
                adjacent_states[next_node_name] = state
        else:
            next_node_name = "Race_{}".format(
                race_distribution.get(key).get("name")
            )
            curr_transition = {
                "condition": {
                    "condition_type": "Race",
                    "race": race_distribution.get(key).get("name")
                },
                "transition": next_node_name
            }
            transitions.append(curr_transition)

            state = {
                "type": "Simple",
                "distributed_transition": [
                    {
                        "transition": next_state,
                        "distribution": prob
                    },
                    {
                        "transition": default_state,
                        "distribution": 1 - prob
                    }
                ],
                "remarks": [
                    "{} have an approx lifetime risk of {} of {}%.".format(
                        race_distribution.get(key).get("name") + " people",
                        condition,
                        prob * 100
                    )
                ]
            }
            adjacent_states[next_node_name] = state

    return transitions, adjacent_states


def generate_synthea_module(symptom_dict, test_condition):
    """Function for generating the PGM module for a given condition.

    Parameters
    ----------
    symptom_dict : dict
        Dictionnary containing all the symptoms of the database
        with their related characteristics.
    test_condition : dict
        Dictionnary containing information related to the condition
        for which the PGM is being generated.

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
    incidence_limit = 3
    node_infection_name = condition_name.replace(" ", "_") + "_Infection"

    states = OrderedDict()

    # add the initial onset
    states["Initial"] = {
        "type": "Initial"
    }

    # sex states
    sex_conditional_transition, sex_states = generate_transition_for_sex(
        condition_name, test_condition.get(
            "sex"), "Check_Race", "TerminalState"
    )
    states["Initial"]["conditional_transition"] = sex_conditional_transition
    states.update(sex_states)

    # add Check_Race node
    states["Check_Race"] = {
        "type": "Simple"
    }

    # race states
    race_conditional_transition, race_states = generate_transition_for_race(
        condition_name,
        test_condition.get("race"), "Init_Counter", "No_Infection"
    )
    states["Check_Race"]["conditional_transition"] = race_conditional_transition
    states.update(race_states)

    # add No_Infection node
    states["No_Infection"] = {
        "type": "Simple",
        "direct_transition": "TerminalState"
    }

    # add Init_Counter node
    states["Init_Counter"] = {
        "type": "SetAttribute",
        "attribute": incidence_attribute,
        "value": 0,
        "direct_transition": potential_infection_transition
    }

    # add Potential_Infection node
    states[potential_infection_transition] = {
        "type": "Delay",
        "range": {
            "low": 1,
            "high": 3,
            "unit": "months"
        }
    }

    # age state
    age_conditional_transition, age_states = generate_transition_for_age(
        condition_name,
        test_condition.get(
            "age"), node_infection_name, potential_infection_transition
    )
    states[potential_infection_transition][
        "conditional_transition"] = age_conditional_transition
    states.update(age_states)

    initial_transition = potential_infection_transition

    # add the Condition state (a ConditionOnset) stage
    condition_hash = hashlib.sha224(test_condition.get(
        "condition_slug").encode("utf-8")).hexdigest()
    condition_code = {
        "system": "sha224",
        "code": condition_hash,
        "display": condition_name
    }
    states[node_infection_name] = {
        "type": "ConditionOnset",
        "codes": [condition_code],
        "target_encounter": "Doctor_Visit",
        "remarks": [
            test_condition.get("condition_description"),
            test_condition.get("condition_remarks")
        ],
        "direct_transition": "Simple_Transition_1"
    }

    # now we start to model the symptoms, we use
    condition_symptoms = test_condition.get("symptoms")
    keys = list(condition_symptoms.keys())
    for idx in range(len(keys)):
        curr_symptom = condition_symptoms.get(keys[idx])
        probability = float(curr_symptom.get("probability")) * 1.0 / 100
        slug = curr_symptom.get("slug")

        symptom_definition = symptom_dict.get(slug, None)
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
                "remarks": []
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
                ]
            }

        simple_transition_name = "Simple_Transition_%d" % (idx + 1)
        symptom_transition_name = "Symptom_%d" % (idx + 1)

        if idx == len(keys) - 1:
            next_target = "Doctor_Visit"
        else:
            next_target = "Simple_Transition_%d" % (idx + 2)

        simple_transition = {
            "type": "Simple",
            "distributed_transition": [
                {
                    "distribution": probability,
                    "transition": symptom_transition_name
                },
                {
                    "distribution": 1 - probability,
                    "transition": next_target
                }
            ]
        }

        symptom_transition.update({
            "direct_transition": next_target
        })

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
        "direct_transition": "TreatmentComplete",
        "condition_onset": node_infection_name
    }

    # let's wait for a year and redo the whole thing!
    states["TreatmentComplete"] = {
        "type": "Delay",
        "exact": {
            "quantity": 1,
            "unit": "years"
        },
        "direct_transition": incidence_counter_transition
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
                    "operator": ">",
                    "value": incidence_limit
                }
            },
            {
                "transition": initial_transition
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


def generate_synthea_modules(symptom_file, conditions_file, output_dir):
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

    for key, value in conditions_data.items():
        module = generate_synthea_module(symptoms_data, value)
        if module is None:
            continue
        filename = os.path.join(output_dir, "%s.json" % key)

        with open(filename, "w") as fp:
            json.dump(module, fp, indent=4)
    return True
