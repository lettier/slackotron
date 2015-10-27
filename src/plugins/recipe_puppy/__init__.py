import lib.scribe
import recipe_puppy
scribe = lib.scribe.Scribe()
try:
  recipe_puppy.RecipePuppy().run()
except Exception as e:
  scribe.error(e)
