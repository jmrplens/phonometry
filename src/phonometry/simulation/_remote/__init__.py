#  Copyright (c) 2026. Jose Manuel Requena Plens
"""How a simulation runs on another machine over SSH (private).

:mod:`.hosts` reads the hosts file, :mod:`.package` gathers the package the
client ships, :mod:`.wire` turns arguments into data, :mod:`.bootstrap` is
the first code a node runs and defines the frames, :mod:`.command` builds the
ssh command line, :mod:`.client` holds the conversation from the client's
side and :mod:`.node` runs the job on the node. Nothing here is imported
until a request names a host.
"""
