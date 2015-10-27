import lib.scribe
import clean_up
scribe = lib.scribe.Scribe()
try:
  clean_up.CleanUp().run()
except Exception as e:
  scribe.error(e)
