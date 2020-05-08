from collections import OrderedDict
import hashlib
from functools import reduce
import itertools

from .basic_module_generator import ModuleGenerator
from .helpers import load_config, TransitionStates, prob_val, round_val, AttrKeys


class AdvancedModuleGenerator(ModuleGenerator):
    def __init__(self, conditions, symptoms, config):
        super().__init__(conditions, symptoms, config)

        self.priors = load_config(self.config.config_file)
        self.sep_key = '|'

    def generate_module(self, key):
        condition = self.conditions.get(key)

        if not condition.get("symptoms", None):
            return None

        min_symptoms = self.config.min_symptoms

        condition_name = condition.get("condition_name")
        condition_slug = condition.get("condition_slug")

        num_symptom_attribute = "count_symptom_%s" % condition_slug
        history_age_attribute = "age_time_to_the_end"
        node_infection_name = condition_name.replace(" ", "_") + "_Infection"

        states = OrderedDict()

        # add the initial onset
        states["Initial"] = {
            "type": "Initial",
            "direct_transition": "Check_History_Age_Attribute"
        }

        states["Check_History_Age_Attribute"] = {
            "type": "Guard",
            "allow": {
                "condition_type": "Attribute",
                "attribute": history_age_attribute,
                "operator": "<=",
                "value": 0
            },
            "direct_transition": TransitionStates.POTENTIAL_INFECTION
        }

        transitions, condition_dict_prob = self.generate_transition_for_sex_race_age(
            condition_name,
            condition,
            TransitionStates.TARGET_ENCOUNTER_START,
            TransitionStates.NO_INFECTION
        )

        states[TransitionStates.POTENTIAL_INFECTION] = {
            "type": "Simple",
            "complex_transition": transitions
        }

        # add No_Infection node
        # we will end this module if a patient does not catch the condition n
        # consecutive times.
        states[TransitionStates.NO_INFECTION] = {
            "type": "Simple",
            "direct_transition": "TerminalState"
        }

        # add the Condition state (a ConditionOnset) stage
        condition_hash = hashlib.sha224(condition.get(
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

        states[TransitionStates.TARGET_ENCOUNTER_START] = {
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
            "direct_transition": node_infection_name
        }

        states[node_infection_name] = {
            "type": "ConditionOnset",
            "codes": [condition_code],
            "target_encounter": "Doctor_Visit",
            "remarks": [
                condition.get("condition_description"),
                condition.get("condition_remarks")
            ],
            "direct_transition": next_stage
        }

        # now we start to model the symptoms, we use
        condition_symptoms = condition.get("symptoms")
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

            symptom_definition = self.symptoms.get(slug, None)

            if idx == len(keys) - 1:
                next_target = TransitionStates.TARGET_ENCOUNTER_END
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
                            "distribution": round_val(probability),
                            "transition": symptom_transition_name
                        },
                        {
                            "distribution": round_val(1 - probability),
                            "transition": next_point
                        }
                    ]
                }
                sym_transitions_dict = {'|'.join(['None'] * 3): probability}
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

                sym_transitions, sym_transitions_dict = self.generate_symptoms_for_sex_race_age(
                    probability,
                    symptom_definition,
                    condition,
                    condition_dict_prob,
                    symptom_transition_name,
                    next_point
                )

                simple_transition = {
                    "type": "Simple",
                    "complex_transition": sym_transitions
                }

            states[simple_transition_name] = simple_transition
            states[symptom_transition_name] = symptom_transition

        states[TransitionStates.TARGET_ENCOUNTER_END] = {
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

    def generate_transition_for_sex_race_age(self, condition, distribution, next_state, default_state=TransitionStates):
        transitions = []
        transitions_dict = {}
        sex_denom = sum([
            prob_val(
                distribution.get("sex").get(sex_key).get("odds")
            ) * self.priors["Gender"][sex_key]
            for sex_key in AttrKeys.SEX_KEYS
        ])
        age_denom = sum([
            prob_val(
                distribution.get("age").get(age_key).get("odds")
            ) * self.priors["Age"][age_key]
            for age_key in AttrKeys.AGE_KEYS
        ])
        race_denom = sum([
            prob_val(
                distribution.get("race").get(
                    "race-ethnicity-other" if race_key in [
                        "race-ethnicity-asian", "race-ethnicity-native"] else race_key
                ).get("odds")
            ) * self.priors["Race"][race_key]
            for race_key in AttrKeys.RACE_PRIOR_KEYS
        ])

        assert sex_denom >= 0, "the sex denom probability must be greater or equal to 0"
        assert age_denom >= 0, "the age denom probability must be greater or equal to 0"
        assert race_denom >= 0, "the race denom probability must be greater or equal to 0"

        max_valid_prior = 1.0
        default_prior_condition = 0.5
        prior_condition = self.priors["Conditions"].get(
            condition.lower(), default_prior_condition)
        prior_condition = min([max_valid_prior, prior_condition])

        transitions_dict['prior_condition'] = prior_condition

        # global key separator
        sep_key = self.sep_key

        # should I include default transition?
        default_flag = False

        for sex_key in AttrKeys.SEX_KEYS:
            sex_odds = distribution.get("sex").get(sex_key).get("odds")
            sex_prob = prob_val(sex_odds)
            if sex_prob <= 0:
                default_flag = True
                for age_key in AttrKeys.AGE_KEYS:
                    for race_key in AttrKeys.RACE_PRIOR_KEYS:
                        global_key = sep_key.join([sex_key, age_key, race_key])
                        transitions_dict[global_key] = 0.0
                continue

            condition_sex = {
                "condition_type": "Gender",
                "gender": "M" if sex_key == "sex-male" else "F"
            }

            for age_key in AttrKeys.AGE_KEYS:
                age_odds = distribution.get("age").get(age_key).get("odds")
                age_prob = prob_val(age_odds)
                if age_prob <= 0:
                    default_flag = True
                    for race_key in AttrKeys.RACE_PRIOR_KEYS:
                        global_key = sep_key.join([sex_key, age_key, race_key])
                        transitions_dict[global_key] = 0.0
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

                for race_key in AttrKeys.RACE_KEYS:
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
                            p_cond_g_sex_race_age = min(1.0, p_cond_g_sex_race_age)

                            assert p_cond_g_sex_race_age <= 1
                            global_key = sep_key.join(
                                [sex_key, age_key, race_val])
                            transitions_dict[global_key] = p_cond_g_sex_race_age

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
                                        "distribution": round_val(1 - p_cond_g_sex_race_age)
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
                        p_cond_g_sex_race_age = min(1.0, p_cond_g_sex_race_age)

                        assert p_cond_g_sex_race_age <= 1
                        global_key = sep_key.join([sex_key, age_key, race_key])
                        transitions_dict[global_key] = p_cond_g_sex_race_age

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
                                    "distribution": round_val(1 - p_cond_g_sex_race_age)
                                }
                            ]
                        })

        if default_flag:
            transitions.append({
                "transition": default_state
            })

        return transitions, transitions_dict

    @staticmethod
    def get_ind_prob_symptom_cond_given_sex(sex_dict, sex_cond_dict, sex_key):
        """compute P(symptom, condition | sex) for a given sex category
        """
        return prob_val(
            sex_dict.get(sex_key).get("odds")
        ) * prob_val(
            sex_cond_dict.get(sex_key).get("odds")
        )

    def get_prob_symptom_cond_given_sex(self, sex_dict, sex_cond_dict):
        """compute P(symptom, condition | sex) for all sex categories
        """
        return [
            self.get_ind_prob_symptom_cond_given_sex(
                sex_dict, sex_cond_dict, sex_key
            ) * self.priors["Gender"][sex_key]
            for sex_key in AttrKeys.SEX_KEYS
        ]

    @staticmethod
    def get_ind_prob_symptom_cond_given_age(age_dict, age_cond_dict, age_key):
        """compute P(symptom, condition | age) for a given age category
        """
        return prob_val(
            age_dict.get(age_key).get("odds")
        ) * prob_val(
            age_cond_dict.get(age_key).get("odds")
        )

    def get_prob_symptom_cond_given_age(self, age_dict, age_cond_dict):
        """compute P(symptom, condition | age) for all age categories
        """
        return [
            self.get_ind_prob_symptom_cond_given_age(
                age_dict, age_cond_dict, age_key
            ) * self.priors["Age"][age_key]
            for age_key in AttrKeys.AGE_KEYS
        ]

    @staticmethod
    def get_ind_prob_symptom_cond_given_race(race_dict, race_cond_dict, race_key):
        """compute P(symptom, condition | race) for a given race category
        """
        return prob_val(
            race_dict.get(
                "race-ethnicity-other" if race_key in [
                    "race-ethnicity-asian", "race-ethnicity-native"] else race_key
            ).get("odds")
        ) * prob_val(
            race_cond_dict.get(
                "race-ethnicity-other" if race_key in [
                    "race-ethnicity-asian", "race-ethnicity-native"] else race_key
            ).get("odds")
        )

    def get_prob_symptom_cond_given_race(self, race_dict, race_cond_dict):
        """compute P(symptom, condition | race) for all race categories
        """
        return [
            self.get_ind_prob_symptom_cond_given_race(
                race_dict, race_cond_dict, race_key
            ) * self.priors["Race"][race_key]
            for race_key in AttrKeys.RACE_KEYS
        ]

    def get_symptom_stats_infos(self, condition_definition, symptom_definition, probability, condition_proba):
        """Function for getting stats info from a symptom given a condition and priors on risks factors

        Parameters
        ----------
        condition_definition : dict
            Dictionnary containing the odd values associated to each age category,
            race category, and sex category
        symptom_definition : dict
            Dictionary containing all the symptoms of the database
            with their related characteristics.
        probability: float
            The absolute probablity value of the symtom given the cuurent condition.
        condition_proba : dict
            the probability of the condition for each coombination of risk factors (sex, age, race)
            without the effect of the condition priors. P(ARG|C)/P(ARG). Note that the true condition
            probability would be obtained by P(C|ARG) = P(ARG|C) * P(C)/ P(ARG).
        priors : dict
            The priors associated to age, race, sex categories as well as conditions and symptoms
        sex_keys : list
            keys for referencing sex related risk factor categories
        age_keys : list
            keys for referencing age related risk factor categories
        race_keys : list
            keys for referencing race related risk factor categories

        Returns
        -------
        cond_prior: float
            the condition prior value that gurantee non negative symptom probability values
        """

        sex_cond_dict = condition_definition.get("sex", {})
        race_cond_dict = condition_definition.get("race", {})
        age_cond_dict = condition_definition.get("age", {})

        sex_dict = symptom_definition.get("sex", {})
        race_dict = symptom_definition.get("race", {})
        age_dict = symptom_definition.get("age", {})

        sex_prob_values = self.get_prob_symptom_cond_given_sex(
            sex_dict, sex_cond_dict
        )
        age_prob_values = self.get_prob_symptom_cond_given_age(
            age_dict, age_cond_dict
        )
        race_prob_values = self.get_prob_symptom_cond_given_race(
            race_dict, race_cond_dict
        )
        sex_denom = sum(
            sex_prob_values
        ) if (len(sex_dict) > 0 and len(sex_cond_dict) > 0) else 1
        age_denom = sum(
            age_prob_values
        ) if (len(age_dict) > 0 and len(age_cond_dict) > 0) else 1
        race_denom = sum(
            race_prob_values
        ) if (len(race_dict) > 0 and len(race_cond_dict) > 0) else 1

        assert sex_denom >= 0, "the sex denom probability must be greater or equal to 0"
        assert age_denom >= 0, "the age denom probability must be greater or equal to 0"
        assert race_denom >= 0, "the race denom probability must be greater or equal to 0"

        # compute P(symptom, condition | risk_factor) / risk_factor_demom
        sex_numerator = [
            self.get_ind_prob_symptom_cond_given_sex(
                sex_dict, sex_cond_dict, sex_key
            )
            for sex_key in AttrKeys.SEX_KEYS
        ]
        age_numerator = [
            self.get_ind_prob_symptom_cond_given_age(
                age_dict, age_cond_dict, age_key
            )  # / age_denom if age_denom > 0 else 0.0
            for age_key in AttrKeys.AGE_KEYS
        ]
        race_numerator = [
            self.get_ind_prob_symptom_cond_given_race(
                race_dict, race_cond_dict, race_key
            )  # / race_denom if race_denom > 0 else 0.0
            for race_key in AttrKeys.RACE_KEYS
        ]

        # compute cross product of risk_factor numerators
        cross_product = [
            reduce((lambda x, y: x * y), element)
            for element in itertools.product(sex_numerator, age_numerator, race_numerator)
        ]

        # global key separator
        sep_key = self.sep_key

        # get p(condition | risk factors)
        prob_condition = [
            condition_proba.get(sep_key.join(element), 0.0)
            for element in itertools.product(AttrKeys.SEX_KEYS, AttrKeys.AGE_KEYS, AttrKeys.RACE_KEYS)
        ]

        denom = sex_denom * age_denom * race_denom
        local_cross_product = []
        for a, b in zip(cross_product, prob_condition):
            if a > 0:
                local_cross_product.append(b * denom / a)

        local_min_cross_product = min(local_cross_product) if len(
            local_cross_product) > 0 else 1.0

        prior_symptom_condition = min([1.0, local_min_cross_product])

        prior_condition = min(prior_symptom_condition / probability, 1.0)

        return sex_denom, age_denom, race_denom, prior_condition

    def generate_symptoms_for_sex_race_age(self, probability, distribution, condition_distribution, condition_proba,
                                           next_state, default_state=TransitionStates.TERMINAL_STATE):
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
            condition : str
                The name of the condition for which the PGM is being generated.
            condition_distribution : dict
                Dictionnary containing the odd values associated to each age category,
                race category, and sex category for the condition related to the symptom
                being generated
            condition_proba: dict
                Dictionnary containing the probabilities of the condition related to the symptom
                being generated given each risk factor combination (sex, age, race).
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
            transitions_dict: dict
                the dict containing the prob values for each risk factor combination (sex,age,race)
            """

        transitions = []
        transitions_dict = {}

        # global key separator
        sep_key = self.sep_key

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
            transitions_dict[sep_key.join(['None', 'None', 'None'])] = probability

            return transitions, transitions_dict

        # Prob (condition | risk factors)
        sex_cond_denom = sum([
            prob_val(
                condition_distribution.get("sex").get(sex_key).get("odds")
            ) * self.priors["Gender"][sex_key]
            for sex_key in AttrKeys.SEX_KEYS
        ])
        age_cond_denom = sum([
            prob_val(
                condition_distribution.get("age").get(age_key).get("odds")
            ) * self.priors["Age"][age_key]
            for age_key in AttrKeys.AGE_KEYS
        ])
        race_cond_denom = sum([
            prob_val(
                condition_distribution.get("race").get(
                    "race-ethnicity-other" if race_key in [
                        "race-ethnicity-asian", "race-ethnicity-native"] else race_key
                ).get("odds")
            ) * self.priors["Race"][race_key]
            for race_key in AttrKeys.RACE_PRIOR_KEYS
        ])

        # should I include default transition?
        default_flag = False

        sex_dict = distribution.get("sex", {})
        race_dict = distribution.get("race", {})
        age_dict = distribution.get("age", {})

        sex_cond_dict = condition_distribution.get("sex", {})
        race_cond_dict = condition_distribution.get("race", {})
        age_cond_dict = condition_distribution.get("age", {})

        sex_denom, age_denom, race_denom, symp_prior_condition = self.get_symptom_stats_infos(
            condition_distribution, distribution,
            probability, condition_proba
        )

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

            if sex_key == fake_sex_key: # fake_dict
                sex_prob = 1
                sex_cond_prob = 1
                condition_sex = None
                sex_key = "None"
            else:
                sex_prob = self.get_ind_prob_symptom_cond_given_sex(
                    sex_dict, sex_cond_dict, sex_key
                )
                sex_cond_prob = prob_val(
                    condition_distribution.get("sex").get(sex_key).get("odds")
                )
                if sex_prob <= 0:
                    default_flag = True
                    for age_key in AttrKeys.AGE_KEYS:
                        for race_key in AttrKeys.RACE_PRIOR_KEYS:
                            global_key = sep_key.join([sex_key, age_key, race_key])
                            transitions_dict[global_key] = 0.0
                    continue

                condition_sex = {
                    "condition_type": "Gender",
                    "gender": "M" if sex_key == "sex-male" else "F"
                }

            for age_key in age_dict.keys():
                if age_key == fake_age_key:  # fake_dict
                    age_prob = 1
                    age_cond_prob = 1
                    condition_age = None
                    age_key = "None"
                else:
                    age_prob = self.get_ind_prob_symptom_cond_given_age(
                        age_dict, age_cond_dict, age_key
                    )
                    age_cond_prob = prob_val(
                        condition_distribution.get("age").get(age_key).get("odds")
                    )
                    if age_prob <= 0:
                        default_flag = True
                        for race_key in AttrKeys.RACE_PRIOR_KEYS:
                            global_key = sep_key.join([sex_key, age_key, race_key])
                            transitions_dict[global_key] = 0.0
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
                        race_cond_prob = 1
                        condition_race = [None]
                        race_key = "None"
                        race_vals = [race_key]
                    else:
                        race_prob = self.get_ind_prob_symptom_cond_given_race(
                            race_dict, race_cond_dict, race_key
                        )
                        race_cond_prob = prob_val(
                            condition_distribution.get(
                                "race").get(race_key).get("odds")
                        )
                        if race_key == "race-ethnicity-other":
                            # split this into three for : NATIVE, "ASIAN" and "OTHER"
                            # according to synthea
                            othersVal = [
                                ("race-ethnicity-native", "Native"),
                                ("race-ethnicity-asian", "Asian"),
                                ("race-ethnicity-other", "Other"),
                            ]
                            condition_race = []
                            race_vals = []
                            for race_val, item in othersVal:
                                condition_race.append({
                                    "condition_type": "Race",
                                    "race": item
                                })
                                race_vals.append(race_val)
                        else:
                            condition_race = [{
                                "condition_type": "Race",
                                "race": distribution.get("race").get(race_key).get("name")
                            }]
                            race_vals = [race_key]

                    for idx, race_val in enumerate(race_vals):

                        global_key = sep_key.join([sex_key, age_key, race_val])

                        p_numerator = probability * sex_prob * age_prob * \
                                        race_prob * sex_cond_denom * age_cond_denom * race_cond_denom
                        p_denominator = age_denom * sex_denom * race_denom * \
                                          sex_cond_prob * age_cond_prob * race_cond_prob
                        p_symp_g_cond_sex_race_age = round_val(
                            p_numerator / p_denominator) if p_denominator > 0 else 0.0
                        p_symp_g_cond_sex_race_age = min(
                            p_symp_g_cond_sex_race_age,
                            1.0
                        )

                        assert p_symp_g_cond_sex_race_age <= 1
                        transitions_dict[global_key] = p_symp_g_cond_sex_race_age

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
                                    "distribution": round_val(p_symp_g_cond_sex_race_age)
                                },
                                {
                                    "transition": default_state,
                                    "distribution": round_val(1 - p_symp_g_cond_sex_race_age)
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

        return transitions, transitions_dict
