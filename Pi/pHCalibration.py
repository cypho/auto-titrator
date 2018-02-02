#!/usr/bin/env python
from pHProbe import pHProbe

pH = pHProbe()
print pH.value(stable=0, unit='pH', verbose=True )
