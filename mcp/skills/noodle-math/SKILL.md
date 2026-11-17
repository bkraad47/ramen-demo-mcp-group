---
name: noodle-math
description: Work out a recipe's quantities for a different number of servings with the demo tools, and report the result briefly.
---
# Noodle math

Use this when someone asks to scale a noodle recipe up or down, or to convert its units.

1. Scale every quantity with `demo_calculator_tool` (`multiply` by the new servings, then `divide` by the old ones),
   one operation per call. Do not compute in your head.
2. Convert units the person asked for with `unit_convert` (grams to ounces, millilitres to cups, Celsius to
   Fahrenheit). Leave units the person did not mention as they are.
3. Before answering, run the final text through `word_count`; if it is over 120 words, shorten it.

Answer with the scaled ingredient list, one line per ingredient, and nothing else.
