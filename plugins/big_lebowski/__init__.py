import scribe
import big_lebowski
scribe = scribe.Scribe()
try:
	big_lebowski.BigLebowski().run()
except Exception as e:
	scribe.error(e)
