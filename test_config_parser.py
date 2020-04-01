import os

from configFileParser import load_config


class TestConfigFileParser(object):

    def sum_prob_distribution(self, probs):
        sum_prob = 0
        for key in probs.keys():
            sum_prob += probs[key]
        return round(sum_prob, 2)

    def test_default(self):
        config_file = ""
        priors = load_config(config_file)

        assert 1.0 == self.sum_prob_distribution(priors['Gender'])
        assert 1.0 == self.sum_prob_distribution(priors['Age'])
        assert 1.0 == self.sum_prob_distribution(priors['Race'])

    def test_empty_config(self, tmpdir):

        config_data = [
            "[Gender]",
            "sex-male = ",
            "sex-female = ",
            "",
            "[Race]",
            "race-ethnicity-black = ",
            "race-ethnicity-hispanic = ",
            "race-ethnicity-white = ",
            "race-ethnicity-other = ",
            "race-ethnicity-asian = ",
            "race-ethnicity-native = ",
            "",
            "[Age]",
            "age-1-years = ",
            "age-1-4-years = ",
            "age-5-14-years = ",
            "age-15-29-years = ",
            "age-30-44-years = ",
            "age-45-59-years = ",
            "age-60-74-years = ",
            "age-75-years = ",
            "",
            "[Symptoms]",
            "",
            "[Conditions]",
        ]

        config_file = tmpdir.join("priors.ini")
        sample_data = "\n".join(config_data)
        config_file.write(sample_data)

        filename = os.path.join(tmpdir, "priors.ini")
        priors = load_config(filename)

        assert 1.0 == self.sum_prob_distribution(priors['Gender'])
        assert 1.0 == self.sum_prob_distribution(priors['Age'])
        assert 1.0 == self.sum_prob_distribution(priors['Race'])

    def test_config(self, tmpdir):

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
            "symptom2 = ",
            "",
            "[Conditions]",
            "condition1 = 0.3",
            "condition2 = ",
        ]

        config_file = tmpdir.join("priors.ini")
        sample_data = "\n".join(config_data)
        config_file.write(sample_data)

        filename = os.path.join(tmpdir, "priors.ini")
        priors = load_config(filename)

        assert 1.0 == self.sum_prob_distribution(priors['Gender'])
        assert 1.0 == self.sum_prob_distribution(priors['Age'])
        assert 1.0 == self.sum_prob_distribution(priors['Race'])

        assert priors['Gender']["sex-male"] == 0.6
        assert priors['Gender']["sex-female"] == 0.4

        assert priors['Age']["age-1-years"] == 0.1
        assert priors['Age']["age-1-4-years"] == 0.2
        assert priors['Age']["age-5-14-years"] == 0.1
        assert priors['Age']["age-15-29-years"] == 0.2
        assert priors['Age']["age-30-44-years"] == 0.1
        assert priors['Age']["age-45-59-years"] == 0.2
        assert priors['Age']["age-60-74-years"] == 0.09
        assert priors['Age']["age-75-years"] == 0.01

        assert priors['Race']["race-ethnicity-black"] == 0.3
        assert priors['Race']["race-ethnicity-hispanic"] == 0.2
        assert priors['Race']["race-ethnicity-white"] == 0.3
        assert priors['Race']["race-ethnicity-other"] == 0.1
        assert priors['Race']["race-ethnicity-asian"] == 0.05
        assert priors['Race']["race-ethnicity-native"] == 0.05

        assert priors['Symptoms']["symptom1"] == 0.6
        assert priors['Symptoms']["symptom2"] == 1.0
        assert priors['Conditions']["condition1"] == 0.3
        assert priors['Conditions']["condition2"] == 1.0
