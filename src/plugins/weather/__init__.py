import lib.scribe
import weather
scribe = lib.scribe.Scribe()
try:
  weather.Weather().run()
except Exception as e:
  scribe.error(e)
