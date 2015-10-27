import lib.scribe
import pivotal_pull
scribe = lib.scribe.Scribe()
try:
  pivotal_pull.PivotalPull().run()
except Exception as e:
  scribe.error(e)
