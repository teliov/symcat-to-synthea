from collections import OrderedDict
import hashlib
import json
import os


def generate_transition_for_age(age_distribution, prev_state, next_state):
    age_keys = [
        "age-1-years", "age-1-4-years", "age-5-14-years", "age-15-29-years",
        "age-30-44-years", "age-45-59-years", "age-60-74-years", "age-75-years"
    ]

    transitions = []
    for key in age_keys:
        odds = age_distribution.get(key).get("odds")
        prob = odds / (1.0 + odds)
        if key == "age-1-years":
            curr_transition = {
                "condition": {
                    "condition_type": "Age",
                    "operator": "<",
                    "unit": "years",
                    "quantity": 1
                },
                "distributions": [
                    {
                        "transition": next_state,
                        "distribution": prob
                    },
                    {
                        "transition": prev_state,
                        "distribution": 1 - prob
                    }
                ]
            }
        elif key == "age-75-years":
            curr_transition = {
                "condition": {
                    "condition_type": "Age",
                    "operator": ">",
                    "unit": "years",
                    "quantity": 75
                },
                "distributions": [
                    {
                        "transition": next_state,
                        "distribution": prob
                    },
                    {
                        "transition": prev_state,
                        "distribution": 1 - prob
                    }
                ]
            }
        else:
            parts = key.split("-")
            age_lower = parts[1]
            age_upper = parts[2]
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
                "distributions": [
                    {
                        "transition": next_state,
                        "distribution": prob
                    },
                    {
                        "transition": prev_state,
                        "distribution": 1 - prob
                    }
                ]
            }
        transitions.append(curr_transition)

    return transitions


def generate_transition_for_sex(sex_distribution, prev_state, next_state):
    male_odds = float(sex_distribution.get("sex-male").get("odds"))
    female_odds = float(sex_distribution.get("sex-female").get("odds"))

    male_prob = male_odds / (1.0 + male_odds)
    female_prob = female_odds / (1.0 + female_odds)

    probabilities = [male_prob, female_prob]

    transition = []
    for idx in range(2):
        transition.append({
            "condition": {
                "condition_type": "Gender",
                "gender": "M" if idx == 0 else "F"
            },
            "distributions": [
                {
                    "transition": next_state,
                    "distribution": probabilities[idx]
                },
                {
                    "transition": prev_state,
                    "distribution": 1 - probabilities[idx]
                }
            ]
        })

    return transition


def generate_transition_for_race(race_distribution, prev_state, next_state):
    race_keys = ["race-ethnicity-black", "race-ethnicity-hispanic", "race-ethnicity-white", "race-ethnicity-other"]

    transitions = []

    for key in race_keys:
        odds = float(race_distribution.get(key).get("odds"))
        prob = odds / (1.0 + odds)
        if key == "race-ethnicity-other":
            # split this into three for : NATIVE, "ASIAN" and "OTHER" according to synthea
            for idx, item in enumerate(["Native", "Asian", "Other"]):
                curr_transition = {
                    "condition": {
                        "condition_type": "Race",
                        "race": item
                    },
                    "distributions": [
                        {
                            "transition": next_state,
                            "distribution": prob
                        },
                        {
                            "transition": prev_state,
                            "distribution": 1 - prob
                        }
                    ]
                }
                transitions.append(curr_transition)
        else:
            curr_transition = {
                "condition": {
                    "condition_type": "Race",
                    "race": race_distribution.get(key).get("name")
                },
                "distributions": [
                    {
                        "transition": next_state,
                        "distribution": prob
                    },
                    {
                        "transition": prev_state,
                        "distribution": 1 - prob
                    }
                ]
            }
            transitions.append(curr_transition)

    return transitions


def generate_synthea_module(symptom_dict, test_condition):

    # check that symptoms do exist for this module!?
    if not test_condition.get("symptoms"):
        return None

    condition_name = test_condition.get("condition_name")
    condition_slug = test_condition.get("condition_slug")

    initial_transition = "Age_Transition"
    incidence_counter_transition = "IncidenceCounter"
    incidence_limit = 3

    states = OrderedDict()

    # add the initial onset
    states["Initial"] = {
        "type": "Initial",
        "direct_transition": initial_transition  # always transition to a potential onset (Delay state)
    }

    # add the potential onset state
    states["Age_Transition"] = {
        "type": "Delay",
        "exact": {
            "quantity": 1,
            "unit": "months"
        },
        "complex_transition": generate_transition_for_age(test_condition.get("age"), initial_transition, "Sex_Transition")
    }

    # add the sex transition state
    states["Sex_Transition"] = {
        "type": "Simple",
        "complex_transition": generate_transition_for_sex(test_condition.get("sex"), initial_transition,
                                                          "Race_Transition")
    }

    # add the race transition state
    states["Race_Transition"] = {
        "type": "Simple",
        "complex_transition": generate_transition_for_race(test_condition.get("race"), initial_transition,
                                                           "ConditionOnset")
    }

    # add the Condition state (a ConditionOnset) stage
    condition_hash = hashlib.sha224(test_condition.get("condition_slug").encode("utf-8")).hexdigest()
    condition_code = {
        "system": "sha224",
        "code": condition_hash,
        "display": condition_name
    }
    states["ConditionOnset"] = {
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
        "condition_onset": "ConditionOnset"
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
    incidence_attribute = "count_%s" % condition_slug
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
                    "value" : incidence_limit
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
