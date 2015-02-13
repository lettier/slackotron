import scribe
import calculator_duck
scribe = scribe.Scribe()
try:
	calculator_duck.CalculatorDuck().run()
except Exception as e:
	scribe.error(e)
