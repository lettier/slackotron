import scribe
import yoda_speak
scribe = scribe.Scribe()
try:
	yoda_speak.YodaSpeak().run()
except Exception as e:
	scribe.error(e)
