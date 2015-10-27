import lib.scribe
import calculator_duck
scribe = lib.scribe.Scribe()
try:
  calculator_duck.CalculatorDuck().run()
except Exception as e:
  scribe.error(e)
