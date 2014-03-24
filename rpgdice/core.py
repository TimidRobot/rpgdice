#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Standard library
import argparse
import multiprocessing
from pprint import pprint
import random
import sys
# Third-party
import ggplot
import pandas
# RPG Dice
from .rulesets import crypto
from .rulesets import dw


args = None
rulemod = None
srand = random.SystemRandom()


def register_rules(subparser):
    for mod in sys.modules:
        parts = mod.split(".")
        if len(parts) == 3 and parts[1] == "rulesets":
            try:
                sys.modules[mod].setup(subparser)
            except:
                pass


def parser_setup():
    """Instantiate, configure and return an ArgumentParser instance."""

    def deformat_int(string):
        """Remove commas from a string and return int"""
        return int(string.replace(",", ""))

    # Top level argument parser
    argparser = argparse.ArgumentParser(description=__doc__)
    argparser.add_argument("-r", "--rolls", default="10,000",
                           type=deformat_int, help="Number of rolls to "
                           "simulate per dice combination (default: "
                           "%(default)s)")
    argparser.add_argument("-d", "--debug", action="store_true")
    argparser.add_argument("--nograph", action="store_false", dest="graph")
    # Sub-parser for modules to register themselves
    subparser = argparser.add_subparsers(title='Subcommands',
                                         dest='ruleset')
    return (argparser, subparser)


def main():
    global args, ruleset
    # Arguments Parser
    argparser, subparser = parser_setup()
    register_rules(subparser)
    args = argparser.parse_args()
    rulemod = sys.modules["rpgdice.rulesets.%s" % args.ruleset]
    rulemod.prepare(args, srand)

    if args.debug:
        print "DEBUG: args", args
        print

    results = list()
    pool = multiprocessing.Pool(1)
    try:
        for result in pool.map(rulemod.simulate_rolls, rulemod.skills):
            results.extend(result)
        pool.close()
        pool.join()
    except KeyboardInterrupt:
        sys.exit(130)

    if args.debug:
        print "DEBUG: results:"
        pprint(results)
        print

    columns = ("Difficulty", rulemod.skills_label, rulemod.result_label,
               "Count", "Percent")
    data = pandas.DataFrame.from_records(results, columns=columns)

    for diff in rulemod.difficulties:

        graph_data = data[data["Difficulty"] == diff]
        graph_data.index = range(1, len(graph_data) + 1)
        if args.debug:
            print "DEBUG: graph_data:"
            pprint(graph_data)
            print

        colors_lower = ["#ff0000", "#cc0000", "#993300", "#666600"]
        colors_upper = ["#006666", "#003399", "#0000cc", "#0000ff"]
        colors_mid = ["#000000", ]
        color_count = len(rulemod.skills) - 1
        if color_count % 2 == 0:
            lower_slice = (color_count / 2) * -1
            upper_slice = color_count / 2
        else:
            lower_slice = ((color_count - 1) / 2) * -1
            upper_slice = (color_count + 1) / 2
        color_list = (colors_lower[lower_slice:] + colors_mid +
                      colors_upper[0:upper_slice])
        if args.debug:
            print "DEBUG: lower_slice:", lower_slice
            print "DEBUG: upper_slice:", upper_slice
            print "DEBUG: color_list"
            pprint(color_list)
            print
        if args.graph:
            plot = (ggplot.ggplot(ggplot.aes(x=rulemod.result_label,
                                             y="Percent",
                                             color=rulemod.skills_label),
                                  data=graph_data) +
                    ggplot.ggtitle(rulemod.titles[diff]) +
                    ggplot.scale_x_discrete(breaks=rulemod.scale_breaks,
                                            labels=rulemod.scale_labels) +
                    ggplot.theme_seaborn() +
                    ggplot.scale_colour_manual(values=color_list) +
                    ggplot.geom_line() +
                    ggplot.geom_point(alpha=0.3, size=50)
                    )
            ggplot.ggsave("%s_%s.png" % (args.ruleset, diff), plot, dpi=75)

    return 0
