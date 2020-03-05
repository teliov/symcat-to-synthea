import os

from parse import parse_symcat_conditions, parse_symcat_symptoms, slugify_condition
from generate import generate_synthea_module


def prob_val(x, ndigits=4):
    return round(x / (1 + x), ndigits)


class TestGenerator(object):

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

        key1 = "abdominal-distention"
        key2 = "bleeding-from-ear"

        prob = "distribution"
        name = "name"
        state = "states"
        dist_dis = "distributed_transition"
        M = "Male"
        F = "Female"
        black = "Race_Black"
        hispa = "Race_Hispanic"
        white = "Race_White"
        other = "Race_Other"
        a0_1 = "Ages_Less_1"
        a1_4 = "Ages_1_4"
        a5_14 = "Ages_5_14"
        a15_29 = "Ages_15_29"
        a30_44 = "Ages_30_44"
        a45_59 = "Ages_45_59"
        a60_74 = "Ages_60_74"
        a75 = "Ages_75_More"
        sym = "symptom"
        tran1 = "Simple_Transition_1"
        tran2 = "Simple_Transition_2"
        ndigits = 4

        modules = {
            key: generate_synthea_module(symptom_map, value)
            for key, value in condition_map.items()
        }

        key1 = slugify_condition("Abdominal aortic aneurysm")
        key2 = slugify_condition("Appendicitis")

        assert len(modules) == 2

        ##################### Test for condition 1 ############################
        assert key1 in modules
        assert modules[key1][name] == "Abdominal aortic aneurysm"

        assert modules[key1][state][M][dist_dis][0][prob] == prob_val(1.8)
        assert modules[key1][state][F][dist_dis][0][prob] == prob_val(0.4)

        assert modules[key1][state][black][dist_dis][0][prob] == prob_val(0.4)
        assert modules[key1][state][hispa][dist_dis][0][prob] == prob_val(0.6)
        assert modules[key1][state][white][dist_dis][0][prob] == prob_val(1.4)
        assert modules[key1][state][other][dist_dis][0][prob] == prob_val(0.1)

        assert a0_1 not in modules[key1][state]
        assert a1_4 not in modules[key1][state]
        assert a5_14 not in modules[key1][state]
        assert a15_29 not in modules[key1][state]
        assert modules[key1][state][a30_44][dist_dis][0][prob] == prob_val(0.1)
        assert modules[key1][state][a45_59][dist_dis][0][prob] == prob_val(0.4)
        assert modules[key1][state][a60_74][dist_dis][0][prob] == prob_val(2.9)
        assert modules[key1][state][a75][dist_dis][0][prob] == prob_val(5.0)

        assert modules[key1][state]["Symptom_1"][sym] == "Bleeding from ear"
        assert modules[key1][state][tran1][dist_dis][0][prob] == 0.53
        assert modules[key1][state]["Symptom_2"][sym] == "Abdominal distention"
        assert modules[key1][state][tran2][dist_dis][0][prob] == 0.35

        ##################### Test for condition 2 ############################
        assert key2 in modules
        assert modules[key2][name] == "Appendicitis"

        assert modules[key2][state][M][dist_dis][0][prob] == prob_val(1.3)
        assert modules[key2][state][F][dist_dis][0][prob] == prob_val(0.8)

        assert modules[key2][state][black][dist_dis][0][prob] == prob_val(0.4)
        assert modules[key2][state][hispa][dist_dis][0][prob] == prob_val(1.5)
        assert modules[key2][state][white][dist_dis][0][prob] == prob_val(0.0)
        assert modules[key2][state][other][dist_dis][0][prob] == prob_val(1.3)

        assert modules[key2][state][a0_1][dist_dis][0][prob] == prob_val(0.1)
        assert modules[key2][state][a1_4][dist_dis][0][prob] == prob_val(0.3)
        assert modules[key2][state][a5_14][dist_dis][0][prob] == prob_val(2.2)
        assert modules[key2][state][a15_29][dist_dis][0][prob] == prob_val(1.9)
        assert modules[key2][state][a30_44][dist_dis][0][prob] == prob_val(1.0)
        assert modules[key2][state][a45_59][dist_dis][0][prob] == prob_val(0.7)
        assert modules[key2][state][a60_74][dist_dis][0][prob] == prob_val(0.5)
        assert modules[key2][state][a75][dist_dis][0][prob] == prob_val(0.2)

        assert modules[key2][state]["Symptom_1"][sym] == "Abdominal distention"
        assert modules[key2][state][tran1][dist_dis][0][prob] == 0.91
