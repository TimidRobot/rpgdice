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
    argparser.add_argument("--dumpsave", action="store_true")
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
    pool = multiprocessing.Pool()
    try:
        for result in pool.map(rulemod.simulate_rolls, rulemod.variables):
            results.extend(result)
        pool.close()
        pool.join()
    except KeyboardInterrupt:
        sys.exit(130)

    if args.debug:
        print "DEBUG: results:"
        pprint(results)
        print

    columns = ("Batch", rulemod.variables_label, rulemod.x_label, "Count",
               "Percent")
    data = pandas.DataFrame.from_records(results, columns=columns)

    for batch in rulemod.batches:
        # graph data
        graph_data = data[data["Batch"] == batch]
        graph_data.index = range(1, len(graph_data) + 1)
        if args.debug:
            print "DEBUG: graph_data:"
            pprint(graph_data)
            print
        # colors
        colors_lower = ["#ff0000", "#cc0000", "#993300", "#666600"]
        colors_upper = ["#006666", "#003399", "#0000cc", "#0000ff"]
        colors_mid = ["#000000", ]
        color_count = len(rulemod.variables) - 1
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
        # graph
        graph = dict()
        batch_items = ("graph_type", "scale_breaks", "scale_labels", "title",
                       "variables_label")
        for item in batch_items:
            if item in rulemod.batches[batch]:
                 graph[item] = rulemod.batches[batch][item]
            else:
                 graph[item] = getattr(rulemod, item)
        if args.debug:
            print "DEBUG: graph:"
            pprint(graph)
            print
        if args.graph:
            plot = (ggplot.ggplot(ggplot.aes(x=rulemod.x_label, y="Percent",
                                             color=graph["variables_label"]),
                                  data=graph_data) +
                    ggplot.ggtitle(graph["title"]) +
                    ggplot.scale_x_discrete(breaks=graph["scale_breaks"],
                                            labels=graph["scale_labels"]) +
                    ggplot.theme_seaborn() +
                    ggplot.scale_colour_manual(values=color_list)
                    )
            if graph["graph_type"] == "bars":
                plot += ggplot.geom_line(size=20)
#                plot += ggplot.geom_point(size=80)
                plot += ggplot.scale_y_continuous(limits=(20,100))
            else:
                plot += ggplot.geom_line()
                plot += ggplot.geom_point(alpha=0.3, size=50)
            plot.rcParams["font.family"] = "monospace"
            if args.dumpsave:
                filename = "/dev/null"
            else:
                filename = "%s_%s.png" % (args.ruleset, batch)
            ggplot.ggsave(filename, plot, format="png", dpi=75)

    return 0
