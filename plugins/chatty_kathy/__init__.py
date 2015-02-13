import scribe
import chatty_kathy
scribe = scribe.Scribe()
try:
	chatty_kathy.ChattyKathy().run()
except Exception as e:
	scribe.error(e)
