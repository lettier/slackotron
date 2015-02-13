import scribe
import happy_sad
scribe = scribe.Scribe()
try:
	happy_sad.HappySad().run()
except Exception as e:
	scribe.error(e)
