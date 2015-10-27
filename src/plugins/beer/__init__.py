import lib.scribe
import beer
scribe = lib.scribe.Scribe()
try:
  beer.Beer().run()
except Exception as e:
  scribe.error(e)
