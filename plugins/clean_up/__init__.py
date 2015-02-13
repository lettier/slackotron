import scribe
import clean_up
scribe = scribe.Scribe()
try:
	clean_up.CleanUp().run()
except Exception as e:
	scribe.error(e)
