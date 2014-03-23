#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
import os.path

args = None
srand = None
ruleset = os.path.basename(__file__).split(".")[0]

difficulties = (1, )
title = "Dungeon World"
titles = {1: title}
abilities = {-3: " 1-3", -2: " 4-5", -1: " 6-8", 0: " 9-12", 1: "13-15",
             2: "16-17", 3: "18"}
modifier_range = xrange(-3, 4)
skills = modifier_range
skills_label = "Ability Score"
result_label = "Result"
scale_breaks = [6, 9, 10, 11, 12]
scale_labels = ["6 or less", "7-9", "10", "11", "12 or more"]


def setup(subparser):
    """Set up the sub-command parser"""
    subcommand = subparser.add_parser(ruleset, help="%s ruleset" % title)


def prepare(parent_args, parent_srand):
    global args, srand
    args = parent_args
    srand = parent_srand


def simulate_rolls(ability_mod):
    outcomes = dict()
    # simulate rolls
    for roll in xrange(args.rolls):
        # Simple 2d6
        roll = srand.randint(1, 6) + srand.randint(1, 6)
        result = roll + ability_mod
         # Constrain results within meaningful range
        if result <= 6:
            result = 6
        elif result >= 7 and result <= 9:
            result = 9
        elif result > 12:
            result = 12
        # Update outcomes
        if result not in outcomes:
            outcomes[result] = 1
        else:
            outcomes[result] += 1
    # Organize data
    data = list()
    for result in outcomes:
        count = outcomes[result]
        percent = round((float(count) / float(args.rolls)) * 100, 1)
        if ability_mod > -1:
            ability_mod_label = "%s. MOD+%s" % (ability_mod + 4, ability_mod)
            ability_mod_label = "%s (2d6+%s)" % (abilities[ability_mod],
                                                 ability_mod)
        else:
            ability_mod_label = "%s. MOD%s" % (ability_mod + 4, ability_mod)
            ability_mod_label = "%s (2d6%s)" % (abilities[ability_mod],
                                                ability_mod)
        data.append((1, ability_mod_label, result, count, percent))
    return sorted(data)
