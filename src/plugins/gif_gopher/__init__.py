import lib.scribe
import gif_gopher
scribe = lib.scribe.Scribe()
try:
  gif_gopher.GifGopher().run()
except Exception as e:
  scribe.error(e)
