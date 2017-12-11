#!/usr/bin/env python
from pHProbe import pHProbe

pH = pHProbe()
print pH.value(stable=True, unit='pH', verbose=True )
