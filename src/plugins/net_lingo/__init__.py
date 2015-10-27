import lib.scribe
import net_lingo
scribe = lib.scribe.Scribe()
try:
  net_lingo.NetLingo().run()
except Exception as e:
  scribe.error(e)
