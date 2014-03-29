#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
import os.path

args = None
batches = dict()
ruleset = os.path.basename(__file__).split(".")[0]
srand = None

title = "Dungeon World"
batches[0] = dict()
batches[0]["file_suffix"] = "_success"
batches[0]["graph_type"] = "bars"
batches[0]["limits"] = (0, 100)
batches[0]["scale_breaks"] = [-3.75, ] + range(-3, 4) + [3.75, ]
batches[0]["scale_labels"] = [" ", ] + range(-3, 4) + [" ", ]
batches[0]["title"] = "%s\nChance of Success" % title
batches[1] = dict()
batches[1]["file_suffix"] = "_simplified"
batches[1]["limits"] = (0, 90)
batches[1]["scale_breaks"] = [6, 8, 10]
batches[1]["scale_labels"] = ["6 or less", "7-9", "10 or more"]
batches[1]["title"] = "%s\nSimplified Results" % title
batches[2] = dict()
batches[2]["file_suffix"] = "_raw"
batches[2]["limits"] = (2, 18)
batches[2]["scale_breaks"] = range(-1, 16)
batches[2]["scale_labels"] = batches[2]["scale_breaks"]
batches[2]["title"] = "%s\nRaw Results" % title
abilities = {-3: " 1-3 ", -2: " 4-5 ", -1: " 6-8 ", 0: " 9-12", 1: "13-15",
             2: "16-17", 3: "18   "}
outcomes_label = "Result"
variables = xrange(-3, 4)  # Ability modifier range
variables_label = "Ability Score"


def setup(subparser):
    """Set up the sub-command parser"""
    subcommand = subparser.add_parser(ruleset, help="%s ruleset" % title)


def prepare(parent_args, parent_srand):
    global args, srand
    args = parent_args
    srand = parent_srand


def simulate_rolls(variable):
    ability_mod = variable
    outcomes = dict()
    for i in batches:
        outcomes[i] = dict()
    # simulate rolls
    for roll in xrange(args.rolls):
        results = dict()
        for i in batches:
            results[i] = 0
        # Simple 2d6
        pips = srand.randint(1, 6) + srand.randint(1, 6)
        for i in batches:
                results[i] = pips + ability_mod
        # Update outcomes
        for i in batches:
            result = results[i]
            if i == 0:
                # Massage data for successes
                if result > 6:
                    result = ability_mod
                else:
                    continue
            elif i == 1:
                # Massage data for simplified
                if result <= 6:
                    result = 6
                elif result >= 7 and result <= 9:
                    result = 8
                else:
                    result = 10
            # Update
            if result not in outcomes[i]:
                outcomes[i][result] = 1
            else:
                outcomes[i][result] += 1
    # Organize data
    data = list()
    for i in batches:
        for result in outcomes[i]:
            count = outcomes[i][result]
            percent = round((float(count) / float(args.rolls)) * 100, 1)
            if ability_mod > -1:
                ability_mod_label = "%s  +%s MOD" % (abilities[ability_mod],
                                                     ability_mod)
            else:
                ability_mod_label = "%s  %s MOD" % (abilities[ability_mod],
                                                    ability_mod)
            data.append((i, ability_mod_label, result, count, percent))
            if i == 0:
                data.append((i, ability_mod_label, result, 0, -1.0))
    return sorted(data)
