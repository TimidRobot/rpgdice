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
from .rulesets import dw
from .rulesets import sweote

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
    subparser = argparser.add_subparsers(title="Ruleset subcommands:",
                                         dest="ruleset", metavar="RULESET" )
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

    columns = ("Batch", rulemod.variables_label, rulemod.outcomes_label,
               "Count", "Percent")
    data = pandas.DataFrame.from_records(results, columns=columns)
    for i in rulemod.batches:
        batch = rulemod.batches[i]

        # plot_data
        plot_data = data[data["Batch"] == i]
        plot_data.index = range(1, len(plot_data) + 1)
        if args.debug:
            print "DEBUG: plot_data:"
            pprint(plot_data)
            print

        # Graph Defaults
        conf = dict()
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
        conf["color_list"] = (colors_lower[lower_slice:] + colors_mid +
                               colors_upper[0:upper_slice])

        # conf from batch
        batch_items = ("color_list", "graph_type", "limits", "scale_breaks",
                       "scale_labels", "title", "variables_label")
        for item in batch_items:
            try:
                conf[item] = batch[item]
            except:
                try:
                    conf[item] = getattr(rulemod, item)
                except:
                    if item not in conf:
                        conf[item] = None
        if args.debug:
            print "DEBUG: conf:"
            pprint(conf)
            print

        # Create plot
        if args.graph:
            plot = (ggplot.ggplot(ggplot.aes(x=rulemod.outcomes_label,
                                             y="Percent",
                                             color=conf["variables_label"]),
                                  data=plot_data) +
                    ggplot.ggtitle(conf["title"]) +
                    ggplot.scale_x_discrete(breaks=conf["scale_breaks"],
                                            labels=conf["scale_labels"]) +
                    ggplot.theme_gray() +
                    ggplot.scale_colour_manual(values=conf["color_list"])
                    )
            plot.rcParams["font.family"] = "monospace"
            if conf["limits"]:
                plot += ggplot.ylim(conf["limits"][0], conf["limits"][1])
            if conf["graph_type"] == "bars":
                plot += ggplot.geom_line(size=20)
                text_data = plot_data[plot_data["Count"] > 0]
                text_data.index = range(0, len(text_data))
                outcomes = dict(text_data[rulemod.outcomes_label])
                percents = dict(text_data["Percent"])
                for k in outcomes:
                    percent = "%4.1f%%" % percents[k]
                    x = outcomes[k]
                    y = percents[k] + 4
                    color = conf["color_list"][k]
                    plot += ggplot.geom_text(label=[percent, ], x=[x, x + 1],
                         y=[y, y - 1], color=color)
            else:
                plot += ggplot.geom_line()
                plot += ggplot.geom_point(alpha=0.3, size=50)
            if hasattr(rulemod, "update_plot"):
                plot = rulemod.update_plot(i, batch, conf, plot)
            if args.dumpsave:
                filename = "/dev/null"
            else:
                suffix = str()
                if "file_suffix" in batch:
                    suffix = batch["file_suffix"]
                filename = "%s%02d%s.png" % (args.ruleset, i, suffix)
            ggplot.ggsave(filename, plot, format="png", dpi=300)

    return 0
