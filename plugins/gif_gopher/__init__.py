import scribe
import gif_gopher
scribe = scribe.Scribe()
try:
	gif_gopher.GifGopher().run()
except Exception as e:
	scribe.error(e)
