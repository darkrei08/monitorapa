#!/usr/bin/env -S python3 -u

# This file is part of MonitoraPA
#
# Copyright (C) 2022 Marco Marinello <contact+nohuman@marinello.bz.it>
#
# MonitoraPA is a hack. You can use it according to the terms and
# conditions of the Hacking License (see LICENSE.txt)

from pathlib import Path
from datetime import datetime
import re

FEED_HEADER = f"""
<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">

  <title>MonitoraPA</title>
  <link href="https://foia.monitora-pa.it/ "/>
  <link type="application/atom+xml" rel="self" href="https://www.monitora-pa.it/atom.xml"/>
  <updated>{datetime.now().isoformat()}</updated>
  <id>http://www.monitora-pa.it/</id>
  <author>
    <name>Giacomo Tesio</name>
    <email>giacomo@tesio.it</email>
    <uri>http://www.tesio.it/</uri>
  </author>
  """


class AtomEntry:
    def __init__(self, directory):
        cwd = Path(Path(".").absolute())
        self.directory = directory
        self.text = f"In data {directory.name} sono stati inviati dalla scuola {directory.parent.name} (provincia di "
        self.text += f"{directory.parent.parent.name.title()}) i seguenti file:"
        self.text += "\n<ul>"
        for attachment in [a for a in directory.glob("*") if a.is_file()]:
            self.text += f"\n<li><a href='https://foia.monitorapa.it/{attachment.relative_to(cwd)}'>"
            self.text += "</li>"
        self.text += "</ul>"

    def export(self):
        return f"<entry><content type=\"html\"><p>{self.text}</p></content></entry>\n"


class AtomFeedElement:
    def __init__(self, path):
        self.root = path
        self.entries = []

    def build(self):
        print("building for", self.root)
        dirs = [a for a in self.root.glob("*") if a.is_dir()]
        if all([re.match("\d\d\d\d-\d\d-\d\d", a.name) for a in dirs]):
            for d in dirs:
                self.entries.append(AtomEntry(d))
            self.write_feed()
            return
        for d in dirs:
            _d = AtomFeedElement(d)
            _d.build()
            self.entries.append(_d)
        self.write_feed()

    def get_entries(self):
        e = [k for k in self.entries if type(k) == AtomEntry]
        for i in [k for k in self.entries if type(k) == AtomFeedElement]:
            e += i.get_entries()
        return sorted(e, key=lambda y: y.directory.name, reverse=True)

    def write_feed(self):
        print("write atom in", self.root / "atom.xml")
        with open(self.root / "atom.xml", "w") as hd:
            hd.write(self.gen_atom())

    def gen_atom(self):
        feed = f"{FEED_HEADER}"
        for e in self.get_entries():
            feed += e.export()
        feed += "</feed>\n"
        return feed


if __name__ == "__main__":
    cwd = Path(Path(".").absolute())
    AtomFeedElement(cwd).build()
