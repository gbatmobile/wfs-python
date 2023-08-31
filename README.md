# wfs-python

This is a small tool for recovering videos from a WFS0.4/5. WFS is a file system popular in chinese DVRs and we don´t know any tool public available to extract videos from this file system.

This software should be used with care; I and a partner have decoded the filesystem from scratch and, of course, error are problable. In spite, we have succefully tested this implementation in a dozen of images acquired in several contexts. 

We have also implemented a The Sleuth Toolkit (TSK) recover for WFS (see https://github.com/gbatmobile/sleuthkit4.9.0-wfs). It is more complicated to use, but much more flexible.
Anyway, if you just to want export videos using a GUI, this is your tool.

Recently, we've included two new features: extracting video slacks and recovering deleted videos (EXPERIMENTAL!).
Galileu Batista and Unaldo Brito (this guy have made a great work in decoding WFS).
