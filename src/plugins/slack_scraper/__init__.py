import lib.scribe
import slack_scraper
scribe = lib.scribe.Scribe()
try:
  slack_scraper.SlackScraper().run()
except Exception as e:
  scribe.error(e)
