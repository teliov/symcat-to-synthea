from collections import OrderedDict
import hashlib
import json
import os


def generate_transition_for_age(age_distribution, prev_state, next_state):
    age_keys = [
        "age-1-years", "age-1-4-years", "age-5-14-years", "age-15-29-years",
        "age-30-44-years", "age-45-59-years", "age-60-74-years", "age-75-years"
    ]

    likelihood_sum = 0
    for key in age_keys:
        likelihood_sum += float(age_distribution.get(key).get("likelihood"))
    likelihood_sum *= 10.0

    transitions = []
    for key in age_keys:
        prob = float(age_distribution.get(key).get("likelihood")) / likelihood_sum
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
    male_likelihood = float(sex_distribution.get("sex-male").get("likelihood"))
    female_likelihood = float(sex_distribution.get("sex-female").get("likelihood"))
    likelihood_sum = 10.0 * (male_likelihood + female_likelihood)

    male_prob = male_likelihood * 1.0 / likelihood_sum
    female_prob = female_likelihood * 1.0 / likelihood_sum

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

    likelihood_sum = 0
    for key in race_keys:
        likelihood_sum += float(race_distribution.get(key).get("likelihood"))
    likelihood_sum *= 10.0

    transitions = []

    for key in race_keys:
        prob = float(race_distribution.get(key).get("likelihood")) / likelihood_sum
        if key == "race-ethnicity-other":
            # split this into three for : NATIVE, "ASIAN" and "OTHER" according to synthea
            for idx, item in enumerate(["Native", "Asian", "Other"]):
                if idx < 2:
                    curr_prob = prob / 2
                else:
                    curr_prob = 1 - prob * 2 / 3

                curr_transition = {
                    "condition": {
                        "condition_type": "Race",
                        "race": item
                    },
                    "distributions": [
                        {
                            "transition": next_state,
                            "distribution": curr_prob
                        },
                        {
                            "transition": prev_state,
                            "distribution": 1 - curr_prob
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
    condition_name = test_condition.get("condition_name")

    states = OrderedDict()

    # add the initial onset
    states["Initial"] = {
        "type": "Initial",
        "direct_transition": "Age_Transition"  # always transition to a potential onset (delay state)
    }

    # add the potential onset state
    states["Age_Transition"] = {
        "type": "delay",
        "exact": {
            "quantity": 1,
            "unit": "months"
        },
        "complex_transition": generate_transition_for_age(test_condition.get("age"), "Age_Transition", "Sex_Transition")
    }

    # add the sex transition state
    states["Sex_Transition"] = {
        "type": "Simple",
        "complex_transition": generate_transition_for_sex(test_condition.get("sex"), "Age_Transition",
                                                          "Race_Transition")
    }

    # add the race transition state
    states["Race_Transition"] = {
        "type": "Simple",
        "complex_transition": generate_transition_for_race(test_condition.get("race"), "Age_Transition",
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
        "direct_transition": "Simple_Symptom_1"
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
            print("No Definition: %s" % slug)
            slug_hash = hashlib.sha224(slug.encode("utf-8")).hexdigest()
            symptom_transition = {
                "type": "Symptom",
                "symptom": slug,
                "range": {
                    "low": 25,
                    "high": 50
                },
                "condition_code": condition_code,
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
                "condition_code": condition_code,
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

    # add the encounter state and the delay state
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
        "direct_transition": "TreatmentComplete"
    }

    states["Treatment"] = {
        "type": "Delay",
        "exact": {
            "quantity": 6,
            "unit": "months"
        },
        "direct_transition": "Terminal"
    }

    states["Terminal"] = {
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
        filename = os.path.join(output_dir, "%s.json" % key)

        with open(filename, "w") as fp:
            json.dump(module, fp, indent=4)
    return True
