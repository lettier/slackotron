import lib.scribe
import yoda_speak
scribe = lib.scribe.Scribe()
try:
  yoda_speak.YodaSpeak().run()
except Exception as e:
  scribe.error(e)
