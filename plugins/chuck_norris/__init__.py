import scribe
import chuck_norris
scribe = scribe.Scribe()
try:
	chuck_norris.ChuckNorris().run()
except Exception as e:
	scribe.error(e)
