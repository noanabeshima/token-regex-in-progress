# type State = str
# type char = str (of length 1)
# type Transitions = dict[char, set[State]]
# type NFA = dict[State, Transitions]

import random
import string
from copy import deepcopy



def randstr(N=5):
    return ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(N))



EXIT_STATE = 'end'
START_STATE = 'start'
ANY_CHAR = 'ANY'

open_to_close = {
    '[': ']',
    '(': ')',
    '{': '}'
}

SPECIAL_CHARS = set(r"|&.+*?^$()[]{}")

def string_excludes(s: str, excludes):
    assert set(excludes).issubset(SPECIAL_CHARS)
    # assert SPECIAL_CHARS.issubset(set(excludes)), excludes
    # Excludes are any subset of special chars
    og_s = deepcopy(s)
    s = list(s)
    while s:
        c = s.pop(0)
        if c == '\\':
            assert len(s) != 0, 'group cannot end in an odd number of backslashes'
            s.pop(0)
            continue
        for x in excludes:
            if c == x:
                assert False, f'{x} in {og_s}'
    return True



from typing import Union

def rename_state(nfa, state, new_state: Union[True, str]=True):
    new_state = randstr() if new_state is True else new_state
    
    if state in nfa:
        nfa[new_state] = deepcopy(nfa[state])
        del nfa[state]

    for cur_state, transitions in nfa.items():
        for obs, dests in transitions.items():
            assert isinstance(dests, set), dests
            if state in dests:
                nfa[cur_state][obs] = (dests - {state}).union({new_state})
    
    return new_state


def extract_bracket_group(s):
    # s == a string that starts with a valid opening character: [, ), { and eventually closes,
    # not necessarily by the end of the string
    og_s = deepcopy(s)
    open_ = s[0]
    group = open_
    close_ = open_to_close[open_]
    s = list(s[1:])
    counter = 1

    while True:
        assert len(s) !=0, f'extraction of bracketed group `{og_s}` failed, not enough closing brackets by end of string'

        c = s.pop(0)
        group = group + c
        if c == '\\':
            assert len(s) != 0, 'string in bracketed group must not end in odd number of backslashes'
            s.pop(0)
            continue
        elif c == open_:
            counter += 1
        elif c == close_:
            counter -= 1
        
        if counter == 0:
            return group


def parse(s):
    if s[0] == '(' and extract_bracket_group(s) == s:
        return parse(s[1:-1])
    s = list(s)
    # last_group = ''
    running_str = ''

    subpatterns = []
    while s:
        c = s[0]
        if c in '&|\{\}+*?^$()[]{}\\':
            if c == '\\':
                assert len(s) != 1, 'groups can\'t end in odd number of backslashes'
                running_str = running_str+s.pop(0)+s.pop(0)
            elif c in '&|^$':
                subpatterns.extend([running_str, s.pop(0)])
                running_str = ''
            elif c in '+*?':
                if running_str == '':
                    assert len(subpatterns) > 1
                    if isinstance(subpatterns[-1], str):
                        assert subpatterns[-1] not in '&|^$'
                    subpatterns.append([s.pop(0), subpatterns.pop()])
                else:
                    subpatterns.extend([running_str[:-1], [s.pop(0), running_str[-1]]])
                running_str = ''
            elif c in r'([{':
                bracket_group = extract_bracket_group(''.join(s))
                if c == '[':
                    subpatterns.extend([running_str, ['[', bracket_group[1:-1]]])#make_char_nfa(bracket_group)])
                elif c == '(':
                    parsed = parse(bracket_group[1:-1])
                    assert isinstance(parsed, list)
                    subpatterns.extend([running_str, parsed])
                elif c == '{':
                    # [STUB] {n} should turn into {n,n} and bracket_group should be expanded into two elements
                    if running_str == '':
                        subpatterns.append(['{', bracket_group[1:-1], subpatterns.pop()])
                    else:
                        subpatterns.extend([running_str[:-1], ['{', bracket_group[1:-1], running_str[-1]]])
                s = s[len(bracket_group):]
                running_str = ''
        else:
            running_str += s.pop(0)
    subpatterns.append(running_str)
    subpatterns = [p for p in subpatterns if p != '']
    while len(subpatterns) == 1 and isinstance(subpatterns[0], list):
        subpatterns = subpatterns[0]
    
    if '|' in subpatterns and '&' in subpatterns:
        subpats = ['&', split_list(subpatterns, '&')]
        for i, subpat in subpats[1]:
            if '|' in subpat:
                subpats[1][i] = ['|', split_list(subpat)]
    
    elif '&' in subpatterns:
        subpatterns = ['&', split_list(subpatterns, '&')]
    elif '|' in subpatterns:
            subpatterns = ['|', split_list(subpatterns, '|')]

    return subpatterns


def split_list(l, s):
    res = [[]]
    for pat in l:
        if pat != s:
            res[-1].append(pat)
        else:
            res.append([])
    res = [p for p in res if p != []]
    for _ in range(4):
        res = [p[0] if len(p) == 1 and isinstance(p[0], str) else p for p in res]
        res = [p[0] if len(p) == 1 and isinstance(p[0], list) else p for p in res]
    return res



def make_or_nfa(parsed_groups):
    nfas = [parse_tree_to_nfa(group) for group in parsed_groups]
    if len(nfas) == 1:
        return nfas[0]
    group_starts = []
    nfa = {}
    for group_nfa in nfas:
        new_start = rename_state(group_nfa, START_STATE)
        new_exit = rename_state(group_nfa, EXIT_STATE)

        # point to shared exit state
        group_nfa[new_exit] = {'': {EXIT_STATE}}
        group_starts.append(new_start)
        nfa.update(group_nfa)
    # add the shared start state
    nfa[START_STATE] = {'': set(group_starts)}
    return nfa

    
def make_char_nfa(char_nfa: str):
    assert string_excludes(char_nfa, excludes=r'|?{}()+.[]')

    return make_or_nfa(list(char_nfa))

DIGITS = '0123456789'
def is_num(s):
    return all([c in DIGITS for c in s])


def make_string_nfa(s):
    s = list(s)
    nfa = {}
    current_state = START_STATE
    while s:
        next_state = randstr()
        if s[0] == '.':
            nfa[current_state] = {ANY_CHAR: {next_state}}
            s = s[1:]
        elif s[0] == '\\':
            assert len(s) >= 2
            nfa[current_state] = {s[1]: {next_state}}
            s = s[2:]
        else:
            nfa[current_state] = {s[0]: {next_state}}
            s = s[1:]
        current_state =  next_state
    rename_state(nfa, current_state, EXIT_STATE)
    return nfa


def add_eps_transition(nfa, start, end):
    if start not in nfa:
        nfa[start] = {}
    if '' not in nfa[start]:
        nfa[start][''] = set()
    nfa[start][''].add(end)
    return nfa

def make_optional_nfa(p):
    parse_tree_to_nfa(p)

def parse_tree_to_nfa(parsed: Union[list, str]):
    if isinstance(parsed, str):
        return make_string_nfa(parsed)
    
    if isinstance(parsed[0], str) and parsed[0] in r'*+?[{&|':
        assert isinstance(parsed, list), f'parser error, the following string shouldn\'t start with the character it does: {parsed[0]}'
        if parsed[0] == '*':
            assert len(parsed) == 2
            nfa = parse_tree_to_nfa(parsed[1])
            add_eps_transition(nfa, EXIT_STATE, START_STATE)
            add_eps_transition(nfa, START_STATE, EXIT_STATE)
            return nfa
        elif parsed[0] == '+':
            assert len(parsed) == 2
            return parse_tree_to_nfa([parse_tree_to_nfa(parsed[1]), ['*', parsed[1]]])
        elif parsed[0] == '?':
            assert len(parsed) == 2
            nfa = parse_tree_to_nfa(parsed[1])
            add_eps_transition(nfa, START_STATE, EXIT_STATE)
            return nfa
        elif parsed[0] == '[':
            assert isinstance(parsed[1], str)
            assert len(parsed) == 2
            return make_char_nfa(parsed[1])
            # return char nfa
        elif parsed[0] == '{':
            assert len(parsed) == 3

            # 3this behavior should go in parser
            ###
            bounds = parsed[1].split(',')
            assert len(bounds) <= 2
            for b in bounds:
                assert b == '' or is_num(b)
            assert ''.join(bounds) != ''
            ###

            if len(bounds) == 2:
                if bounds[0] == '':
                    return parse_tree_to_nfa([r'{', bounds[1], ['?', parsed[2]]])
                elif bounds[1] == '':
                    return parse_tree_to_nfa([[r'{', bounds[0], parsed[2]], ['*', parsed[2]]])
                else:
                    return parse_tree_to_nfa([[r'{', bounds[0], parsed[2]], ['{', str(int(bounds[1])-int(bounds[0])), ['?', parsed[2]]]])

            elif len(bounds) == 1:
                return parse_tree_to_nfa([parsed[2] for _ in range(int(bounds[0]))])
            else:
                assert False, 'Previously-thought impossible location'            
        elif parsed[0] == '&':
            assert False, '& unimplemented, needs modifications to parse_tree_to_nfa'
        elif parsed[0] == '|':
            assert len(parsed) == 2
            return make_or_nfa(parsed[1])
        else:
            assert False, f'Previously-thought impossible case, "{parsed[0]}"'  

    nfa = {}
    current_state = randstr()
    add_eps_transition(nfa, START_STATE, current_state)
    while parsed:
        new_nfa = parse_tree_to_nfa(parsed.pop(0))
        new_state = randstr()
        rename_state(new_nfa, START_STATE, current_state)
        rename_state(new_nfa, EXIT_STATE, new_state)
        nfa.update(new_nfa)

        current_state = new_state

    rename_state(nfa, current_state, EXIT_STATE)

    return nfa


def check(nfa, s):
    pennies = [{'state': START_STATE, 'string': '', 'i': 0, 'eps_seen_states': set(), 'transitions': []}]
    while pennies:
        penny = pennies.pop()
        state = penny['state']

        next_char = s[penny['i']] if penny['i'] < len(s) else False

        state_transitions = nfa.get(state, {})
        for next_state in nfa.get(state, {}).get('', []):
            if next_state not in penny['eps_seen_states']:
                new_penny = deepcopy(penny)
                new_penny['eps_seen_states'].add(penny['state'])
                new_penny['state'] = next_state
                new_penny['transitions'].append((state, '', next_state))
                pennies.append(new_penny)
    
        if next_char in state_transitions or ANY_CHAR in state_transitions and next_char is not False:
            attainable_states = state_transitions.get(next_char, set()).union(state_transitions.get(ANY_CHAR, set()))
            for next_state in attainable_states:
                new_penny = deepcopy(penny)
                new_penny['eps_seen_states'] = set()
                new_penny['state'] = next_state
                new_penny['string'] += next_char
                new_penny['i'] += 1
                new_penny['transitions'].append((state, next_char, next_state))
                pennies.append(new_penny)

        
        if next_char == False and penny['state'] == EXIT_STATE:
            return True
    else:
        return False
    
s = r'\([0123456789]{3}\) [0123456789]{3}-[0123456789]{4,}'
nfa = parse_tree_to_nfa(parse(s))

print(check(nfa, '(231) 512-56363'))