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
                                         dest="ruleset", metavar="RULESET")
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

    conf = dict()
    conf = {"vlab": "Variables", "xlab": "Outcome", "ylab": "Probability %"}
    for item in conf:
        try:
            conf[item] = getattr(rulemod, item)
        except:
            pass

    columns = ("Graph", conf["vlab"], conf["xlab"], "Count", conf["ylab"])
    data = pandas.DataFrame.from_records(results, columns=columns)
    for gkey in rulemod.graphs:
        # Graph Defaults
        graph_conf = conf.copy()
        graph_conf["file_suffix"] = str()
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
        graph_conf["color_list"] = (colors_lower[lower_slice:] + colors_mid +
                                    colors_upper[0:upper_slice])

        # graph_conf from graph
        graph_items = ("color_list", "file_suffix", "graph_type", "limits",
                       "x_breaks", "x_labels", "title", "vlab", "xlab", "ylab")
        for item in graph_items:
            try:
                graph_conf[item] = rulemod.graphs[gkey][item]
            except:
                try:
                    graph_conf[item] = getattr(rulemod, item)
                except:
                    if item not in graph_conf:
                        graph_conf[item] = None
        if args.debug:
            print "DEBUG: graph_conf:"
            pprint(graph_conf)
            print

        # plot_data
        plot_data = data.copy()
        plot_data = plot_data[plot_data["Graph"] == gkey]
        plot_data.rename(columns={conf["vlab"]: graph_conf["vlab"],
                                  conf["xlab"]: graph_conf["xlab"],
                                  conf["ylab"]: graph_conf["ylab"]},
                         inplace=True)
        plot_data.index = range(1, len(plot_data) + 1)
        if args.debug:
            print "DEBUG: plot_data:"
            pprint(plot_data)
            print

        # Create plot
        if args.graph:
            plot = (ggplot.ggplot(ggplot.aes(x=graph_conf["xlab"],
                                             y=graph_conf["ylab"],
                                             color=graph_conf["vlab"]),
                                  data=plot_data) +
                    ggplot.scale_x_discrete(breaks=graph_conf["x_breaks"],
                                            labels=graph_conf["x_labels"]) +
                    ggplot.ggtitle(graph_conf["title"]) +
                    ggplot.theme_gray() +
                    ggplot.scale_colour_manual(values=graph_conf["color_list"])
                    )
            plot.rcParams["font.family"] = "monospace"
            if graph_conf["limits"]:
                plot += ggplot.ylim(graph_conf["limits"][0],
                                    graph_conf["limits"][1])
            if graph_conf["graph_type"] == "bars":
                plot += ggplot.geom_line(size=20)
                text_data = plot_data[plot_data["Count"] > 0]
                text_data.index = range(0, len(text_data))
                outcomes = dict(text_data[graph_conf["xlab"]])
                percents = dict(text_data[graph_conf["ylab"]])
                for k in outcomes:
                    percent = "%4.1f%%" % percents[k]
                    x = outcomes[k]
                    y = percents[k] + 4
                    color = graph_conf["color_list"][k]
                    plot += ggplot.geom_text(label=[percent, ], x=[x, x + 1],
                                             y=[y, y - 1], color=color)
            else:
                plot += ggplot.geom_line()
                plot += ggplot.geom_point(alpha=0.3, size=50)
            if hasattr(rulemod, "update_plot"):
                plot = rulemod.update_plot(gkey, graph_conf, plot)
            if args.dumpsave:
                filename = "/dev/null"
            else:
                filename = "%s%02d%s.png" % (args.ruleset, gkey,
                                             graph_conf["file_suffix"])
            ggplot.ggsave(filename, plot, format="png", dpi=300)

    return 0
