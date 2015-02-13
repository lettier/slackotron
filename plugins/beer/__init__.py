import scribe
import beer
scribe = scribe.Scribe()
try:
	beer.Beer().run()
except Exception as e:
	scribe.error(e)
