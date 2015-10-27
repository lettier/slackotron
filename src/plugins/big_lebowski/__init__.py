import lib.scribe
import big_lebowski
scribe = lib.scribe.Scribe()
try:
  big_lebowski.BigLebowski().run()
except Exception as e:
  scribe.error(e)
