from collections import OrderedDict

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


def generate_transition_for_history_attribute(attribute_name, next_state):
    """Function for defining age-based transitions in the generated PGM module
    Parameters
    ----------
    attribute_name : str
        The name of the attribute for testing purposes.
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
    transitions = []
    adjacent_states = {}
    for idx, key in enumerate(AttrKeys.TIME_KEYS):
        if key == "age-1-years":
            next_node_name = "End_Time_LessOrEqual_1"
            curr_transition = {
                "condition": {
                    "condition_type": "Attribute",
                    "attribute": attribute_name,
                    "operator": "<=",
                    "value": 1
                },
                "transition": next_node_name
            }
            state = {
                "type": "Delay",
                "exact": {
                    "quantity": 1,
                    "unit": "months"
                },
                "direct_transition": next_state
            }
        elif key == "age-75-years":
            next_node_name = "End_Time_Greater_75"
            curr_transition = {
                "condition": {
                    "condition_type": "Attribute",
                    "attribute": attribute_name,
                    "operator": ">",
                    "value": 75
                },
                "transition": next_node_name
            }
            state = {
                "type": "Delay",
                "exact": {
                    "quantity": 75,
                    "unit": "years"
                },
                "direct_transition": next_state
            }
        else:
            parts = key.split("-")
            age_lower = parts[1]
            age_upper = parts[2]
            next_node_name = "End_Time_{}_{}".format(age_lower, age_upper)
            curr_transition = {
                "condition": {
                    "condition_type": "And",
                    "conditions": [
                        {
                            "condition_type": "Attribute",
                            "attribute": attribute_name,
                            "operator": ">",
                            "value": int(age_lower)
                        },
                        {
                            "condition_type": "Attribute",
                            "attribute": attribute_name,
                            "operator": "<=",
                            "value": int(age_upper)
                        }
                    ],
                },
                "transition": next_node_name
            }
            state = {
                "type": "Delay",
                "exact": {
                    "quantity": int(age_lower),
                    "unit": "years"
                },
                "direct_transition": next_state
            }
        transitions.append(curr_transition)
        adjacent_states[next_node_name] = state

    return transitions, adjacent_states


def generate_synthea_common_history_module(num_history_years=1):
    """Function for generating the PGM module which aims at setting the attribute
    `age_time_to_the_end` for a given person as a function of his current_age and target_age
    that is: `age_time_to_the_end = target_age - current_age`.

    Parameters
    ----------
    num_history_years: int
        given the target age of a patient, this is the number of years from
        that target year from which pathologoes are generated.
        (default: 1)

    Returns
    -------
    dict
        A ddictionnary describing the PGM of the correspondinf module.
    """
    history_age_attribute = "age_time_to_the_end"

    states = OrderedDict()

    # add the initial onset
    states["Initial"] = {
        "type": "Initial",
        "direct_transition": "History_Age_Attribute"
    }

    # set attrbute based on target age
    states["History_Age_Attribute"] = {
        "type": "SetAttribute",
        "attribute": history_age_attribute,
        "expression": "#{target_age} - #{age} - " + str(num_history_years)
    }

    # time states
    time_conditional_transition, time_states = generate_transition_for_history_attribute(
        history_age_attribute, "Check_Exit"
    )
    states["History_Age_Attribute"][
        "conditional_transition"] = time_conditional_transition
    states.update(time_states)

    # check if the time history is verified
    states["Check_Exit"] = {
        "type": "Simple",
        "conditional_transition": [
            {
                "condition": {
                    "condition_type": "False",
                },
                "transition": "TerminalState"
            },
            {
                "transition": "History_Age_Attribute"
            }
        ]
    }

    states["TerminalState"] = {
        "type": "Terminal"
    }

    return {
        "name": "update_age_time_to_the_end",
        "states": states
    }


def get_transition_to_no_infection():
    return {
        "type": "Simple",
        "direct_transition": TransitionStates.NO_INFECTION
    }


class AttrKeys:
    AGE_KEYS = [
            "age-1-years", "age-1-4-years", "age-5-14-years", "age-15-29-years",
            "age-30-44-years", "age-45-59-years", "age-60-74-years", "age-75-years"
    ]
    RACE_KEYS = [
            "race-ethnicity-black", "race-ethnicity-hispanic",
            "race-ethnicity-white", "race-ethnicity-other"
    ]
    RACE_PRIOR_KEYS = [
            "race-ethnicity-black", "race-ethnicity-hispanic",
            "race-ethnicity-white", "race-ethnicity-other",
            "race-ethnicity-asian", "race-ethnicity-native",
    ]
    SEX_KEYS = ["sex-male", "sex-female"]
    TIME_KEYS = [
            "age-1-years", "age-1-5-years", "age-5-15-years", "age-15-30-years",
            "age-30-45-years", "age-45-60-years", "age-60-75-years", "age-75-years"
    ]


class TransitionStates:
    TERMINAL_STATE = "TerminalState"
    NO_INFECTION = "No_Infection"
