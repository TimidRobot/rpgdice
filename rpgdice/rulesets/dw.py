#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
import os.path

args = None
graphs = dict()
ruleset = os.path.basename(__file__).split(".")[0]
srand = None

title = "Dungeon World"
xlab = "Outcome (2d6+MOD)"
variables = xrange(-3, 4)  # Ability modifier range
vlab = "Ability Score"
# Graphs
graphs[0] = dict()
graphs[0]["file_suffix"] = "_success"
graphs[0]["graph_type"] = "bars"
graphs[0]["limits"] = (0, 100)
graphs[0]["title"] = "%s\nChance of Any Success" % title
graphs[0]["x_breaks"] = [-4, ] + range(-3, 4)
graphs[0]["x_labels"] = [" ", ] + range(-3, 4)
graphs[0]["xlab"] = "Modifier"
graphs[1] = dict()
graphs[1]["file_suffix"] = "_simplified"
graphs[1]["limits"] = (0, 90)
graphs[1]["title"] = "%s\nSimplified Results" % title
graphs[1]["x_breaks"] = [6, 8, 10]
graphs[1]["x_labels"] = ["6 or less\nFailure", "7 to 9\nPartial Success",
                         "10 or more\nSuccess"]
graphs[2] = dict()
graphs[2]["file_suffix"] = "_raw"
graphs[2]["limits"] = (2, 18)
graphs[2]["x_breaks"] = range(-1, 16)
graphs[2]["x_labels"] = graphs[2]["x_breaks"]
graphs[2]["title"] = "%s\nRaw Results" % title
abilities = {-3: " 1-3 ", -2: " 4-5 ", -1: " 6-8 ", 0: " 9-12", 1: "13-15",
             2: "16-17", 3: "18   "}


def setup(subparser):
    """Set up the sub-command parser"""
    subparser.add_parser(ruleset, help="%s ruleset" % title)


def prepare(parent_args, parent_srand):
    global args, srand
    args = parent_args
    srand = parent_srand


def simulate_rolls(variable):
    ability_mod = variable
    outcomes = dict()
    for gkey in graphs:
        outcomes[gkey] = dict()
    # simulate rolls
    for roll in xrange(args.rolls):
        results = dict()
        for gkey in graphs:
            results[gkey] = 0
        # Simple 2d6
        pips = srand.randint(1, 6) + srand.randint(1, 6)
        for gkey in graphs:
                results[gkey] = pips + ability_mod
        # Update outcomes
        for gkey in graphs:
            result = results[gkey]
            if gkey == 0:
                # Massage data for successes
                if result > 6:
                    result = ability_mod
                else:
                    continue
            elif gkey == 1:
                # Massage data for simplified
                if result <= 6:
                    result = 6
                elif result >= 7 and result <= 9:
                    result = 8
                else:
                    result = 10
            # Update
            if result not in outcomes[gkey]:
                outcomes[gkey][result] = 1
            else:
                outcomes[gkey][result] += 1
    # Organize data
    data = list()
    for gkey in graphs:
        for result in outcomes[gkey]:
            count = outcomes[gkey][result]
            percent = round((float(count) / float(args.rolls)) * 100, 1)
            if ability_mod > -1:
                ability_mod_label = "%s  +%s MOD" % (abilities[ability_mod],
                                                     ability_mod)
            else:
                ability_mod_label = "%s  %s MOD" % (abilities[ability_mod],
                                                    ability_mod)
            data.append((gkey, ability_mod_label, result, count, percent))
            if gkey == 0:
                data.append((gkey, ability_mod_label, result, 0, -1.0))
    return sorted(data)
