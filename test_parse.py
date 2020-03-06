import os

from parse import parse_symcat_conditions, parse_symcat_symptoms, slugify_condition


class TestParser(object):

    def test_symcat_symptom__parser(self, tmpdir):
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
            ",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,30-44 years,http://www.symcat.com/demographics/age-30-44-years,0.8x,Bleeding from ear,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,45-59 years,http://www.symcat.com/demographics/age-45-59-years,0.5x,Bleeding from ear,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,60-74 years,http://www.symcat.com/demographics/age-60-74-years,0.3x,Bleeding from ear,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,75+ years,http://www.symcat.com/demographics/age-75-years,1.1x,Bleeding from ear,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,Male,http://www.symcat.com/demographics/sex-male,1.3x,Bleeding from ear,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,Female,http://www.symcat.com/demographics/sex-female,0.8x,Bleeding from ear,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,Black,http://www.symcat.com/demographics/race-ethnicity-black,0.9x,Bleeding from ear,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,Hispanic,http://www.symcat.com/demographics/race-ethnicity-hispanic,1.4x,Bleeding from ear,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,White,http://www.symcat.com/demographics/race-ethnicity-white,0.9x,Bleeding from ear,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,Other,http://www.symcat.com/demographics/race-ethnicity-other,1.0x,Bleeding from ear,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,"
        ]
        symptoms = tmpdir.join("symptoms.csv")
        sample_data = "\n".join(sample_symptoms)
        symptoms.write(sample_data)
        filename = os.path.join(tmpdir, 'symptoms.csv')
        symptom_map = parse_symcat_symptoms(filename)

        key1 = "abdominal-distention"
        key2 = "bleeding-from-ear"

        com = "common_causes"
        age = "age"
        sex = "sex"
        race = "race"
        prob = "probability"
        odd = "odds"

        assert len(symptom_map) == 2

        ##################### Test for symptom 1 ##############################
        assert key1 in symptom_map
        assert symptom_map[key1]["name"] == "Abdominal distention"
        assert symptom_map[key1]["description"] == "description_1"

        assert len(symptom_map[key1][com]) == 8
        assert symptom_map[key1][com]["cause-cirrhosis"][prob] == 18
        assert symptom_map[key1][com][
            "cause-alcoholic-liver-disease"][prob] == 10
        assert symptom_map[key1][com]["cause-heart-failure"][prob] == 8
        assert symptom_map[key1][com]["cause-pleural-effusion"][prob] == 5
        assert symptom_map[key1][com]["cause-liver-disease"][prob] == 5
        assert symptom_map[key1][com]["cause-anemia"][prob] == 5
        assert symptom_map[key1][com][
            "cause-pyogenic-skin-infection"][prob] == 5
        assert symptom_map[key1][com]["cause-fluid-overload"][prob] == 5

        assert len(symptom_map[key1][age]) == 8
        assert symptom_map[key1][age]["age-1-years"][odd] == 0.8
        assert symptom_map[key1][age]["age-1-4-years"][odd] == 0.0
        assert symptom_map[key1][age]["age-5-14-years"][odd] == 0.0
        assert symptom_map[key1][age]["age-15-29-years"][odd] == 0.3
        assert symptom_map[key1][age]["age-30-44-years"][odd] == 0.8
        assert symptom_map[key1][age]["age-45-59-years"][odd] == 1.9
        assert symptom_map[key1][age]["age-60-74-years"][odd] == 2.4
        assert symptom_map[key1][age]["age-75-years"][odd] == 0.3

        assert len(symptom_map[key1][sex]) == 2
        assert symptom_map[key1][sex]["sex-male"][odd] == 1.2
        assert symptom_map[key1][sex]["sex-female"][odd] == 0.9

        assert len(symptom_map[key1][race]) == 4
        assert symptom_map[key1][race]["race-ethnicity-black"][odd] == 0.9
        assert symptom_map[key1][race]["race-ethnicity-hispanic"][odd] == 0.5
        assert symptom_map[key1][race]["race-ethnicity-white"][odd] == 1.2
        assert symptom_map[key1][race]["race-ethnicity-other"][odd] == 0.5

        ##################### Test for symptom 2 ##############################
        assert key2 in symptom_map
        assert symptom_map[key2]["name"] == "Bleeding from ear"
        assert symptom_map[key2]["description"] == "description_2"

        assert len(symptom_map[key2][com]) == 8
        assert symptom_map[key2][com]["cause-otitis-media"][prob] == 34
        assert symptom_map[key2][com][
            "cause-otitis-externa-swimmer-s-ear"][prob] == 15
        assert symptom_map[key2][com]["cause-burn"][prob] == 8
        assert symptom_map[key2][com]["cause-injury-to-the-face"][prob] == 8
        assert symptom_map[key2][com]["cause-ear-drum-damage"][prob] == 7
        assert symptom_map[key2][com]["cause-open-wound-of-the-ear"][prob] == 5
        assert symptom_map[key2][com][
            "cause-foreign-body-in-the-ear"][prob] == 3
        assert symptom_map[key2][com]["cause-chronic-otitis-media"][prob] == 2

        assert len(symptom_map[key2][age]) == 8
        assert symptom_map[key2][age]["age-1-years"][odd] == 2.1
        assert symptom_map[key2][age]["age-1-4-years"][odd] == 4.2
        assert symptom_map[key2][age]["age-5-14-years"][odd] == 1.7
        assert symptom_map[key2][age]["age-15-29-years"][odd] == 0.7
        assert symptom_map[key2][age]["age-30-44-years"][odd] == 0.8
        assert symptom_map[key2][age]["age-45-59-years"][odd] == 0.5
        assert symptom_map[key2][age]["age-60-74-years"][odd] == 0.3
        assert symptom_map[key2][age]["age-75-years"][odd] == 1.1

        assert len(symptom_map[key2][sex]) == 2
        assert symptom_map[key2][sex]["sex-male"][odd] == 1.3
        assert symptom_map[key2][sex]["sex-female"][odd] == 0.8

        assert len(symptom_map[key2][race]) == 4
        assert symptom_map[key2][race]["race-ethnicity-black"][odd] == 0.9
        assert symptom_map[key2][race]["race-ethnicity-hispanic"][odd] == 1.4
        assert symptom_map[key2][race]["race-ethnicity-white"][odd] == 0.9
        assert symptom_map[key2][race]["race-ethnicity-other"][odd] == 1.0

    def test_symcat_condition__parser(self, tmpdir):
        sample_conditions = [
            ",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            "Abdominal aortic aneurysm,http://www.symcat.com/conditions/abdominal-aortic-aneurysm,Abdominal aortic aneurysm,\"condition_description_1\",\"symptom_summary_1\",Sharp abdominal pain,http://www.symcat.com/symptoms/sharp-abdominal-pain,53,http://www.symcat.com/symptoms/sharp-abdominal-pain,Abdominal aortic aneurysm,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            "Abdominal aortic aneurysm,http://www.symcat.com/conditions/abdominal-aortic-aneurysm,Abdominal aortic aneurysm,-''-,\"symptom_summary_1\",Back pain,http://www.symcat.com/symptoms/back-pain,35,http://www.symcat.com/symptoms/back-pain,Abdominal aortic aneurysm,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            "Abdominal aortic aneurysm,http://www.symcat.com/conditions/abdominal-aortic-aneurysm,Abdominal aortic aneurysm,-''-,\"symptom_summary_1\",Shortness of breath,http://www.symcat.com/symptoms/shortness-of-breath,28,http://www.symcat.com/symptoms/shortness-of-breath,Abdominal aortic aneurysm,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            "Abdominal aortic aneurysm,http://www.symcat.com/conditions/abdominal-aortic-aneurysm,Abdominal aortic aneurysm,-''-,\"symptom_summary_1\",Sharp chest pain,http://www.symcat.com/symptoms/sharp-chest-pain,28,http://www.symcat.com/symptoms/sharp-chest-pain,Abdominal aortic aneurysm,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            "Abdominal aortic aneurysm,http://www.symcat.com/conditions/abdominal-aortic-aneurysm,Abdominal aortic aneurysm,-''-,\"symptom_summary_1\",Side pain,http://www.symcat.com/symptoms/side-pain,23,http://www.symcat.com/symptoms/side-pain,Abdominal aortic aneurysm,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            "Abdominal aortic aneurysm,http://www.symcat.com/conditions/abdominal-aortic-aneurysm,Abdominal aortic aneurysm,-''-,\"symptom_summary_1\",Burning abdominal pain,http://www.symcat.com/symptoms/burning-abdominal-pain,23,http://www.symcat.com/symptoms/burning-abdominal-pain,Abdominal aortic aneurysm,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            "Abdominal aortic aneurysm,http://www.symcat.com/conditions/abdominal-aortic-aneurysm,Abdominal aortic aneurysm,-''-,\"symptom_summary_1\",Swollen abdomen,http://www.symcat.com/symptoms/swollen-abdomen,13,http://www.symcat.com/symptoms/swollen-abdomen,Abdominal aortic aneurysm,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            "Abdominal aortic aneurysm,http://www.symcat.com/conditions/abdominal-aortic-aneurysm,Abdominal aortic aneurysm,-''-,\"symptom_summary_1\",Palpitations,http://www.symcat.com/symptoms/palpitations,13,http://www.symcat.com/symptoms/palpitations,Abdominal aortic aneurysm,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            "Abdominal aortic aneurysm,http://www.symcat.com/conditions/abdominal-aortic-aneurysm,Abdominal aortic aneurysm,-''-,\"symptom_summary_1\",Retention of urine,http://www.symcat.com/symptoms/retention-of-urine,13,http://www.symcat.com/symptoms/retention-of-urine,Abdominal aortic aneurysm,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            "Abdominal aortic aneurysm,http://www.symcat.com/conditions/abdominal-aortic-aneurysm,Abdominal aortic aneurysm,-''-,\"symptom_summary_1\",Arm swelling,http://www.symcat.com/symptoms/arm-swelling,7,http://www.symcat.com/symptoms/arm-swelling,Abdominal aortic aneurysm,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            "Abdominal aortic aneurysm,http://www.symcat.com/conditions/abdominal-aortic-aneurysm,Abdominal aortic aneurysm,-''-,\"symptom_summary_1\",Groin pain,http://www.symcat.com/symptoms/groin-pain,7,http://www.symcat.com/symptoms/groin-pain,Abdominal aortic aneurysm,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            "Abdominal aortic aneurysm,http://www.symcat.com/conditions/abdominal-aortic-aneurysm,Abdominal aortic aneurysm,-''-,\"symptom_summary_1\",Pallor,http://www.symcat.com/symptoms/pallor,7,http://www.symcat.com/symptoms/pallor,Abdominal aortic aneurysm,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
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
            ",,,,,,,,,,,,,,,,,,,,,,,2,http://www.symcat.com/conditions?q=&page=2,Appendicitis,http://www.symcat.com/conditions/appendicitis,Appendicitis,\"condition_description_2\",\"symptom_summary_2\",Sharp abdominal pain,http://www.symcat.com/symptoms/sharp-abdominal-pain,91,http://www.symcat.com/symptoms/sharp-abdominal-pain,Appendicitis,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,2,http://www.symcat.com/conditions?q=&page=2,Appendicitis,http://www.symcat.com/conditions/appendicitis,Appendicitis,-''-,\"symptom_summary_2\",Lower abdominal pain,http://www.symcat.com/symptoms/lower-abdominal-pain,64,http://www.symcat.com/symptoms/lower-abdominal-pain,Appendicitis,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,2,http://www.symcat.com/conditions?q=&page=2,Appendicitis,http://www.symcat.com/conditions/appendicitis,Appendicitis,-''-,\"symptom_summary_2\",Vomiting,http://www.symcat.com/symptoms/vomiting,57,http://www.symcat.com/symptoms/vomiting,Appendicitis,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,2,http://www.symcat.com/conditions?q=&page=2,Appendicitis,http://www.symcat.com/conditions/appendicitis,Appendicitis,-''-,\"symptom_summary_2\",Nausea,http://www.symcat.com/symptoms/nausea,54,http://www.symcat.com/symptoms/nausea,Appendicitis,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,2,http://www.symcat.com/conditions?q=&page=2,Appendicitis,http://www.symcat.com/conditions/appendicitis,Appendicitis,-''-,\"symptom_summary_2\",Fever,http://www.symcat.com/symptoms/fever,44,http://www.symcat.com/symptoms/fever,Appendicitis,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,2,http://www.symcat.com/conditions?q=&page=2,Appendicitis,http://www.symcat.com/conditions/appendicitis,Appendicitis,-''-,\"symptom_summary_2\",Burning abdominal pain,http://www.symcat.com/symptoms/burning-abdominal-pain,41,http://www.symcat.com/symptoms/burning-abdominal-pain,Appendicitis,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,2,http://www.symcat.com/conditions?q=&page=2,Appendicitis,http://www.symcat.com/conditions/appendicitis,Appendicitis,-''-,\"symptom_summary_2\",Side pain,http://www.symcat.com/symptoms/side-pain,29,http://www.symcat.com/symptoms/side-pain,Appendicitis,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,2,http://www.symcat.com/conditions?q=&page=2,Appendicitis,http://www.symcat.com/conditions/appendicitis,Appendicitis,-''-,\"symptom_summary_2\",Diarrhea,http://www.symcat.com/symptoms/diarrhea,25,http://www.symcat.com/symptoms/diarrhea,Appendicitis,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,2,http://www.symcat.com/conditions?q=&page=2,Appendicitis,http://www.symcat.com/conditions/appendicitis,Appendicitis,-''-,\"symptom_summary_2\",Upper abdominal pain,http://www.symcat.com/symptoms/upper-abdominal-pain,20,http://www.symcat.com/symptoms/upper-abdominal-pain,Appendicitis,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,2,http://www.symcat.com/conditions?q=&page=2,Appendicitis,http://www.symcat.com/conditions/appendicitis,Appendicitis,-''-,\"symptom_summary_2\",Chills,http://www.symcat.com/symptoms/chills,11,http://www.symcat.com/symptoms/chills,Appendicitis,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,2,http://www.symcat.com/conditions?q=&page=2,Appendicitis,http://www.symcat.com/conditions/appendicitis,Appendicitis,-''-,\"symptom_summary_2\",Decreased appetite,http://www.symcat.com/symptoms/decreased-appetite,11,http://www.symcat.com/symptoms/decreased-appetite,Appendicitis,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,2,http://www.symcat.com/conditions?q=&page=2,Appendicitis,http://www.symcat.com/conditions/appendicitis,Appendicitis,-''-,\"symptom_summary_2\",Stomach bloating,http://www.symcat.com/symptoms/stomach-bloating,5,http://www.symcat.com/symptoms/stomach-bloating,Appendicitis,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,2,http://www.symcat.com/conditions?q=&page=2,,,,,,,,,,,< 1 years,http://www.symcat.com/demographics/age-1-years,0.0x,Appendicitis,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
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
            ",,,,,,,,,,,,,,,,,,,,,,,2,http://www.symcat.com/conditions?q=&page=2,,,,,,,,,,,,,,,,,,,White,http://www.symcat.com/demographics/race-ethnicity-white,1.0x,Appendicitis,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
            ",,,,,,,,,,,,,,,,,,,,,,,2,http://www.symcat.com/conditions?q=&page=2,,,,,,,,,,,,,,,,,,,Other,http://www.symcat.com/demographics/race-ethnicity-other,1.3x,Appendicitis,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,"
        ]
        conditions = tmpdir.join("conditions.csv")
        sample_data = "\n".join(sample_conditions)
        conditions.write(sample_data)
        filename = os.path.join(tmpdir, 'conditions.csv')
        condition_map = parse_symcat_conditions(filename)

        key1 = slugify_condition("Abdominal aortic aneurysm")
        key2 = slugify_condition("Appendicitis")

        desc = "condition_description"
        name = "condition_name"
        sym = "symptoms"
        age = "age"
        sex = "sex"
        race = "race"
        prob = "probability"
        odd = "odds"

        assert len(condition_map) == 2

        ##################### Test for condition 1 ############################
        assert key1 in condition_map
        assert condition_map[key1][name] == "Abdominal aortic aneurysm"
        assert condition_map[key1][desc] == "condition_description_1"

        assert len(condition_map[key1][sym]) == 12
        assert condition_map[key1][sym]["sharp-abdominal-pain"][prob] == 53
        assert condition_map[key1][sym]["back-pain"][prob] == 35
        assert condition_map[key1][sym]["shortness-of-breath"][prob] == 28
        assert condition_map[key1][sym]["sharp-chest-pain"][prob] == 28
        assert condition_map[key1][sym]["side-pain"][prob] == 23
        assert condition_map[key1][sym]["burning-abdominal-pain"][prob] == 23
        assert condition_map[key1][sym]["swollen-abdomen"][prob] == 13
        assert condition_map[key1][sym]["palpitations"][prob] == 13
        assert condition_map[key1][sym]["retention-of-urine"][prob] == 13
        assert condition_map[key1][sym]["arm-swelling"][prob] == 7
        assert condition_map[key1][sym]["groin-pain"][prob] == 7
        assert condition_map[key1][sym]["pallor"][prob] == 7

        assert len(condition_map[key1][age]) == 8
        assert condition_map[key1][age]["age-1-years"][odd] == 0.0
        assert condition_map[key1][age]["age-1-4-years"][odd] == 0.0
        assert condition_map[key1][age]["age-5-14-years"][odd] == 0.0
        assert condition_map[key1][age]["age-15-29-years"][odd] == 0.0
        assert condition_map[key1][age]["age-30-44-years"][odd] == 0.1
        assert condition_map[key1][age]["age-45-59-years"][odd] == 0.4
        assert condition_map[key1][age]["age-60-74-years"][odd] == 2.9
        assert condition_map[key1][age]["age-75-years"][odd] == 5.0

        assert len(condition_map[key1][sex]) == 2
        assert condition_map[key1][sex]["sex-male"][odd] == 1.8
        assert condition_map[key1][sex]["sex-female"][odd] == 0.4

        assert len(condition_map[key1][race]) == 4
        assert condition_map[key1][race]["race-ethnicity-black"][odd] == 0.4
        assert condition_map[key1][race]["race-ethnicity-hispanic"][odd] == 0.6
        assert condition_map[key1][race]["race-ethnicity-white"][odd] == 1.4
        assert condition_map[key1][race]["race-ethnicity-other"][odd] == 0.1

        ##################### Test for condition 2 ############################
        assert key2 in condition_map
        assert condition_map[key2][name] == "Appendicitis"
        assert condition_map[key2][desc] == "condition_description_2"

        assert len(condition_map[key2][sym]) == 12
        assert condition_map[key2][sym]["sharp-abdominal-pain"][prob] == 91
        assert condition_map[key2][sym]["lower-abdominal-pain"][prob] == 64
        assert condition_map[key2][sym]["vomiting"][prob] == 57
        assert condition_map[key2][sym]["nausea"][prob] == 54
        assert condition_map[key2][sym]["fever"][prob] == 44
        assert condition_map[key2][sym]["burning-abdominal-pain"][prob] == 41
        assert condition_map[key2][sym]["side-pain"][prob] == 29
        assert condition_map[key2][sym]["diarrhea"][prob] == 25
        assert condition_map[key2][sym]["upper-abdominal-pain"][prob] == 20
        assert condition_map[key2][sym]["chills"][prob] == 11
        assert condition_map[key2][sym]["decreased-appetite"][prob] == 11
        assert condition_map[key2][sym]["stomach-bloating"][prob] == 5

        assert len(condition_map[key2][age]) == 8
        assert condition_map[key2][age]["age-1-years"][odd] == 0.0
        assert condition_map[key2][age]["age-1-4-years"][odd] == 0.3
        assert condition_map[key2][age]["age-5-14-years"][odd] == 2.2
        assert condition_map[key2][age]["age-15-29-years"][odd] == 1.9
        assert condition_map[key2][age]["age-30-44-years"][odd] == 1.0
        assert condition_map[key2][age]["age-45-59-years"][odd] == 0.7
        assert condition_map[key2][age]["age-60-74-years"][odd] == 0.5
        assert condition_map[key2][age]["age-75-years"][odd] == 0.2

        assert len(condition_map[key2][sex]) == 2
        assert condition_map[key2][sex]["sex-male"][odd] == 1.3
        assert condition_map[key2][sex]["sex-female"][odd] == 0.8

        assert len(condition_map[key2][race]) == 4
        assert condition_map[key2][race]["race-ethnicity-black"][odd] == 0.4
        assert condition_map[key2][race]["race-ethnicity-hispanic"][odd] == 1.5
        assert condition_map[key2][race]["race-ethnicity-white"][odd] == 1.0
        assert condition_map[key2][race]["race-ethnicity-other"][odd] == 1.3
