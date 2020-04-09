import os
import itertools

from parse import parse_symcat_conditions, parse_symcat_symptoms, slugify_condition
from generate import generate_synthea_module, prob_val, round_val
from configFileParser import load_config


class TestGenerator(object):

    def test_prob_value(self):
        assert prob_val(0.4) == round(0.4 / 1.4, 4)
        assert prob_val(0.3, 7) == round(0.3 / 1.3, 7)
        assert prob_val(0.3, 2) != 0.5

    def get_symptom_proba(self, symptom_name, age_key, race_key, gender_key, priors, provided_condition_probs, marginale_condition, expected_probability):

        p_gender = provided_condition_probs["Gender"][gender_key]
        gender_prior = priors["Gender"][gender_key]

        p_race = provided_condition_probs["Race"][race_key]
        race_prior = priors["Race"][race_key]

        p_age = provided_condition_probs["Age"][age_key]
        age_prior = priors["Age"][age_key]

        age_race_gender_prior = age_prior * race_prior * gender_prior

        sym_prior_gender = marginale_condition["Gender"]
        sym_prior_age = marginale_condition["Age"]
        sym_prior_race = marginale_condition["Race"]

        computed_proba = (expected_probability *
                          p_gender * p_race * p_age)
        computed_proba /= (sym_prior_gender *
                           sym_prior_age * sym_prior_race)

        computed_proba = round_val(computed_proba)

        return computed_proba, age_race_gender_prior

    def get_condition_proba(self, condition_name, age_key, race_key, gender_key, priors, provided_condition_probs, marginale_condition):

        p_gender = provided_condition_probs["Gender"][gender_key]
        gender_prior = priors["Gender"][gender_key]

        p_race = provided_condition_probs["Race"][race_key]
        race_prior = priors["Race"][race_key]

        p_age = provided_condition_probs["Age"][age_key]
        age_prior = priors["Age"][age_key]

        age_race_gender_prior = age_prior * race_prior * gender_prior

        default_condition_prior = 0.5

        condition_prior_gender = priors["Conditions"].get(
            condition_name, default_condition_prior
        )

        marginal_prior_gender = marginale_condition["Gender"]
        marginal_prior_age = marginale_condition["Age"]
        marginal_prior_race = marginale_condition["Race"]

        computed_proba = (
            condition_prior_gender * p_gender * p_race * p_age
        )
        computed_proba /= (
            marginal_prior_gender * marginal_prior_age * marginal_prior_race)

        computed_proba = round_val(computed_proba)

        return computed_proba, age_race_gender_prior

    def get_exception_keys_and_num_condition(self, provided_condition_probs):
        keys_to_avoids = {
            "Age": [
                k for k in provided_condition_probs["Age"]
                if provided_condition_probs["Age"][k] == 0
            ],
            "Gender": [
                k for k in provided_condition_probs["Gender"]
                if provided_condition_probs["Gender"][k] == 0
            ],
        }
        expected_num_conditions = len(provided_condition_probs["Race"])
        expected_num_conditions *= (
            len(provided_condition_probs["Gender"]
                ) - len(keys_to_avoids["Gender"])
        )
        expected_num_conditions *= (
            len(provided_condition_probs["Age"]) - len(keys_to_avoids["Age"])
        )
        return keys_to_avoids, expected_num_conditions

    def process_complex_transition(self, condition_stmts, keys_to_avoids):
        age_min = 0
        age_max = 140
        gender = None
        race = None

        for acase in condition_stmts:
            if acase["condition_type"] == "Gender":
                gender = acase["gender"]
            elif acase["condition_type"] == "Race":
                race = acase["race"]
            elif acase["condition_type"] == "Age":
                if acase["operator"] in [">", ">="]:
                    age_min = acase["quantity"]
                elif acase["operator"] in ["<", "<="]:
                    age_max = acase["quantity"]
                else:
                    assert False
            elif acase["condition_type"] == "And":
                assert len(acase["conditions"]) == 2
                for subcase in acase["conditions"]:
                    if subcase["condition_type"] == "Age":
                        if subcase["operator"] in [">", ">="]:
                            age_min = subcase["quantity"]
                        elif subcase["operator"] in ["<", "<="]:
                            age_max = subcase["quantity"]
                        else:
                            assert False
                    else:
                        assert False
            else:
                assert False

        age_min = int(age_min)
        age_max = int(age_max)

        assert gender is not None
        assert race is not None
        assert age_min <= age_max

        if gender == "M":
            gender_key = "sex-male"
        elif gender == "F":
            gender_key = "sex-female"
        else:
            assert False

        if race == "Black":
            race_key = "race-ethnicity-black"
        elif race == "Hispanic":
            race_key = "race-ethnicity-hispanic"
        elif race == "White":
            race_key = "race-ethnicity-white"
        elif race == "Asian":
            race_key = "race-ethnicity-asian"
        elif race == "Native":
            race_key = "race-ethnicity-native"
        elif race == "Other":
            race_key = "race-ethnicity-other"
        else:
            assert False

        if (age_min == 0 and age_max == 1):
            age_key = "age-1-years"
        elif (age_min == 1 and age_max == 4):
            age_key = "age-1-4-years"
        elif (age_min == 5 and age_max == 14):
            age_key = "age-5-14-years"
        elif (age_min == 15 and age_max == 29):
            age_key = "age-15-29-years"
        elif (age_min == 30 and age_max == 44):
            age_key = "age-30-44-years"
        elif (age_min == 45 and age_max == 59):
            age_key = "age-45-59-years"
        elif (age_min == 60 and age_max == 74):
            age_key = "age-60-74-years"
        elif (age_min == 75):
            age_key = "age-75-years"
        else:
            assert False

        if keys_to_avoids is not None:
            if "Age" in keys_to_avoids:
                for k in keys_to_avoids["Age"]:
                    assert not (age_key == k)
            if "Gender" in keys_to_avoids:
                for k in keys_to_avoids["Gender"]:
                    assert not (gender_key == k)

        return age_key, race_key, gender_key

    def check_condition_proba(self, condition_name, module_proba, priors, provided_condition_probs):

        keys_to_avoids, expected_num_conditions = self.get_exception_keys_and_num_condition(
            provided_condition_probs
        )

        marginale_condition = {
            k: sum([priors[k][d] * provided_condition_probs[k][d] for d in priors[k].keys()])
            for k in provided_condition_probs.keys()
        }
        marginale_not_condition = {
            k: sum([priors[k][d] * (1 - provided_condition_probs[k][d]) for d in priors[k].keys()])
            for k in provided_condition_probs.keys()
        }

        all_possibilities = module_proba['complex_transition']
        num_distributed_condtions = 0
        for possibility in all_possibilities:
            if "condition" in possibility and "distributions" in possibility:
                num_distributed_condtions += 1

                condition_stmts = possibility["condition"]
                distribution_stmts = possibility["distributions"]

                if condition_stmts["condition_type"] == "And":
                    condition_stmts = condition_stmts["conditions"]
                else:
                    condition_stmts = [condition_stmts]

                age_key, race_key, gender_key = self.process_complex_transition(
                    condition_stmts, keys_to_avoids
                )

                probability = distribution_stmts[0]["distribution"]

                computed_proba, age_race_gender_prior = self.get_condition_proba(
                    condition_name, age_key, race_key, gender_key,
                    priors, provided_condition_probs, marginale_condition
                )

                assert probability == computed_proba

        assert (num_distributed_condtions == expected_num_conditions)

    def check_symptom_proba(self, symptom_name, module_proba, priors, provided_condition_probs, expected_probability):

        keys_to_avoids, expected_num_conditions = self.get_exception_keys_and_num_condition(
            provided_condition_probs
        )

        marginale_condition = {
            k: sum([priors[k][d] * provided_condition_probs[k][d] for d in priors[k].keys()])
            for k in provided_condition_probs.keys()
        }

        all_possibilities = module_proba['complex_transition']
        num_distributed_condtions = 0

        mean_proba = 0
        contributed_keys = set()

        for possibility in all_possibilities:
            if "condition" in possibility and "distributions" in possibility:
                num_distributed_condtions += 1

                condition_stmts = possibility["condition"]
                distribution_stmts = possibility["distributions"]

                if condition_stmts["condition_type"] == "And":
                    condition_stmts = condition_stmts["conditions"]
                else:
                    condition_stmts = [condition_stmts]

                age_key, race_key, gender_key = self.process_complex_transition(
                    condition_stmts, keys_to_avoids
                )

                probability = distribution_stmts[0]["distribution"]
                contributed_keys.add(
                    age_key + "|" + gender_key + "|" + race_key
                )

                computed_proba, age_race_gender_prior = self.get_symptom_proba(
                    symptom_name, age_key, race_key, gender_key,
                    priors, provided_condition_probs, marginale_condition,
                    expected_probability
                )

                mean_proba += probability * age_race_gender_prior

                assert probability == computed_proba

        assert (num_distributed_condtions == expected_num_conditions)
        assert (round_val(mean_proba) == round_val(expected_probability))

    def test_symcat_2_synthea__generator(self, tmpdir):
        sample_symptoms = [
            ",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            "Abdominal distention,http://www.symcat.com/symptoms/abdominal-distention,Abdominal distention,\"description_1\",\"cause_description_1\",Cirrhosis,http://www.symcat.com/conditions/cirrhosis,18,http://www.symcat.com/conditions/cirrhosis,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            "Abdominal distention,http://www.symcat.com/symptoms/abdominal-distention,Abdominal distention,-''-,\"cause_description_1\",Alcoholic liver disease,http://www.symcat.com/conditions/alcoholic-liver-disease,10,http://www.symcat.com/conditions/alcoholic-liver-disease,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            "Abdominal distention,http://www.symcat.com/symptoms/abdominal-distention,Abdominal distention,-''-,\"cause_description_1\",Heart failure,http://www.symcat.com/conditions/heart-failure,8,http://www.symcat.com/conditions/heart-failure,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            "Abdominal distention,http://www.symcat.com/symptoms/abdominal-distention,Abdominal distention,-''-,\"cause_description_1\",Pleural effusion,http://www.symcat.com/conditions/pleural-effusion,5,http://www.symcat.com/conditions/pleural-effusion,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            "Abdominal distention,http://www.symcat.com/symptoms/abdominal-distention,Abdominal distention,-''-,\"cause_description_1\",Liver disease,http://www.symcat.com/conditions/liver-disease,5,http://www.symcat.com/conditions/liver-disease,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            "Abdominal distention,http://www.symcat.com/symptoms/abdominal-distention,Abdominal distention,-''-,\"cause_description_1\",Anemia,http://www.symcat.com/conditions/anemia,5,http://www.symcat.com/conditions/anemia,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            "Abdominal distention,http://www.symcat.com/symptoms/abdominal-distention,Abdominal distention,-''-,\"cause_description_1\",Pyogenic skin infection,http://www.symcat.com/conditions/pyogenic-skin-infection,5,http://www.symcat.com/conditions/pyogenic-skin-infection,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            "Abdominal distention,http://www.symcat.com/symptoms/abdominal-distention,Abdominal distention,-''-,\"cause_description_1\",Fluid overload,http://www.symcat.com/conditions/fluid-overload,5,http://www.symcat.com/conditions/fluid-overload,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,< 1 years,http://www.symcat.com/demographics/age-1-years,0.8x,Abdominal distention,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,1-4 years,http://www.symcat.com/demographics/age-1-4-years,0.0x,Abdominal distention,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,5-14 years,http://www.symcat.com/demographics/age-5-14-years,0.0x,Abdominal distention,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,15-29 years,http://www.symcat.com/demographics/age-15-29-years,0.3x,Abdominal distention,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,30-44 years,http://www.symcat.com/demographics/age-30-44-years,0.8x,Abdominal distention,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,45-59 years,http://www.symcat.com/demographics/age-45-59-years,1.9x,Abdominal distention,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,60-74 years,http://www.symcat.com/demographics/age-60-74-years,2.4x,Abdominal distention,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,75+ years,http://www.symcat.com/demographics/age-75-years,0.3x,Abdominal distention,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,Male,http://www.symcat.com/demographics/sex-male,1.2x,Abdominal distention,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,Female,http://www.symcat.com/demographics/sex-female,0.9x,Abdominal distention,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,Black,http://www.symcat.com/demographics/race-ethnicity-black,0.9x,Abdominal distention,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,Hispanic,http://www.symcat.com/demographics/race-ethnicity-hispanic,0.5x,Abdominal distention,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,White,http://www.symcat.com/demographics/race-ethnicity-white,1.2x,Abdominal distention,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,Other,http://www.symcat.com/demographics/race-ethnicity-other,0.5x,Abdominal distention,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,Bleeding from ear,http://www.symcat.com/symptoms/bleeding-from-ear,Bleeding from ear,description_2,\"cause_description_2\",Otitis media,http://www.symcat.com/conditions/otitis-media,34,http://www.symcat.com/conditions/otitis-media,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,Bleeding from ear,http://www.symcat.com/symptoms/bleeding-from-ear,Bleeding from ear,description_2,\"cause_description_2\",Otitis externa (swimmer's ear),http://www.symcat.com/conditions/otitis-externa-swimmer-s-ear,15,http://www.symcat.com/conditions/otitis-externa-swimmer-s-ear,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,Bleeding from ear,http://www.symcat.com/symptoms/bleeding-from-ear,Bleeding from ear,description_2,\"cause_description_2\",Burn,http://www.symcat.com/conditions/burn,8,http://www.symcat.com/conditions/burn,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,Bleeding from ear,http://www.symcat.com/symptoms/bleeding-from-ear,Bleeding from ear,description_2,\"cause_description_2\",Injury to the face,http://www.symcat.com/conditions/injury-to-the-face,8,http://www.symcat.com/conditions/injury-to-the-face,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,Bleeding from ear,http://www.symcat.com/symptoms/bleeding-from-ear,Bleeding from ear,description_2,\"cause_description_2\",Ear drum damage,http://www.symcat.com/conditions/ear-drum-damage,7,http://www.symcat.com/conditions/ear-drum-damage,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,Bleeding from ear,http://www.symcat.com/symptoms/bleeding-from-ear,Bleeding from ear,description_2,\"cause_description_2\",Open wound of the ear,http://www.symcat.com/conditions/open-wound-of-the-ear,5,http://www.symcat.com/conditions/open-wound-of-the-ear,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,Bleeding from ear,http://www.symcat.com/symptoms/bleeding-from-ear,Bleeding from ear,description_2,\"cause_description_2\",Foreign body in the ear,http://www.symcat.com/conditions/foreign-body-in-the-ear,3,http://www.symcat.com/conditions/foreign-body-in-the-ear,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,Bleeding from ear,http://www.symcat.com/symptoms/bleeding-from-ear,Bleeding from ear,description_2,\"cause_description_2\",Chronic otitis media,http://www.symcat.com/conditions/chronic-otitis-media,2,http://www.symcat.com/conditions/chronic-otitis-media,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,< 1 years,http://www.symcat.com/demographics/age-1-years,2.1x,Bleeding from ear,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,1-4 years,http://www.symcat.com/demographics/age-1-4-years,4.2x,Bleeding from ear,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,5-14 years,http://www.symcat.com/demographics/age-5-14-years,1.7x,Bleeding from ear,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,15-29 years,http://www.symcat.com/demographics/age-15-29-years,0.7x,Bleeding from ear,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,30-44 years,http://www.symcat.com/demographics/age-30-44-years,0.0x,Bleeding from ear,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,45-59 years,http://www.symcat.com/demographics/age-45-59-years,0.5x,Bleeding from ear,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,60-74 years,http://www.symcat.com/demographics/age-60-74-years,0.3x,Bleeding from ear,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,75+ years,http://www.symcat.com/demographics/age-75-years,1.1x,Bleeding from ear,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,Male,http://www.symcat.com/demographics/sex-male,1.3x,Bleeding from ear,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,Female,http://www.symcat.com/demographics/sex-female,0.0x,Bleeding from ear,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,Black,http://www.symcat.com/demographics/race-ethnicity-black,0.9x,Bleeding from ear,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,Hispanic,http://www.symcat.com/demographics/race-ethnicity-hispanic,1.4x,Bleeding from ear,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,White,http://www.symcat.com/demographics/race-ethnicity-white,0.9x,Bleeding from ear,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,Other,http://www.symcat.com/demographics/race-ethnicity-other,0.0x,Bleeding from ear,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,"
        ]
        symptoms = tmpdir.join("symptoms.csv")
        sample_data = "\n".join(sample_symptoms)
        symptoms.write(sample_data)
        filename_symptom = os.path.join(tmpdir, 'symptoms.csv')
        symptom_map = parse_symcat_symptoms(filename_symptom)

        sample_conditions = [
            ",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            "Abdominal aortic aneurysm,http://www.symcat.com/conditions/abdominal-aortic-aneurysm,Abdominal aortic aneurysm,\"condition_description_1\",\"symptom_summary_1\",Bleeding from ear,http://www.symcat.com/symptoms/bleeding-from-ear,53,http://www.symcat.com/symptoms/bleeding-from-ear,Abdominal aortic aneurysm,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            "Abdominal aortic aneurysm,http://www.symcat.com/conditions/abdominal-aortic-aneurysm,Abdominal aortic aneurysm,-''-,\"symptom_summary_1\",Abdominal distention,http://www.symcat.com/symptoms/abdominal-distention,35,http://www.symcat.com/symptoms/abdominal-distention,Abdominal aortic aneurysm,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,< 1 years,http://www.symcat.com/demographics/age-1-years,0.0x,Abdominal aortic aneurysm,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,1-4 years,http://www.symcat.com/demographics/age-1-4-years,0.0x,Abdominal aortic aneurysm,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,5-14 years,http://www.symcat.com/demographics/age-5-14-years,0.0x,Abdominal aortic aneurysm,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,15-29 years,http://www.symcat.com/demographics/age-15-29-years,0.0x,Abdominal aortic aneurysm,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,30-44 years,http://www.symcat.com/demographics/age-30-44-years,0.1x,Abdominal aortic aneurysm,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,45-59 years,http://www.symcat.com/demographics/age-45-59-years,0.4x,Abdominal aortic aneurysm,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,60-74 years,http://www.symcat.com/demographics/age-60-74-years,2.9x,Abdominal aortic aneurysm,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,75+ years,http://www.symcat.com/demographics/age-75-years,5.0x,Abdominal aortic aneurysm,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,Male,http://www.symcat.com/demographics/sex-male,1.8x,Abdominal aortic aneurysm,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,Female,http://www.symcat.com/demographics/sex-female,0.4x,Abdominal aortic aneurysm,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,Black,http://www.symcat.com/demographics/race-ethnicity-black,0.4x,Abdominal aortic aneurysm,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,Hispanic,http://www.symcat.com/demographics/race-ethnicity-hispanic,0.6x,Abdominal aortic aneurysm,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,White,http://www.symcat.com/demographics/race-ethnicity-white,1.4x,Abdominal aortic aneurysm,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,Other,http://www.symcat.com/demographics/race-ethnicity-other,0.1x,Abdominal aortic aneurysm,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,2,http://www.symcat.com/conditions?q=&page=2,Appendicitis,http://www.symcat.com/conditions/appendicitis,Appendicitis,\"condition_description_2\",\"symptom_summary_2\",Abdominal distention,http://www.symcat.com/symptoms/abdominal-distention,91,http://www.symcat.com/symptoms/abdominal-distention,Appendicitis,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,2,http://www.symcat.com/conditions?q=&page=2,,,,,,,,,,,< 1 years,http://www.symcat.com/demographics/age-1-years,0.1x,Appendicitis,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,2,http://www.symcat.com/conditions?q=&page=2,,,,,,,,,,,1-4 years,http://www.symcat.com/demographics/age-1-4-years,0.3x,Appendicitis,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,2,http://www.symcat.com/conditions?q=&page=2,,,,,,,,,,,5-14 years,http://www.symcat.com/demographics/age-5-14-years,2.2x,Appendicitis,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,2,http://www.symcat.com/conditions?q=&page=2,,,,,,,,,,,15-29 years,http://www.symcat.com/demographics/age-15-29-years,1.9x,Appendicitis,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,2,http://www.symcat.com/conditions?q=&page=2,,,,,,,,,,,30-44 years,http://www.symcat.com/demographics/age-30-44-years,1.0x,Appendicitis,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,2,http://www.symcat.com/conditions?q=&page=2,,,,,,,,,,,45-59 years,http://www.symcat.com/demographics/age-45-59-years,0.7x,Appendicitis,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,2,http://www.symcat.com/conditions?q=&page=2,,,,,,,,,,,60-74 years,http://www.symcat.com/demographics/age-60-74-years,0.5x,Appendicitis,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,2,http://www.symcat.com/conditions?q=&page=2,,,,,,,,,,,75+ years,http://www.symcat.com/demographics/age-75-years,0.2x,Appendicitis,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,2,http://www.symcat.com/conditions?q=&page=2,,,,,,,,,,,,,,,Male,http://www.symcat.com/demographics/sex-male,1.3x,Appendicitis,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,2,http://www.symcat.com/conditions?q=&page=2,,,,,,,,,,,,,,,Female,http://www.symcat.com/demographics/sex-female,0.8x,Appendicitis,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,2,http://www.symcat.com/conditions?q=&page=2,,,,,,,,,,,,,,,,,,,Black,http://www.symcat.com/demographics/race-ethnicity-black,0.4x,Appendicitis,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,2,http://www.symcat.com/conditions?q=&page=2,,,,,,,,,,,,,,,,,,,Hispanic,http://www.symcat.com/demographics/race-ethnicity-hispanic,1.5x,Appendicitis,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,2,http://www.symcat.com/conditions?q=&page=2,,,,,,,,,,,,,,,,,,,White,http://www.symcat.com/demographics/race-ethnicity-white,0.0x,Appendicitis,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,2,http://www.symcat.com/conditions?q=&page=2,,,,,,,,,,,,,,,,,,,Other,http://www.symcat.com/demographics/race-ethnicity-other,1.3x,Appendicitis,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,"
        ]
        conditions = tmpdir.join("conditions.csv")
        sample_data_conditions = "\n".join(sample_conditions)
        conditions.write(sample_data_conditions)
        filename_condition = os.path.join(tmpdir, 'conditions.csv')
        condition_map = parse_symcat_conditions(filename_condition)

        config_data = [
            "[Gender]",
            "sex-male = 1.2",
            "sex-female = 0.8",
            "",
            "[Race]",
            "race-ethnicity-black = 0.3",
            "race-ethnicity-hispanic = 0.2",
            "race-ethnicity-white = 0.3",
            "race-ethnicity-other = 0.1",
            "race-ethnicity-asian = 0.05",
            "race-ethnicity-native = 0.05",
            "",
            "[Age]",
            "age-1-years = 0.1",
            "age-1-4-years = 0.2",
            "age-5-14-years = 0.1",
            "age-15-29-years = 0.2",
            "age-30-44-years = 0.1",
            "age-45-59-years = 0.2",
            "age-60-74-years = 0.09",
            "age-75-years = 0.01",
            "",
            "[Symptoms]",
            "symptom1 = 0.6",
            "",
            "[Conditions]",
            "condition1 = 0.3",
        ]

        config_file = tmpdir.join("priors.ini")
        sample_data = "\n".join(config_data)
        config_file.write(sample_data)
        filename_config = os.path.join(tmpdir, "priors.ini")
        priors = load_config(filename_config)

        modules = {
            key: generate_synthea_module(symptom_map, value, priors)
            for key, value in condition_map.items()
        }

        key1 = slugify_condition("Abdominal aortic aneurysm")
        key2 = slugify_condition("Appendicitis")

        name = "name"
        state = "states"
        sym = "symptom"

        assert len(modules) == 2

        ##################### Test for condition 1 ############################

        assert key1 in modules
        assert modules[key1][name] == "Abdominal aortic aneurysm"
        provided_condition_probs = {
            "Gender": {
                "sex-male": prob_val(1.8),
                "sex-female": prob_val(0.4),
            },
            "Race": {
                "race-ethnicity-black": prob_val(0.4),
                "race-ethnicity-hispanic": prob_val(0.6),
                "race-ethnicity-white": prob_val(1.4),
                "race-ethnicity-other": prob_val(0.1),
                "race-ethnicity-asian": prob_val(0.1),
                "race-ethnicity-native": prob_val(0.1),
            },

            "Age": {
                "age-1-years": prob_val(0.0),
                "age-1-4-years": prob_val(0.0),
                "age-5-14-years": prob_val(0.0),
                "age-15-29-years": prob_val(0.0),
                "age-30-44-years": prob_val(0.1),
                "age-45-59-years": prob_val(0.4),
                "age-60-74-years": prob_val(2.9),
                "age-75-years": prob_val(5.0),
            },
        }
        self.check_condition_proba(
            modules[key1][name],
            modules[key1][state]['Potential_Infection'],
            priors,
            provided_condition_probs
        )

        assert modules[key1][state]["Symptom_1"][sym] == "Bleeding from ear"
        expected_symptom_probability = 0.53
        provided_symptom_probs = {
            "Gender": {
                "sex-male": prob_val(1.3),
                "sex-female": prob_val(0.0),
            },
            "Race": {
                "race-ethnicity-black": prob_val(0.9),
                "race-ethnicity-hispanic": prob_val(1.4),
                "race-ethnicity-white": prob_val(0.9),
                "race-ethnicity-other": prob_val(0.0),
                "race-ethnicity-asian": prob_val(0.0),
                "race-ethnicity-native": prob_val(0.0),
            },
            "Age": {
                "age-1-years": prob_val(2.1),
                "age-1-4-years": prob_val(4.2),
                "age-5-14-years": prob_val(1.7),
                "age-15-29-years": prob_val(0.7),
                "age-30-44-years": prob_val(0.0),
                "age-45-59-years": prob_val(0.5),
                "age-60-74-years": prob_val(0.3),
                "age-75-years": prob_val(1.1),
            },
        }
        self.check_symptom_proba(
            modules[key1][state]["Symptom_1"]["symptom"],
            modules[key1][state]["Simple_Transition_1"],
            priors,
            provided_symptom_probs,
            expected_symptom_probability
        )

        assert modules[key1][state]["Symptom_2"][sym] == "Abdominal distention"
        expected_symptom_probability = 0.35
        provided_symptom_probs = {
            "Gender": {
                "sex-male": prob_val(1.2),
                "sex-female": prob_val(0.9),
            },
            "Race": {
                "race-ethnicity-black": prob_val(0.9),
                "race-ethnicity-hispanic": prob_val(0.5),
                "race-ethnicity-white": prob_val(1.2),
                "race-ethnicity-other": prob_val(0.5),
                "race-ethnicity-asian": prob_val(0.5),
                "race-ethnicity-native": prob_val(0.5),
            },
            "Age": {
                "age-1-years": prob_val(0.8),
                "age-1-4-years": prob_val(0.0),
                "age-5-14-years": prob_val(0.0),
                "age-15-29-years": prob_val(0.3),
                "age-30-44-years": prob_val(0.8),
                "age-45-59-years": prob_val(1.9),
                "age-60-74-years": prob_val(2.4),
                "age-75-years": prob_val(0.3),
            },
        }
        self.check_symptom_proba(
            modules[key1][state]["Symptom_2"]["symptom"],
            modules[key1][state]["Simple_Transition_2"],
            priors,
            provided_symptom_probs,
            expected_symptom_probability
        )

        ##################### Test for condition 2 ############################
        assert key2 in modules
        assert modules[key2][name] == "Appendicitis"

        provided_condition_probs = {
            "Gender": {
                "sex-male": prob_val(1.3),
                "sex-female": prob_val(0.8),
            },
            "Race": {
                "race-ethnicity-black": prob_val(0.4),
                "race-ethnicity-hispanic": prob_val(1.5),
                "race-ethnicity-white": prob_val(0.0),
                "race-ethnicity-other": prob_val(1.3),
                "race-ethnicity-asian": prob_val(1.3),
                "race-ethnicity-native": prob_val(1.3),
            },

            "Age": {
                "age-1-years": prob_val(0.1),
                "age-1-4-years": prob_val(0.3),
                "age-5-14-years": prob_val(2.2),
                "age-15-29-years": prob_val(1.9),
                "age-30-44-years": prob_val(1.0),
                "age-45-59-years": prob_val(0.7),
                "age-60-74-years": prob_val(0.5),
                "age-75-years": prob_val(0.2),
            },
        }
        self.check_condition_proba(
            modules[key2][name],
            modules[key2][state]['Potential_Infection'],
            priors,
            provided_condition_probs
        )

        assert modules[key2][state]["Symptom_1"][sym] == "Abdominal distention"
        expected_symptom_probability = 0.91
        provided_symptom_probs = {
            "Gender": {
                "sex-male": prob_val(1.2),
                "sex-female": prob_val(0.9),
            },
            "Race": {
                "race-ethnicity-black": prob_val(0.9),
                "race-ethnicity-hispanic": prob_val(0.5),
                "race-ethnicity-white": prob_val(1.2),
                "race-ethnicity-other": prob_val(0.5),
                "race-ethnicity-asian": prob_val(0.5),
                "race-ethnicity-native": prob_val(0.5),
            },

            "Age": {
                "age-1-years": prob_val(0.8),
                "age-1-4-years": prob_val(0.0),
                "age-5-14-years": prob_val(0.0),
                "age-15-29-years": prob_val(0.3),
                "age-30-44-years": prob_val(0.8),
                "age-45-59-years": prob_val(1.9),
                "age-60-74-years": prob_val(2.4),
                "age-75-years": prob_val(0.3),
            },
        }
        self.check_symptom_proba(
            modules[key2][state]["Symptom_1"]["symptom"],
            modules[key2][state]["Simple_Transition_1"],
            priors,
            provided_symptom_probs,
            expected_symptom_probability
        )
