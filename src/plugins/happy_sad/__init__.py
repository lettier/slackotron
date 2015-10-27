import lib.scribe
import happy_sad
scribe = lib.scribe.Scribe()
try:
  happy_sad.HappySad().run()
except Exception as e:
  scribe.error(e)
