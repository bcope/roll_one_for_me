#!/usr/bin/env python3
import random
import re
import string

import logging

from classes.tables.table_entry import TableItem
from classes.tables.table_outcome import TableRoll

_trash = string.punctuation + string.whitespace
_header_regex = "^(\d+)?[dD](\d+)(.*)"
_line_regex = "^(\d+)(\s*-+\s*\d+)?(.*)"


class Table:
    """Container for a single set of TableItem objects
    A single post will likely contain many Table objects"""

    def __init__(self, roll, header, *outcomes):
        self.roll = roll
        self.header = header
        self.outcomes = outcomes

    def __repr__(self):
        return "<Table with header: {}>".format(self.text.split('\n')[0])

    def _parse(self):
        lines = self.text.split('\n')
        head = lines.pop(0)
        head_match = re.search(_header_regex, head.strip(_trash))
        if head_match:
            self.roll = int(head_match.group(2))
            self.header = head_match.group(3)
        self.outcomes = [TableItem(l) for l in lines if re.search(_line_regex, l.strip(_trash))]

    def roll(self):
        try:
            weights = [i.weight for i in self.outcomes]
            total_weight = sum(weights)
            #            if debug:
            #                lprint("Weights ; Outcome")
            #                pprint(list(zip(self.weights, self.outcomes)))
            if self.roll != total_weight:
                self.header = "[Table roll error: parsed die did not match sum of item wieghts.]  \n" + self.header
            # stops = [ sum(weights[:i+1]) for i in range(len(weights))]
            c = random.randint(1, self.roll)
            scan = c
            ind = -1
            while scan > 0:
                ind += 1
                scan -= weights[ind]

            R = TableRoll(d=self.roll,
                          rolled=c,
                          head=self.header,
                          out=self.outcomes[ind])
            if len(self.outcomes) != self.roll:
                R.error("Expected {} items found {}".format(self.roll, len(self.outcomes)))
            return R
        # TODO: Handle errors more gracefully.
        except Exception as e:
            logging.error("Exception in Table roll ({}): {}".format(self, e))
            return None

    """FEATURES IN SCRAPS: This is essentially-exactly a lookup-table"""

    def __init__(self):
        self.items = []
        pass

    def __hash__(self):
        return hash(tuple(self.items))

    def __len__(self):
        return len(self.items)

    def __getitem__(self, value):
        """Assume a 1-index on value passed to a table."""
        assert 0 < value <= len(self.items), "Out of bounds error"
        return self.items[value - 1]

    def add_item(self, item, weight=1):
        self.items.extend([item] * weight)


class ReflexiveTable(Table):
    def __getitem__(self, value):
        return str(value)


class InlineTable(Table):
    '''A Table object whose text is parsed in one line, instead of expecting line breaks'''

    def __init__(self, text):
        super().__init__(text)
        self.is_inline = True

    def __repr__(self):
        return "<d{} Inline table>".format(self.die)

    def _parse(self):
        top = re.search("[dD](\d+)(.*)", self.text)
        if not top:
            return

        self.die = int(top.group(1))
        tail = top.group(2)
        # sub_outs = []
        while tail:
            in_match = re.search(_line_regex, tail.strip(_trash))
            if not in_match:
                logging.debug("Could not complete parsing InlineTable; in_match did not catch.")
                logging.debug("Returning blank roll area.")
                self.outcomes = [TableItem("1-{}. N/A".format(self.die))]
                return
            this_out = in_match.group(3)
            next_match = re.search(_line_regex[1:], this_out)
            if next_match:
                tail = this_out[next_match.start():]
                this_out = this_out[:next_match.start()]
            else:
                tail = ""

            TI_text = in_match.group(1) + (in_match.group(2) if in_match.group(2) else "") + this_out
            try:
                self.outcomes.append(TableItem(TI_text))
            except Exception as _:
                logging.exception("Error building TableItem in inline table; item skipped.")
