import scribe
import weather
scribe = scribe.Scribe()
try:
	weather.Weather().run()
except Exception as e:
	scribe.error(e)
