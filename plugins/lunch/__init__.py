import scribe
import lunch
scribe = scribe.Scribe()
try:
	lunch.Lunch().run()
except Exception as e:
	scribe.error(e)
