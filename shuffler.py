import yaml
import re

# Open logic YAML
with open("logic.yml", 'r') as logicFile:
	logicDefs = yaml.safe_load(logicFile)


def addAccess(access, new):
	if new in access:
		access[new] += 1
	else:
		access[new] = 1

	return access


def removeAccess(access, toRemove):
	if toRemove in access:
		access[toRemove] -= 1
		if access[toRemove] == 0:
			access.pop(toRemove)
	return access


def hasAccess(access, key, amount=1):
	return key in access and access[key] >= amount


def checkAccess(newCheck, access, logic):
	# get the name of the check without the parameter sometimes applied to enemy checks
	noParams = re.match('[a-zA-Z0-9-]+', newCheck).group(0)

	if logicDefs[newCheck]['type'] == 'enemy':
		param = re.search('\\[([a-z]+)\\]', newCheck)
		if param:
			return eval(parseCondition(logicDefs[newCheck]['condition-basic'])) or eval(parseCondition(logicDefs[newCheck]['condition-'+param]))
		else:
			return eval(parseCondition(logicDefs[newCheck]['condition-basic']))
	else:
		# For item and follower checks, see if you have access to the region. Otherwise, check on the conditions, if they exist
		regionAccess = hasAccess(access, logicDefs[newCheck]['region']) if (logicDefs[newCheck]['type'] == 'item' or logicDefs[newCheck]['type'] == 'follower') else True
		basic        = eval(parseCondition(logicDefs[newCheck]['condition-basic'])) if ('condition-basic' in logicDefs[newCheck]) else True
		advanced     = eval(parseCondition(logicDefs[newCheck]['condition-advanced'])) if (('condition-advanced' in logicDefs[newCheck]) and (logic == 'advanced' or logic == 'glitched')) else False
		glitched     = eval(parseCondition(logicDefs[newCheck]['condition-glitched'])) if (('condition-glitched' in logicDefs[newCheck]) and logic == 'glitched') else False
		return regionAccess and (basic or advanced or glitched)



def parseCondition(condition):
	func = condition
	func = re.sub('([a-zA-Z-]+)', lambda match: f'hasAccess(access, "{match.group(1)}")', func)
	func = re.sub('\\):(\\d+)', lambda match: f', {match.group(1)})', func)
	func = re.sub('\\|', 'or', func)
	func = re.sub('&', 'and', func)
	return func


access = {}
items = []
locations = []
placements = {}
logic = 'basic'  #for now just hardcoding

for key in logicDefs:
	if logicDefs[key]['type'] == 'item':
		items.append(logicDefs[key]['content'])
		locations.append(key)
		placements[key] = None
		access = addAccess(access, logicDefs[key]['content'])
