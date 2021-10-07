import evfl

idgen = evfl.util.IdGenerator()

# Converts a list into a dict of {value: index} pairs
def invertList(l):
	return {l[i]: i for i in range(len(l))}


def readFlow(evflFile):
	flow = evfl.EventFlow()
	with open(evflFile, 'rb') as file:
		flow.read(file.read())

	return flow


def writeFlow(evflFile, flow):
	with open(evflFile, 'wb') as modified_file:
		flow.write(modified_file)

# Find and return an event from a flowchart given a name as a string. Return None if not found.
def findEvent(flowchart, name):
	if name == None:
		return

	for event in flowchart.events:
		if event.name == name:
			return event

	return None

# Find and return an entry point from a flowchart given a name as a string. Return None if not found.
def findEntryPoint(flowchart, name):
	if name == None:
		return

	for ep in flowchart.entry_points:
		if ep.name == name:
			return ep

	return None

def findActor(flowchart, name):
	return flowchart.find_actor(evfl.common.ActorIdentifier(name))

def addActorAction(actor, action):
	actor.actions.append(evfl.common.StringHolder(action))

def addActorQuery (actor, action):
	actor.queries.append(evfl.common.StringHolder(action))

# Change the previous event or entry point to have new be the next event. {previous} is the name of the event/entry point, {new} is the name of the event to add
# Return True if any event or entry point was modified and False if not
def insertEventAfter(flowchart, previous, new):
	newEvent = findEvent(flowchart, new)
	if not newEvent:
		return False

	prevEvent = findEvent(flowchart, previous)
	if prevEvent:
		prevEvent.data.nxt.v = newEvent
		prevEvent.data.nxt.set_index(invertList(flowchart.events))

		return True

	entry_point = findEntryPoint(flowchart, previous)
	if entry_point:
		entry_point.main_event.v = newEvent
		entry_point.main_event.set_index(invertList(flowchart.events))
		return True

	return False


def insertActionChain(flowchart, before, events):
	if len(events) == 0:
		return

	insertEventAfter(flowchart, before, events[0])

	for i in range(1, len(events)):
		insertEventAfter(flowchart, events[i-1], events[i])


def createActionChain(flowchart, before, eventDefs, after=None):
	if len(eventDefs) == 0:
		return

	current = createActionEvent(flowchart, eventDefs[0][0], eventDefs[0][1], eventDefs[0][2])
	insertEventAfter(flowchart, before, current)

	for i in range(1, len(eventDefs)):
		next = None if i != len(eventDefs)-1 else after
		before = current
		current = createActionEvent(flowchart, eventDefs[i][0], eventDefs[i][1], eventDefs[i][2], after)
		insertEventAfter(flowchart, before, current)


# Creates a new action event. {actor} and {action} should be strings, {params} should be a dict.
# {nextev} is the name of the next event.
def createActionEvent(flowchart, actor, action, params, nextev=None):
	nextEvent = findEvent(flowchart, nextev)

	new = evfl.event.Event()
	new.data = evfl.event.ActionEvent()
	new.data.actor = evfl.util.make_rindex(flowchart.find_actor(evfl.common.ActorIdentifier(actor)))
	new.data.actor.set_index(invertList(flowchart.actors))
	new.data.actor_action = evfl.util.make_rindex(new.data.actor.v.find_action(action))
	new.data.actor_action.set_index(invertList(new.data.actor.v.actions))
	new.data.params = evfl.container.Container()
	new.data.params.data = params

	flowchart.add_event(new, idgen)

	if nextEvent:
		new.data.nxt.v = nextEvent
		new.data.nxt.set_index(invertList(flowchart.events))

	return new.name


# Creates a new switch event and inserts it into the flow after the event named {previous}
# {actor} and {query} should be strings, {params} should be a dict, {cases} is a dict if {int: event name}
def createSwitchEvent(flowchart, actor, query, params, cases):
	new = evfl.event.Event()
	new.data = evfl.event.SwitchEvent()
	new.data.actor = evfl.util.make_rindex(flowchart.find_actor(evfl.common.ActorIdentifier(actor)))
	new.data.actor.set_index(invertList(flowchart.actors))
	new.data.actor_query = evfl.util.make_rindex(new.data.actor.v.find_query(query))
	new.data.actor_query.set_index(invertList(new.data.actor.v.queries))
	new.data.params = evfl.container.Container()
	new.data.params.data = params

	flowchart.add_event(new, idgen)

	caseEvents = {}
	for case in cases:
		ev = findEvent(flowchart, cases[case])
		if ev:
			caseEvents[case] = evfl.util.make_rindex(ev)
			caseEvents[case].set_index(invertList(flowchart.events))

	new.data.cases = caseEvents

	return new.name
