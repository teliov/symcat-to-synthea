import csv
import hashlib
import re

symcat_symptom_url_regex = re.compile(r"http://www.symcat.com/symptoms/(.*)")
symcat_condition_url_regex = re.compile(r"http://www.symcat.com/conditions/(.*)")
symcat_age_url_regex = re.compile(r"http://www.symcat.com/demographics/age-(.*)")
symcat_sex_url_regex = re.compile(r"http://www.symcat.com/demographics/sex-(.*)")
symcat_race_url_regex = re.compile(r"http://www.symcat.com/demographics/race-ethnicity-(.*)")


def parse_symcat_symptoms(filename):
    # let's start with the easy one first. Symcat has these 474 symptoms.
    # let's get a unique id symptom_name, symptom_description for all of them

    symptom_map = {}
    # the csv file is structured a bit weirdly. There are 105 columns,
    # but every 21 columns is repeated but with different column name
    # so when checking for the symptom name for instance, you would need to check all 5 different column group
    # for a match before concluding that the target is indeed missing.
    content_offsets = [0, 21, 42, 63, 84]
    with open(filename, newline='') as fp:
        symptom_reader = csv.reader(fp)
        idx = 0
        for row in symptom_reader:
            if idx == 0:
                pass
            else:
                curr_offset = None
                symptom_name = None
                for jdx in content_offsets:
                    symptom_name = row[jdx].strip()
                    if len(symptom_name) == 0:
                        continue
                    else:
                        curr_offset = jdx
                        break
                if curr_offset is None:
                    continue

                symptom_url = row[curr_offset + 1]
                match = symcat_symptom_url_regex.match(symptom_url)
                if match is None:
                    continue
                symptom_slug = match.groups()[0].strip()
                if symptom_slug not in symptom_map:
                    # we've not seen this symptom already
                    # generate a hash based off this
                    symptom_hash = hashlib.sha224(symptom_slug.encode("UTF-8")).hexdigest()

                    # get the description for this symptom.
                    symptom_description = row[curr_offset + 3]

                    symptom_map[symptom_slug] = {
                        'name': symptom_name,
                        'hash': symptom_hash,
                        'description': symptom_description
                    }
            idx = idx + 1

    return symptom_map


def slugify_condition(condition_name):
    condition_name = condition_name.lower()
    condition_name = re.sub(r"\s+", "-", condition_name)
    condition_name = re.sub(r"'", "-", condition_name)
    condition_name = re.sub(r"\(", "", condition_name)
    condition_name = re.sub(r"\)", "", condition_name)
    return condition_name


def is_valid_symptom(row):
    symptom_offsets = [0, 25, 50, 75, 100, 125, 150]
    is_valid = False
    symptom = {}
    for idx in symptom_offsets:
        condition_name = row[idx].strip()
        if condition_name == "":
            continue
        condition_url = row[idx + 1].strip()
        if condition_url == "":
            continue
        match = symcat_condition_url_regex.match(condition_url)
        if match is None:
            continue
        condition_slug = match.groups()[0]

        # if the condition ends with --2,
        # then it's probably to avoid conflict with a symptom that also has the same name
        if condition_slug[-3:] == "--2":
            condition_slug = condition_slug[:-3]

        condition_description = row[idx + 3].strip()
        condition_symptom_summary = row[idx + 4].strip()

        # some conditions have two columns for the condition symptom summary.
        # this would offset the symptom definition by a bit, so we test
        symptom_url_offsets = [6, 7]
        condition_symptom_slug = None
        condition_symptom_offset = None
        for jdx in symptom_url_offsets:
            url = row[idx + jdx].strip()
            if url == "":
                continue

            match = symcat_symptom_url_regex.match(url)
            if match is None:
                continue

            condition_symptom_slug = match.groups()[0].strip()
            condition_symptom_offset = jdx
            break

        if condition_symptom_offset is None:
            continue

        # if it's the second offset then we re-assign the symptom description
        if condition_symptom_offset == 7:
            condition_description = row[idx + 4].strip()
            condition_symptom_summary = row[idx + 5].strip()

        condition_symptom_prob = row[idx + condition_symptom_offset + 1].strip()
        condition_symptom = row[idx + condition_symptom_offset - 1].strip()

        if condition_symptom == "":
            continue

        try:
            condition_symptom_prob = int(condition_symptom_prob)
        except ValueError:
            continue  # invalid probability value

        # if we get here then all is good
        is_valid = True
        symptom = {
            "condition_name": condition_name,
            "condition_slug": condition_slug,
            "condition_description": condition_description,
            "condition_remarks": condition_symptom_summary,
            "symptom_name": condition_symptom,
            "symptom_slug": condition_symptom_slug,
            "symptom_probability": condition_symptom_prob
        }
        break

    return is_valid, symptom


def is_valid_demographics(demo_type, row):
    offset_dict = {
        "age": [10, 35, 61, 86, 110, 135, 160],
        "sex": [14, 39, 65, 90, 114, 139, 164],
        "race": [18, 43, 69, 94, 118, 143, 168],
    }

    offsets = offset_dict.get(demo_type, None)
    if offsets is None:
        raise Exception("Invalid demography type")

    regex_selector = {
        "age": symcat_age_url_regex,
        "sex": symcat_sex_url_regex,
        "race": symcat_race_url_regex
    }

    slug_prefix = {
        "age": "age-",
        "sex": "sex-",
        "race": "race-ethnicity-"
    }

    is_valid = False
    data = {}

    for idx in offsets:
        grp_name = row[idx].strip()
        if grp_name == "":
            continue
        grp_url = row[idx + 1].strip()
        if grp_url == "":
            continue

        regex = regex_selector.get(demo_type)
        match = regex.match(grp_url)
        if match is None:
            continue
        grp_slug = match.groups()[0].strip()

        odds = row[idx + 2].strip().split("x")[0]
        if odds == "":
            continue
        try:
            odds = float(odds)
        except ValueError:
            continue
        condition_name = row[idx + 3].strip()
        if condition_name == "":
            continue
        # if we get here then surely this is a valid age definition
        is_valid = True
        data = {
            "condition_name": condition_name,
            "condition_slug": slugify_condition(condition_name),
            "grp_name": grp_name,
            "grp_slug": slug_prefix.get(demo_type) + grp_slug,
            "grp_odds": odds
        }
        break

    return is_valid, data


def parse_symcat_conditions(filename):
    # working on the symcat conditions now ..,
    # let's get the conditions
    condition_map = {}

    # similar weird construct of the csv files
    with open(filename, newline='') as fp:
        symptom_reader = csv.reader(fp)
        idx = 0
        for row in symptom_reader:
            if idx == 0:
                pass
            else:
                # check if it's a valid symptom definition
                is_symptom, symptom_data = is_valid_symptom(row)
                if is_symptom:
                    condition_slug = symptom_data.get("condition_slug")
                    if condition_slug not in condition_map:
                        condition_map[condition_slug] = {
                            "condition_name": symptom_data.get("condition_name"),
                            "condition_slug": symptom_data.get("condition_slug"),
                            "condition_description": symptom_data.get("condition_description"),
                            "condition_remarks": symptom_data.get("condition_remarks"),
                            "symptoms": {},
                            "age": {},
                            "race": {},
                            "sex": {}
                        }

                    if condition_map[condition_slug].get("condition_description", None) is None:
                        condition_map[condition_slug]["condition_description"] = symptom_data.get(
                            "condition_description")

                    if condition_map[condition_slug].get("condition_remarks", None) is None:
                        condition_map[condition_slug]["condition_remarks"] = symptom_data.get("condition_remarks")

                    # have we not recorded this symptom already ? then:
                    symptom_slug = symptom_data.get("symptom_slug")
                    if symptom_slug not in condition_map[condition_slug]["symptoms"]:
                        condition_map[condition_slug]["symptoms"][symptom_slug] = {
                            "slug": symptom_slug,
                            "probability": symptom_data.get("symptom_probability")
                        }
                else:
                    demo_types = ["age", "sex", "race"]
                    for demo_type in demo_types:
                        is_valid, demo_data = is_valid_demographics(demo_type, row)
                        if is_valid:
                            condition_slug = demo_data.get("condition_slug")
                            if condition_slug not in condition_map:
                                condition_map[condition_slug] = {
                                    "condition_name": demo_data.get("condition_name"),
                                    "condition_slug": demo_data.get("condition_slug"),
                                    "condition_description": None,
                                    "condition_remarks": None,
                                    "symptoms": {},
                                    "age": {},
                                    "race": {},
                                    "sex": {}
                                }

                            grp_slug = demo_data.get("grp_slug")
                            if grp_slug not in condition_map[condition_slug][demo_type]:
                                condition_map[condition_slug][demo_type][grp_slug] = {
                                    "name": demo_data.get("grp_name"),
                                    "slug": grp_slug,
                                    "odds": demo_data.get("grp_odds")
                                }
                            break
            idx = idx + 1

    return condition_map
