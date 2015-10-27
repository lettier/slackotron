import lib.scribe
import lunch
scribe = lib.scribe.Scribe()
try:
  lunch.Lunch().run()
except Exception as e:
  scribe.error(e)
