import random
import string
# special_chars = r".+*?^$()[]{}\|"

def randstr(N=3):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(N))

SPECIAL_CHARS = r'\[]'

import regex as re
from copy import deepcopy
EXIT_STATE = 'end'
START_STATE = 'start'

def make_or_nfa(pattern):
    assert pattern[0] == '(' and pattern[-1] == ')'
    assert string_excludes(pattern[1:-1], '\\'), f'no trailing backspaces in group {pattern}'

    pattern = list(pattern)[1:-1]
    
    groups = []
    current_group = ''
    while pattern:
        next_char = pattern.pop(0)

        if next_char == '\\':
            assert pattern != '', 'group can\'t end in odd # backslashes'
            current_group += next_char+pattern.pop(0)
        elif next_char == '|':
            groups.append(current_group)
            current_group = ''
        else:
            current_group += next_char
    
    groups.append(current_group)

    groups = [make_nfa(group) for group in groups]
    group_starts = []
    nfa = {}
    for group_nfa in groups:
        new_start, new_end = rename_boundary_states(group_nfa)
        group_nfa[new_end] = {'': {EXIT_STATE}}
        group_starts.append(new_start)
        nfa.update(group_nfa)
    nfa[START_STATE] = {'': set(group_starts)}
    return nfa
        


open_to_close = {
    '[': ']',
    '(': ')',
    '{': '}'
}

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

def string_excludes(s: str, excludes):
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
# special_chars = r".+*?^$()[]{}\|"



def rename_boundary_states(nfa):
    assert EXIT_STATE not in nfa
    new_start, new_end = randstr(), randstr()
    
    assert START_STATE in nfa
    nfa[new_start] = deepcopy(nfa[START_STATE])

    if START_STATE in nfa:
        del nfa[START_STATE]

    for state, transitions in nfa.items():
        for obs, dests in transitions.items():
            assert isinstance(dests, set), dests
            if EXIT_STATE in dests:
                nfa[state][obs] = (dests - {EXIT_STATE}).union({new_end})
    return new_start, new_end

def combine_nfas(nfa1, nfa2):
    assert START_STATE in nfa1 and START_STATE in nfa2
    in_between_state = 'transition_'+randstr()
    nfa1, nfa2 = deepcopy(nfa1), deepcopy(nfa2)
    for current_state, transition_rules in nfa1.items():
        for obs, dests in transition_rules.items():
            if EXIT_STATE in dests:
                dests.remove(EXIT_STATE)
                dests.add(in_between_state)
    nfa2[in_between_state] = deepcopy(nfa2[START_STATE])
    del nfa2[START_STATE]
    
    nfa1.update(nfa2)
    return nfa1

    
def make_nfa(pattern):
    # returns nfa: { current_state: {next_char: next_state, ...}, ...}

    nfa = {}
    current_state = START_STATE
    pattern = list(pattern)
    while pattern:
        if pattern[0] in r'[({':
            group = extract_bracket_group(''.join(pattern))
                
            if group == False:
                assert False, f"Unbalanced group from here on: {''.join(pattern)}"
            elif group[0] == '(':
                if group[1] == '?':
                    assert False, '(? unimplemented'
                # if 
                # group_nfa = make_nfa(group)
            elif group[0] == '[':
                group_nfa = make_char_nfa(group)
            elif group[0] == '\{':
                assert False, r'{...} unimplemented'
            
            gp_start, gp_end = rename_boundary_states(group_nfa)
            nfa[current_state] = {
                '': {gp_start}
            }
            nfa.update(group_nfa)
            current_state = gp_end

            pattern = pattern[len(group):]
            continue
        else:
            c = pattern.pop(0)
            assert c not in SPECIAL_CHARS
            next_state = randstr()
            nfa[current_state] = {
                    c: {next_state}
                }
            current_state = next_state


    nfa[current_state] = {'': {EXIT_STATE}}
    return nfa

def check(nfa, s, all_prefix_matches=False):
    all_matches = []
    pennies = [{'state': START_STATE, 'begin': 0, 'string': '', 'end': 0, 'eps_seen_states': set()}]
    while pennies:
        penny = pennies.pop()
        state = penny['state']

        next_char = s[penny['end']] if penny['end'] < len(s) else False

        for next_state in nfa.get(state, {}).get('', []):
            if next_state not in penny['eps_seen_states']:
                new_penny = deepcopy(penny)
                new_penny['eps_seen_states'].add(penny['state'])
                new_penny['state'] = next_state
                pennies.append(new_penny)
    
        if next_char in nfa.get(state, {}):
            for new_state in nfa[state][next_char]:
                new_penny = deepcopy(penny)
                new_penny['eps_seen_states'] = set()
                new_penny['state'] = new_state
                new_penny['end'] += 1
                new_penny['string'] += next_char
                pennies.append(new_penny)
        
        if (next_char == False or all_prefix_matches) and penny['state'] == EXIT_STATE:
                if all_prefix_matches:
                    all_matches.append(deepcopy(penny))
                else:
                    return penny
    return all_matches
    
    
                

# # nfa1 = make_nfa('ab')
# nfa2 = make_nfa('ab[df]')
# # nfa = combine_nfas(nfa1, nfa2)


# print(check(nfa2, 'abd', all_prefix_matches=True))


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
# special_chars = r".+*?^$()[]{}\|"

# Relevant: any unescaped &, |, {..}, +, *, ?, ^, $, (), [], {},

def seq_nfa(s: string):
    assert False

def make_and_nfa():
    assert False
# print(parse('thi|s (is a[ ]) t\{2,3\}?est'))

# special_chars = '&|\{\}+*?^$()[]{}\\'
# def parse(s):
#     s = list(s)
#     current_group = ''
#     subpatterns = []
#     while s:
#         c = s[0]
#         if c in special_chars:
#             # do something
#             if c == '\\':
#                 assert len(s) != 1, 'groups can\'t end in odd number of backslashes'
#                 current_group = current_group+s.pop(0)+s.pop(0)
#             elif c in '&|+*^$?':
#                 subpatterns.extend([current_group, s.pop(0)])
#                 current_group = ''
#             elif c in r'([{':
#                 bracket_group = extract_bracket_group(''.join(s))
#                 subpatterns.extend([current_group, bracket_group])
#                 s = s[len(bracket_group):]
#                 current_group = ''
#         else:
#             current_group += s.pop(0)
#     subpatterns.append(current_group)
#     return [p for p in subpatterns if p is not '']




special_chars = '&|\{\}+*?^$()[]{}\\'
def parse(s):
    if s[0] == '(' and extract_bracket_group(s) == s:
        return parse(s[1:-1])
    s = list(s)
    current_group = ''
    subpatterns = []
    while s:
        c = s[0]
        if c in special_chars:
            # do something
            if c == '\\':
                assert len(s) != 1, 'groups can\'t end in odd number of backslashes'
                current_group = current_group+s.pop(0)+s.pop(0)
            elif c in '&|^$':
                subpatterns.extend([current_group, s.pop(0)])
                current_group = ''
            elif c in '+*?':
                subpatterns.append([s.pop(0), current_group])
                current_group = ''
            elif c in r'([{':
                bracket_group = extract_bracket_group(''.join(s))
                if c == '[':
                    subpatterns.extend([current_group, ['[', bracket_group]])#make_char_nfa(bracket_group)])
                elif c == '(':
                    subpatterns.extend([current_group, [parse(bracket_group[1:-1])]])
                elif c == '{':
                    subpatterns.extend([['{', bracket_group, current_group]])# make quantifier basically
                s = s[len(bracket_group):]
                current_group = ''
        else:
            current_group += s.pop(0)
    subpatterns.append(current_group)
    subpatterns = [p for p in subpatterns if p != '']
    return subpatterns

def split_by_s_and_recurse(parsed, s):
    res = [[]]
    for pat in parsed:
        if pat != s:
            res[-1].append(pat)
        else:
            res.append([])
    return [parse_to_nfa(pat) for pat in res]

def make_or_nfa(parsed_patterns):
    groups = [make_nfa(group) for group in groups]
    group_starts = []
    nfa = {}
    for group_nfa in groups:
        new_start, new_end = rename_boundary_states(group_nfa)
        group_nfa[new_end] = {'': {EXIT_STATE}}
        group_starts.append(new_start)
        nfa.update(group_nfa)
    nfa[START_STATE] = {'': set(group_starts)}
    return nfa
    
    
def make_char_nfa(char_nfa: str):
    assert char_nfa[0] == '['
    assert char_nfa[-1] == ']'
    assert string_excludes(char_nfa[1:-1], excludes=r'|?{}()+.')
    
    # or_pat = '('+'|'.join(list(char_nfa[1:-1]))+')'
    or_nfa = make_or_nfa(list(char_nfa))
    return or_nfa

def make_char_nfa(char_nfa: str):
    assert char_nfa[0] == '['
    assert char_nfa[-1] == ']'
    assert string_excludes(char_nfa[1:-1], excludes=r'|?{}()+.')
    
    or_pat = '('+'|'.join(list(char_nfa[1:-1]))+')'
    or_nfa = make_or_nfa(or_pat)
    return or_nfa


def parse_to_nfa(parsed):
    if isinstance(parsed[0], str):
        if parsed[0] == '[':
            assert isinstance(parsed[1], str)
            return make_char_nfa(parsed[1])
            # return char nfa
        if parsed[0] == '{':
            # return quantifier nfa
            pass
        if parsed[0] in '?+*':
            # return quantifier nfa
            pass
    if '&' in parsed:
        return split_by_s_and_recurse(parsed, '&') #AND(split_by_s(...))
    if '|' in parsed:
        return split_by_s_and_recurse(parsed, '|') #OR(split_by_s(...))

    return parsed

parsed_str = parse(r'thi|s (is a[ ]) t{2,3}?est')



print(parse_to_nfa(parse(r'thi|s (is a[ ]) t&s{2,3}?es&t')))

