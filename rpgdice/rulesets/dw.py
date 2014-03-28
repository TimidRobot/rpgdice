#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
import os.path


# Defaults
args = None
batches = dict()
graph_type = None
limits = None
outcomes_label = "Outcomes"
ruleset = os.path.basename(__file__).split(".")[0]
scale_breaks = None
scale_labels = None
srand = None
variables = None
variables_label = None


# Ruleset
title = "Dungeon World"
batches = {0: dict(), 1: dict()}
batches[0]["title"] = "%s - Simplified Results" % title
batches[1]["title"] = "%s - Raw Results" % title
variables = xrange(-3, 4)  # Ability modifier range
variables_label = "Ability Score"
outcomes_label = "Result"
scale_breaks = range(-1, 16)
scale_labels = scale_breaks
batches[0]["scale_breaks"] = [6, 8, 10]
batches[0]["scale_labels"] = ["6 or less", "7-9", "10 or more"]
abilities = {-3: " 1-3 ", -2: " 4-5 ", -1: " 6-8 ", 0: " 9-12", 1: "13-15",
             2: "16-17", 3: "18   "}


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
    for batch in batches:
        outcomes[batch] = dict()
    # simulate rolls
    for roll in xrange(args.rolls):
        results = dict()
        for batch in batches:
            results[batch] = 0
        # Simple 2d6
        pips = srand.randint(1, 6) + srand.randint(1, 6)
        result = pips + ability_mod
        for batch in batches:
            if batch == 0:
                # Constrain results to simplified range
                if result <= 6:
                    results[batch] = 6
                elif result >= 7 and result <= 9:
                    results[batch] = 8
                else:
                    results[batch] = 10
            else:
                results[batch] = result
        # Update outcomes
        for batch in batches:
            result = results[batch]
            if result not in outcomes[batch]:
                outcomes[batch][result] = 1
            else:
                outcomes[batch][result] += 1
    # Organize data
    data = list()
    for batch in batches:
        for result in outcomes[batch]:
            count = outcomes[batch][result]
            percent = round((float(count) / float(args.rolls)) * 100, 1)
            if ability_mod > -1:
                ability_mod_label = "%s  +%s MOD" % (abilities[ability_mod],
                                                     ability_mod)
            else:
                ability_mod_label = "%s  %s MOD" % (abilities[ability_mod],
                                                    ability_mod)
            data.append((batch, ability_mod_label, result, count, percent))
    return sorted(data)
