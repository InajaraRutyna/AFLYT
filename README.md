# AFLYT

Night operations in Danish. Listen to the bugged conversations, write Danish orders for your operatives, press RUN and watch them do exactly what you wrote. Wrong Danish makes the plan fail in front of you; the debrief names the rule and shows the fixed sentence.

- `src/aflyt.html` is the source; `python3 tools/build.py` writes `index.html`.
- `python3 test/logic.py` checks the parser and every night across 300 seeds.
- `python3 test/ui.py` plays all three nights on a phone-sized screen.
