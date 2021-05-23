import sys

import shuffler
import spoiler

if len(sys.argv) > 1:
	seed = sys.argv.pop(1)
else:
	seed = None

if len(sys.argv) > 1:
	logic = sys.argv.pop(1)
else:
	logic = 'basic'

allSettings = ['fast-trendy', 'free-fishing', 'free-shop', 'free-book']
settings = []

for setting in allSettings:
	if setting in sys.argv:
		settings.append(setting)

placements = shuffler.makeRandomizedPlacement(seed, logic, ['dampe-page-1-first', 'dampe-page-1-second', 'dampe-page-2', 'dampe-bottle', 'dampe-page-3'], 
		['D1-instrument', 'D2-instrument', 'D3-instrument', 'D4-instrument', 'D5-instrument', 'D6-instrument', 'D7-instrument', 'D8-instrument',
		'trendy-prize-1', 'mamasha', 'ciao-ciao', 'sale', 'kiki', 'tarin-ukuku', 'chef-bear', 'papahl', 'christine-trade', 'mr-write', 'grandma-yahoo', 'bay-fisherman', 'mermaid-martha', 'mermaid-cave',
		'kanalet-crow', 'kanalet-mad-bomber', 'kanalet-kill-room', 'kanalet-bombed-guard', 'kanalet-final-guard'],
		settings, True)

spoiler.generateSpoilerLog(placements, 'outputs', seed)