import scribe
import slack_scraper
scribe = scribe.Scribe()
try:
	slack_scraper.SlackScraper().run()
except Exception as e:
	scribe.error(e)
