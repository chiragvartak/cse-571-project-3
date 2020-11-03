# wumpus_kb.py
# ------------
# Licensing Information:
# Please DO NOT DISTRIBUTE OR PUBLISH solutions to this project.
# You are free to use and extend these projects for EDUCATIONAL PURPOSES ONLY.
# The Hunt The Wumpus AI project was developed at University of Arizona
# by Clay Morrison (clayton@sista.arizona.edu), spring 2013.
# This project extends the python code provided by Peter Norvig as part of
# the Artificial Intelligence: A Modern Approach (AIMA) book example code;
# see http://aima.cs.berkeley.edu/code.html
# In particular, the following files come directly from the AIMA python
# code: ['agents.py', 'logic.py', 'search.py', 'utils.py']
# ('logic.py' has been modified by Clay Morrison in locations with the
# comment 'CTM')
# The file ['minisat.py'] implements a slim system call wrapper to the minisat
# (see http://minisat.se) SAT solver, and is directly based on the satispy
# python project, see https://github.com/netom/satispy .

import utils

#-------------------------------------------------------------------------------
# Wumpus Propositions
#-------------------------------------------------------------------------------

### atemporal variables

proposition_bases_atemporal_location = ['P', 'W', 'S', 'B']

def pit_str(x, y):
    "There is a Pit at <x>,<y>"
    return 'P{0}_{1}'.format(x, y)
def wumpus_str(x, y):
    "There is a Wumpus at <x>,<y>"
    return 'W{0}_{1}'.format(x, y)
def stench_str(x, y):
    "There is a Stench at <x>,<y>"
    return 'S{0}_{1}'.format(x, y)
def breeze_str(x, y):
    "There is a Breeze at <x>,<y>"
    return 'B{0}_{1}'.format(x, y)

### fluents (every proposition who's truth depends on time)

proposition_bases_perceptual_fluents = ['Stench', 'Breeze', 'Glitter', 'Bump', 'Scream']

def percept_stench_str(t):
    "A Stench is perceived at time <t>"
    return 'Stench{0}'.format(t)
def percept_breeze_str(t):
    "A Breeze is perceived at time <t>"
    return 'Breeze{0}'.format(t)
def percept_glitter_str(t):
    "A Glitter is perceived at time <t>"
    return 'Glitter{0}'.format(t)
def percept_bump_str(t):
    "A Bump is perceived at time <t>"
    return 'Bump{0}'.format(t)
def percept_scream_str(t):
    "A Scream is perceived at time <t>"
    return 'Scream{0}'.format(t)

proposition_bases_location_fluents = ['OK', 'L']

def state_OK_str(x, y, t):
    "Location <x>,<y> is OK at time <t>"
    return 'OK{0}_{1}_{2}'.format(x, y, t)
def state_loc_str(x, y, t):
    "At Location <x>,<y> at time <t>"
    return 'L{0}_{1}_{2}'.format(x, y, t)

def loc_proposition_to_tuple(loc_prop):
    """
    Utility to convert location propositions to location (x,y) tuples
    Used by HybridWumpusAgent for internal bookkeeping.
    """
    parts = loc_prop.split('_')
    return (int(parts[0][1:]), int(parts[1]))

# Hmm, even the actions are defined as PL sentences - no, these are not actions, these are just other env "states"
proposition_bases_state_fluents = ['HeadingNorth', 'HeadingEast',
                                   'HeadingSouth', 'HeadingWest',
                                   'HaveArrow', 'WumpusAlive']

def state_heading_north_str(t):
    "Heading North at time <t>"
    return 'HeadingNorth{0}'.format(t)
def state_heading_east_str(t):
    "Heading East at time <t>"
    return 'HeadingEast{0}'.format(t)
def state_heading_south_str(t):
    "Heading South at time <t>"
    return 'HeadingSouth{0}'.format(t)
def state_heading_west_str(t):
    "Heading West at time <t>"
    return 'HeadingWest{0}'.format(t)
def state_have_arrow_str(t):
    "Have Arrow at time <t>"
    return 'HaveArrow{0}'.format(t)
def state_wumpus_alive_str(t):
    "Wumpus is Alive at time <t>"
    return 'WumpusAlive{0}'.format(t)

proposition_bases_actions = ['Forward', 'Grab', 'Shoot', 'Climb',
                             'TurnLeft', 'TurnRight', 'Wait']

# .. and I think so is the physics of the game - defined as PL sentences.
def action_forward_str(t=None):
    "Action Forward executed at time <t>"
    return ('Forward{0}'.format(t) if t != None else 'Forward')
def action_grab_str(t=None):
    "Action Grab executed at time <t>"
    return ('Grab{0}'.format(t) if t != None else 'Grab')
def action_shoot_str(t=None):
    "Action Shoot executed at time <t>"
    return ('Shoot{0}'.format(t) if t != None else 'Shoot')
def action_climb_str(t=None):
    "Action Climb executed at time <t>"
    return ('Climb{0}'.format(t) if t != None else 'Climb')
def action_turn_left_str(t=None):
    "Action Turn Left executed at time <t>"
    return ('TurnLeft{0}'.format(t) if t != None else 'TurnLeft')
def action_turn_right_str(t=None):
    "Action Turn Right executed at time <t>"
    return ('TurnRight{0}'.format(t) if t != None else 'TurnRight')
def action_wait_str(t=None):
    "Action Wait executed at time <t>"
    return ('Wait{0}'.format(t) if t != None else 'Wait')


def add_time_stamp(prop, t): return '{0}{1}'.format(prop, t)

proposition_bases_all = [proposition_bases_atemporal_location,
                         proposition_bases_perceptual_fluents,
                         proposition_bases_location_fluents,
                         proposition_bases_state_fluents,
                         proposition_bases_actions]


#-------------------------------------------------------------------------------
# Axiom Generator: Current Percept Sentence
#-------------------------------------------------------------------------------

# I know I have quite simply written this. And I think that's fine because an input-output example is given.
# But I think, in general, you will have to keep an eye on all propositional symbols, to make sure that you are not
# leaving out anything that has to be asserted.
#def make_percept_sentence(t, tvec):
def axiom_generator_percept_sentence(t, tvec):
    """
    Asserts that each percept proposition is True or False at time t.

    t := time
    tvec := a boolean (True/False) vector with entries corresponding to
            percept propositions, in this order:
                (<stench>,<breeze>,<glitter>,<bump>,<scream>)

    Example:
        Input:  [False, True, False, False, True]
        Output: '~Stench0 & Breeze0 & ~Glitter0 & ~Bump0 & Scream0'
    """
    axiom_str = ''
    "*** YOUR CODE HERE ***"
    stench_pr = ('' if tvec[0] else '~') + percept_stench_str(t)
    breeze_pr = ('' if tvec[1] else '~') + percept_breeze_str(t)
    glitter_pr = ('' if tvec[2] else '~') + percept_glitter_str(t)
    bump_pr = ('' if tvec[3] else '~') + percept_bump_str(t)
    scream_pr = ('' if tvec[4] else '~') + percept_scream_str(t)
    axiom_str = ' & '.join([stench_pr, breeze_pr, glitter_pr, bump_pr, scream_pr])
    return axiom_str


#-------------------------------------------------------------------------------
# Axiom Generators: Initial Axioms
#-------------------------------------------------------------------------------

def axiom_generator_initial_location_assertions(x, y):
    """
    Assert that there is no Pit and no Wumpus in the location

    x,y := the location
    """
    axiom_str = ''
    "*** YOUR CODE HERE ***"
    axiom_str = '~'+pit_str(x,y) + ' & ' + '~'+wumpus_str(x,y)
    return axiom_str

# TODO: The "or the same location!" part, does not make much sense to me. I have not implemented it.
# Maybe it will come to bite me later? Need to check.
def axiom_generator_pits_and_breezes(x, y, xmin, xmax, ymin, ymax):
    """
    Assert that Breezes (atemporal) are only found in locations where
    there are one or more Pits in a neighboring location (or the same location!)

    x,y := the location
    xmin, xmax, ymin, ymax := the bounds of the environment; you use these
           variables to 'prune' any neighboring locations that are outside
           of the environment (and therefore are walls, so can't have Pits).
    """
    axiom_str = ''
    "*** YOUR CODE HERE ***"
    adjacent_locations = allowed_adjacent_locations(x, y, xmin, xmax, ymin, ymax)
    adjacent_pit_symbols = [pit_str(xi,yi) for xi,yi in adjacent_locations]
    pit_in_at_least_one_adjacent_location = " | ".join(adjacent_pit_symbols)

    axiom_str = breeze_str(x,y) + " <=> " + "(" + pit_in_at_least_one_adjacent_location + ")"

    return axiom_str

def generate_pit_and_breeze_axioms(xmin, xmax, ymin, ymax):
    axioms = []
    for x in range(xmin, xmax + 1):
        for y in range(ymin, ymax + 1):
            axioms.append(axiom_generator_pits_and_breezes(x, y, xmin, xmax, ymin, ymax))
    if utils.all_empty_strings(axioms):
        utils.print_not_implemented('axiom_generator_pits_and_breezes')
    return axioms

def axiom_generator_wumpus_and_stench(x, y, xmin, xmax, ymin, ymax):
    """
    Assert that Stenches (atemporal) are only found in locations where
    there are one or more Wumpi in a neighboring location (or the same location!)

    (Don't try to assert here that there is only one Wumpus;
    we'll handle that separately)

    x,y := the location
    xmin, xmax, ymin, ymax := the bounds of the environment; you use these
           variables to 'prune' any neighboring locations that are outside
           of the environment (and therefore are walls, so can't have Wumpi).
    """
    axiom_str = ''
    "*** YOUR CODE HERE ***"
    adjacent_locations = allowed_adjacent_locations(x, y, xmin, xmax, ymin, ymax)
    adjacent_wumpus_symbols = [wumpus_str(xi, yi) for xi, yi in adjacent_locations]
    wumpus_in_at_least_one_adjacent_location = " | ".join(adjacent_wumpus_symbols)
    wumpus_in_the_same_location = wumpus_str(x, y)

    axiom_str = stench_str(x, y) + " <=> " + "(" + wumpus_in_at_least_one_adjacent_location + \
                " | " + wumpus_in_the_same_location + \
                ")"

    return axiom_str

def generate_wumpus_and_stench_axioms(xmin, xmax, ymin, ymax):
    axioms = []
    for x in range(xmin, xmax + 1):
        for y in range(ymin, ymax + 1):
            axioms.append(axiom_generator_wumpus_and_stench(x, y, xmin, xmax, ymin, ymax))
    if utils.all_empty_strings(axioms):
        utils.print_not_implemented('axiom_generator_wumpus_and_stench')
    return axioms

def axiom_generator_at_least_one_wumpus(xmin, xmax, ymin, ymax):
    """
    Assert that there is at least one Wumpus.

    xmin, xmax, ymin, ymax := the bounds of the environment.
    """
    axiom_str = ''
    "*** YOUR CODE HERE ***"
    all_squares = all_possible_squares(xmin, xmax, ymin, ymax)
    return ' | '.join([wumpus_str(xi,yi) for xi,yi in all_squares])

def axiom_generator_at_most_one_wumpus(xmin, xmax, ymin, ymax):
    """
    Assert that there is at at most one Wumpus.

    xmin, xmax, ymin, ymax := the bounds of the environment.
    """
    axiom_str = ''
    "*** YOUR CODE HERE ***"
    all_squares = all_possible_squares(xmin, xmax, ymin, ymax)
    assertions = []
    added = set()
    for square1 in all_squares:
        for square2 in all_squares:
            if square1 == square2: continue
            key = tuple(sorted([square1, square2]))
            if key not in added:
                assertion = '(' + '~'+wumpus_str(square1[0], square1[1]) + ' | ' \
                            + '~'+wumpus_str(square2[0], square2[1]) + ')'
                assertions.append(assertion)
                added.add(key)
    axiom_str = ' & '.join(assertions)
    return axiom_str

def axiom_generator_only_in_one_location(xi, yi, xmin, xmax, ymin, ymax, t = 0):
    """
    Assert that the Agent can only be in one (the current xi,yi) location at time t.

    xi,yi := the current location.
    xmin, xmax, ymin, ymax := the bounds of the environment.
    t := time; default=0
    """
    axiom_str = ''
    "*** YOUR CODE HERE ***"
    other_locations = all_possible_squares(xmin, xmax, ymin, ymax)
    other_locations.remove((xi,yi))
    not_in_other_locations = ' & '.join(['~'+state_loc_str(other_x, other_y, t) for other_x,other_y in other_locations])
    axiom_str = state_loc_str(xi,yi,t) + ' & ' + '(' + not_in_other_locations + ')'
    return axiom_str

def axiom_generator_only_one_heading(heading = 'north', t = 0):
    """
    Assert that Agent can only head in one direction at a time.

    heading := string indicating heading; default='north';
               will be one of: 'north', 'east', 'south', 'west'
    t := time; default=0
    """
    axiom_str = ''
    "*** YOUR CODE HERE ***"
    heading_prop = None
    if heading == 'north':
        heading_prop = state_heading_north_str(t)
    elif heading == 'east':
        heading_prop = state_heading_east_str(t)
    elif heading == 'south':
        heading_prop = state_heading_south_str(t)
    elif heading == 'west':
        heading_prop = state_heading_west_str(t)
    else:
        raise Exception('Unreachable statement')
    other_directions = [
        state_heading_north_str(t), state_heading_east_str(t), state_heading_south_str(t), state_heading_west_str(t)
    ]
    other_directions.remove(heading_prop)
    no_other_direction = ' & '.join(['~'+direction for direction in other_directions])
    axiom_str = heading_prop + ' & ' + '(' + no_other_direction + ')'
    return axiom_str

def axiom_generator_have_arrow_and_wumpus_alive(t = 0):
    """
    Assert that Agent has the arrow and the Wumpus is alive at time t.

    t := time; default=0
    """
    axiom_str = ''
    "*** YOUR CODE HERE ***"
    axiom_str = state_have_arrow_str(t) + ' & ' + state_wumpus_alive_str(t)
    return axiom_str


def initial_wumpus_axioms(xi, yi, width, height, heading='east'):
    """
    Generate all of the initial wumpus axioms
    
    xi,yi = initial location
    width,height = dimensions of world
    heading = str representation of the initial agent heading
    """
    axioms = [axiom_generator_initial_location_assertions(xi, yi)]
    axioms.extend(generate_pit_and_breeze_axioms(1, width, 1, height))
    axioms.extend(generate_wumpus_and_stench_axioms(1, width, 1, height))
    
    axioms.append(axiom_generator_at_least_one_wumpus(1, width, 1, height))
    axioms.append(axiom_generator_at_most_one_wumpus(1, width, 1, height))

    axioms.append(axiom_generator_only_in_one_location(xi, yi, 1, width, 1, height))
    axioms.append(axiom_generator_only_one_heading(heading))

    axioms.append(axiom_generator_have_arrow_and_wumpus_alive())
    
    return axioms


#-------------------------------------------------------------------------------
# Axiom Generators: Temporal Axioms (added at each time step)
#-------------------------------------------------------------------------------

def axiom_generator_location_OK(x, y, t):
    """
    Assert the conditions under which a location is safe for the Agent.
    (Hint: Are Wumpi always dangerous?)

    x,y := location
    t := time
    """
    axiom_str = ''
    "*** YOUR CODE HERE ***"
    no_pit = '~' + pit_str(x,y)
    wumpus_condition = "(~{0} | ~{1})".format(state_wumpus_alive_str(t), wumpus_str(x,y))
    rhs = ' & '.join([no_pit, wumpus_condition])
    axiom_str = "{0} <=> ({1})".format(state_OK_str(x,y,t), rhs)
    return axiom_str

def generate_square_OK_axioms(t, xmin, xmax, ymin, ymax):
    axioms = []
    for x in range(xmin, xmax + 1):
        for y in range(ymin, ymax + 1):
            axioms.append(axiom_generator_location_OK(x, y, t))
    if utils.all_empty_strings(axioms):
        utils.print_not_implemented('axiom_generator_location_OK')
    return filter(lambda s: s != '', axioms)


#-------------------------------------------------------------------------------
# Connection between breeze / stench percepts and atemporal location properties

# Ah, look at this - mapping the percepts to the actual knowledge.
# This is where the dicussion of methodology of how the knowledge base is implemented and modified comes into picture.
# How I think of it, there can be 2 ways to work upon the knowledge:
# 1) Have fewer PL sentences, and only atemporal PL sentences, and, keep modifying them, based on the percepts you
# you receive at each step. You will be modifying them using simple Python code. But the problem that arises is, when
# one PL sentence is modified, how do you modify the rest of the KB, to incorporate the change based on this new
# knowledge? I think that will be a very difficult problem to solve.
# 2) Another alternative, that what is being done here, is introducing temporal information, and creating newer PL
# sentences. This way you don't need to modify existing PL sentences at all, because they are of a previous time. Of
# course, this is simpler, but introduces a large number of PL symbols. And I think, most of there PL symbols are
# useless information, that you are mostly not gonna use. Like, do you really care about *when* you killed the wumpus?
# Just the fact that the wumpus has been killed is enough to make future decisions. But yeah, this approach is simpler,
# and this is the approach that is being used in the project.
#
# There is one more things I want to point out. With approach (1) you will mostly write non-PL Python code for things
# like doing actions and making sense of sequences. I mean, that this code will be told which action has been done (or
# which percept has been observed) and modify the existing, relevant PL sentences accordingly.
# But with (2), because we don't know how to properly modify the KB based on actions and percepts, we model that as PL
# sentences themselves, and add more PL sentences to link those to the PL sentences that we actually care about.
# That is, (Breeze1, L_1_1) -- Breeze1_1 -- (P_1_2 or P_2_1)
# Notice how the first two PL sentences relate the percepts to the PL sentences that we actually care about to the
# actual inference that we again care about. The second link is what we mainly have been learning all this time in
# theory. The first link is just to make working on the KB in this project easier.
def axiom_generator_breeze_percept_and_location_property(x, y, t):
    """
    Assert that when in a location at time t, then perceiving a breeze
    at that time (a percept) means that the location is breezy (atemporal)

    x,y := location
    t := time
    """
    axiom_str = ''
    "*** YOUR CODE HERE ***"
    axiom_str = "{0} >> ({1} <=> {2})".format(
        state_loc_str(x,y,t),
        percept_breeze_str(t),
        breeze_str(x,y)
    )
    return axiom_str

def generate_breeze_percept_and_location_axioms(t, xmin, xmax, ymin, ymax):
    axioms = []
    for x in range(xmin, xmax + 1):
        for y in range(ymin, ymax + 1):
            axioms.append(axiom_generator_breeze_percept_and_location_property(x, y, t))
    if utils.all_empty_strings(axioms):
        utils.print_not_implemented('axiom_generator_breeze_percept_and_location_property')
    return filter(lambda s: s != '', axioms)

def axiom_generator_stench_percept_and_location_property(x, y, t):
    """
    Assert that when in a location at time t, then perceiving a stench
    at that time (a percept) means that the location has a stench (atemporal)

    x,y := location
    t := time
    """
    axiom_str = ''
    "*** YOUR CODE HERE ***"
    axiom_str = "{0} >> ({1} <=> {2})".format(
        state_loc_str(x, y, t),
        percept_stench_str(t),
        stench_str(x, y)
    )
    return axiom_str

def generate_stench_percept_and_location_axioms(t, xmin, xmax, ymin, ymax):
    axioms = []
    for x in range(xmin, xmax + 1):
        for y in range(ymin, ymax + 1):
            axioms.append(axiom_generator_stench_percept_and_location_property(x, y, t))
    if utils.all_empty_strings(axioms):
        utils.print_not_implemented('axiom_generator_stench_percept_and_location_property')
    return filter(lambda s: s != '', axioms)


#-------------------------------------------------------------------------------
# Transition model: Successor-State Axioms (SSA's)
# Avoid the frame problem(s): don't write axioms about actions, write axioms about
# fluents!  That is, write successor-state axioms as opposed to effect and frame
# axioms
#
# The general successor-state axioms pattern (where F is a fluent):
#   F^{t+1} <=> (Action(s)ThatCause_F^t) | (F^t & ~Action(s)ThatCauseNot_F^t)

# NOTE: this is very expensive in terms of generating many (~170 per axiom) CNF clauses!
def axiom_generator_at_location_ssa(t, x, y, xmin, xmax, ymin, ymax):
    """
    Assert the conditions at time t under which the agent is in
    a particular location (state_loc_str: L) at time t+1, following
    the successor-state axiom pattern.

    See Section 7. of AIMA.  However...
    NOTE: the book's version of this class of axioms is not complete
          for the version in Project 3.
    
    x,y := location
    t := time
    xmin, xmax, ymin, ymax := the bounds of the environment.
    """
    axiom_str = ''
    "*** YOUR CODE HERE ***"
    # Ah! I think the catch given as the "NOTE" is just to consider the "Wait" action too.
    # Okay, I'm not so sure anymore
    # TODO: Only generating for (1,1) and (1,2). Might or might not be a problem.

    upper_location = (x, y+1)
    bottom_location = (x, y-1)
    right_location = (x+1, y)
    left_location = (x-1, y)
    adjacent_locations = allowed_adjacent_locations(x, y, xmin, xmax, ymin, ymax)

    # For actions that cause F
    move_south, move_north, move_west, move_east = None, None, None, None
    if upper_location in adjacent_locations:
        move_south = "{0} & {1} & {2}".format(
            state_loc_str(upper_location[0], upper_location[1], t),
            state_heading_south_str(t),
            action_forward_str(t)
        )
    if bottom_location in adjacent_locations:
        move_north = "{0} & {1} & {2}".format(
            state_loc_str(bottom_location[0], bottom_location[1], t),
            state_heading_north_str(t),
            action_forward_str(t)
        )
    if right_location in adjacent_locations:
        move_west = "{0} & {1} & {2}".format(
            state_loc_str(right_location[0], right_location[1], t),
            state_heading_west_str(t),
            action_forward_str(t)
        )
    if left_location in adjacent_locations:
        move_east = "{0} & {1} & {2}".format(
            state_loc_str(left_location[0], left_location[1], t),
            state_heading_east_str(t),
            action_forward_str(t)
        )

    # For actions that prevent F
    just_stay_where_you_are = "{0} & ~({1} & ~{2})".format(
        state_loc_str(x,y,t),
        action_forward_str(t),
        percept_bump_str(t+1)
    )

    action_axioms = [move_south, move_north, move_west, move_east, just_stay_where_you_are]
    action_axioms = [e for e in action_axioms if e is not None]
    action_axioms = ['('+e+')' for e in action_axioms]

    axiom_str = "{0} <=> ({1})".format(
        state_loc_str(x,y,t+1),
        ' | '.join(action_axioms)
    )
    return axiom_str

def generate_at_location_ssa(t, x, y, xmin, xmax, ymin, ymax, heading):
    """
    The full at_location SSA converts to a fairly large CNF, which in
    turn causes the KB to grow very fast, slowing overall inference.
    We therefore need to restric generating these axioms as much as possible.
    This fn generates the at_location SSA only for the current location and
    the location the agent is currently facing (in case the agent moves
    forward on the next turn).
    This is sufficient for tracking the current location, which will be the
    single L location that evaluates to True; however, the other locations
    may be False or Unknown.
    """
    axioms = [axiom_generator_at_location_ssa(t, x, y, xmin, xmax, ymin, ymax)]
    if heading == 'west' and x - 1 >= xmin:
        axioms.append(axiom_generator_at_location_ssa(t, x-1, y, xmin, xmax, ymin, ymax))
    if heading == 'east' and x + 1 <= xmax:
        axioms.append(axiom_generator_at_location_ssa(t, x+1, y, xmin, xmax, ymin, ymax))
    if heading == 'south' and y - 1 >= ymin:
        axioms.append(axiom_generator_at_location_ssa(t, x, y-1, xmin, xmax, ymin, ymax))
    if heading == 'north' and y + 1 <= ymax:
        axioms.append(axiom_generator_at_location_ssa(t, x, y+1, xmin, xmax, ymin, ymax))
    if utils.all_empty_strings(axioms):
        utils.print_not_implemented('axiom_generator_at_location_ssa')
    return filter(lambda s: s != '', axioms)

#----------------------------------

def axiom_generator_have_arrow_ssa(t):
    """
    Assert the conditions at time t under which the Agent
    has the arrow at time t+1

    t := time
    """
    axiom_str = ''
    "*** YOUR CODE HERE ***"
    axiom_str = "{0} <=> ({1} & ~{2})".format(
        state_have_arrow_str(t+1),
        state_have_arrow_str(t),
        action_shoot_str(t)
    )
    return axiom_str

def axiom_generator_wumpus_alive_ssa(t):
    """
    Assert the conditions at time t under which the Wumpus
    is known to be alive at time t+1

    (NOTE: If this axiom is implemented in the standard way, it is expected
    that it will take one time step after the Wumpus dies before the Agent
    can infer that the Wumpus is actually dead.)

    t := time
    """
    axiom_str = ''
    "*** YOUR CODE HERE ***"
    axiom_str = "{0} <=> ({1} & ~{2})".format(
        state_wumpus_alive_str(t+1),
        state_wumpus_alive_str(t),
        percept_scream_str(t+1)
    )
    return axiom_str

#----------------------------------


def axiom_generator_heading_north_ssa(t):
    """
    Assert the conditions at time t under which the
    Agent heading will be North at time t+1

    t := time
    """
    axiom_str = ''
    "*** YOUR CODE HERE ***"
    # For actions that cause HeadingNorth
    turn_right_when_facing_west = "{} & {}".format(state_heading_west_str(t), action_turn_right_str(t))
    turn_left_when_facing_east = "{} & {}".format(state_heading_east_str(t), action_turn_left_str(t))

    # For actions that remove an existing HeadingNorth
    turn_away_when_facing_north = "{} & ~({} | {})".format(
        state_heading_north_str(t), action_turn_right_str(t), action_turn_left_str(t)
    )

    axiom_str = "{} <=> (({}) | ({}) | ({}))".format(
        state_heading_north_str(t+1),
        turn_right_when_facing_west,
        turn_left_when_facing_east,
        turn_away_when_facing_north
    )
    return axiom_str

def axiom_generator_heading_east_ssa(t):
    """
    Assert the conditions at time t under which the
    Agent heading will be East at time t+1

    t := time
    """
    axiom_str = ''
    "*** YOUR CODE HERE ***"
    turn_right_when_facing_north = "{} & {}".format(state_heading_north_str(t), action_turn_right_str(t))
    turn_left_when_facing_south = "{} & {}".format(state_heading_south_str(t), action_turn_left_str(t))

    turn_away_when_facing_east = "{} & ~({} | {})".format(
        state_heading_east_str(t), action_turn_right_str(t), action_turn_left_str(t)
    )

    axiom_str = "{} <=> (({}) | ({}) | ({}))".format(
        state_heading_east_str(t + 1),
        turn_right_when_facing_north,
        turn_left_when_facing_south,
        turn_away_when_facing_east
    )
    return axiom_str

def axiom_generator_heading_south_ssa(t):
    """
    Assert the conditions at time t under which the
    Agent heading will be South at time t+1

    t := time
    """
    axiom_str = ''
    "*** YOUR CODE HERE ***"
    turn_right_when_facing_east = "{} & {}".format(state_heading_east_str(t), action_turn_right_str(t))
    turn_left_when_facing_west = "{} & {}".format(state_heading_west_str(t), action_turn_left_str(t))

    turn_away_when_facing_south = "{} & ~({} | {})".format(
        state_heading_south_str(t), action_turn_right_str(t), action_turn_left_str(t)
    )

    axiom_str = "{} <=> (({}) | ({}) | ({}))".format(
        state_heading_south_str(t + 1),
        turn_right_when_facing_east,
        turn_left_when_facing_west,
        turn_away_when_facing_south
    )
    return axiom_str

def axiom_generator_heading_west_ssa(t):
    """
    Assert the conditions at time t under which the
    Agent heading will be West at time t+1

    t := time
    """
    axiom_str = ''
    "*** YOUR CODE HERE ***"
    turn_right_when_facing_south = "{} & {}".format(state_heading_south_str(t), action_turn_right_str(t))
    turn_left_when_facing_north = "{} & {}".format(state_heading_north_str(t), action_turn_left_str(t))

    turn_away_when_facing_west = "{} & ~({} | {})".format(
        state_heading_west_str(t), action_turn_right_str(t), action_turn_left_str(t)
    )

    axiom_str = "{} <=> (({}) | ({}) | ({}))".format(
        state_heading_west_str(t + 1),
        turn_right_when_facing_south,
        turn_left_when_facing_north,
        turn_away_when_facing_west
    )
    return axiom_str

def generate_heading_ssa(t):
    """
    Generates all of the heading SSAs.
    """
    return [axiom_generator_heading_north_ssa(t),
            axiom_generator_heading_east_ssa(t),
            axiom_generator_heading_south_ssa(t),
            axiom_generator_heading_west_ssa(t)]

def generate_non_location_ssa(t):
    """
    Generate all non-location-based SSAs
    """
    axioms = [] # all_state_loc_ssa(t, xmin, xmax, ymin, ymax)
    axioms.append(axiom_generator_have_arrow_ssa(t))
    axioms.append(axiom_generator_wumpus_alive_ssa(t))
    axioms.extend(generate_heading_ssa(t))
    return filter(lambda s: s != '', axioms)

#----------------------------------

def axiom_generator_heading_only_north(t):
    """
    Assert that when heading is North, the agent is
    not heading any other direction.

    t := time
    """
    axiom_str = ''
    "*** YOUR CODE HERE ***"
    axiom_str = "{} <=> (~{} & ~{} & ~{})".format(
        state_heading_north_str(t),
        state_heading_south_str(t),
        state_heading_east_str(t),
        state_heading_west_str(t)
    )
    return axiom_str

def axiom_generator_heading_only_east(t):
    """
    Assert that when heading is East, the agent is
    not heading any other direction.

    t := time
    """
    axiom_str = ''
    "*** YOUR CODE HERE ***"
    axiom_str = "{} <=> (~{} & ~{} & ~{})".format(
        state_heading_east_str(t),
        state_heading_south_str(t),
        state_heading_north_str(t),
        state_heading_west_str(t)
    )
    return axiom_str

def axiom_generator_heading_only_south(t):
    """
    Assert that when heading is South, the agent is
    not heading any other direction.

    t := time
    """
    axiom_str = ''
    "*** YOUR CODE HERE ***"
    axiom_str = "{} <=> (~{} & ~{} & ~{})".format(
        state_heading_south_str(t),
        state_heading_north_str(t),
        state_heading_east_str(t),
        state_heading_west_str(t)
    )
    return axiom_str

def axiom_generator_heading_only_west(t):
    """
    Assert that when heading is West, the agent is
    not heading any other direction.

    t := time
    """
    axiom_str = ''
    "*** YOUR CODE HERE ***"
    axiom_str = "{} <=> (~{} & ~{} & ~{})".format(
        state_heading_west_str(t),
        state_heading_south_str(t),
        state_heading_east_str(t),
        state_heading_north_str(t)
    )
    return axiom_str

def generate_heading_only_one_direction_axioms(t):
    return [axiom_generator_heading_only_north(t),
            axiom_generator_heading_only_east(t),
            axiom_generator_heading_only_south(t),
            axiom_generator_heading_only_west(t)]


def axiom_generator_only_one_action_axioms(t):
    """
    Assert that only one action can be executed at a time.
    
    t := time
    """
    axiom_str = ''
    "*** YOUR CODE HERE ***"
    assertions = []
    added = set()
    for action1 in proposition_bases_actions:
        for action2 in proposition_bases_actions:
            key = tuple(sorted([action1, action2]))
            if (key in added) or (action1 == action2):
                continue
            assertion = "~{} | ~{}".format(action1+str(t), action2+str(t))
            assertions.append(assertion)
            added.add(key)
    axiom_str = " & ".join(['('+e+')' for e in assertions])
    return axiom_str


def generate_mutually_exclusive_axioms(t):
    """
    Generate all time-based mutually exclusive axioms.
    """
    axioms = []
    
    # must be t+1 to constrain which direction could be heading _next_
    axioms.extend(generate_heading_only_one_direction_axioms(t + 1))

    # actions occur in current time, after percept
    axioms.append(axiom_generator_only_one_action_axioms(t))

    return filter(lambda s: s != '', axioms)

#-------------------------------------------------------------------------------

# Some utility functions go here:


def allowed_adjacent_locations(X, Y, XMIN, XMAX, YMIN, YMAX):
    X_allowed_adjacent = [X-1, X+1]
    if X == XMAX:
        X_allowed_adjacent.remove(X+1)
    if X == XMIN:
        X_allowed_adjacent.remove(X-1)
    Y_allowed_adjacent = [Y-1, Y+1]
    if Y == YMAX:
        Y_allowed_adjacent.remove(Y+1)
    if Y == YMIN:
        Y_allowed_adjacent.remove(Y-1)
    from itertools import product
    return list(product([X], Y_allowed_adjacent)) + list(product(X_allowed_adjacent, [Y]))


def all_possible_squares(xmin, xmax, ymin, ymax):
    return [(x, y) for x in range(xmin, xmax+1) for y in range(ymin, ymax+1)]


if __name__ == "__main__":
    # X, Y = 2, 1
    # XMIN, XMAX = 1, 4
    # YMIN, YMAX = 1, 4
    # print allowed_adjacent_locations(X, Y, XMIN, XMAX, YMIN, YMAX)

    print all_possible_squares(1, 4, 1, 4)

# TODO: Stench in wumpus's location? Breeze in pit's location? Yes this needs to be done. But take a look at the outputs first.
