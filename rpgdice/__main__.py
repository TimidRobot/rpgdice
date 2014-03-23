#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
"""The main entry point. Invoke as `rpgdice' or `python -m rpgdice'.

"""
import sys
from .core import main


if __name__ == '__main__':
    sys.exit(main())
