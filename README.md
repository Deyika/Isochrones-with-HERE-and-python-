# Isochrones-with-HERE-and-python-

The plothere module contains some useful functions for interacting with the HERE isoline routing API. In particular, the plot_isolines module solves some of the difficulties I encountered when plotting these polygons. On their own, these polygons overlap which looks very messy when plotted with opacity onto a basemap. This module 'hollows out' the larger isolines to avoid this. Also adds a scalebar to the map. 
