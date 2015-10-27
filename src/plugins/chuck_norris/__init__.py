import lib.scribe
import chuck_norris
scribe = lib.scribe.Scribe()
try:
  chuck_norris.ChuckNorris().run()
except Exception as e:
  scribe.error(e)
