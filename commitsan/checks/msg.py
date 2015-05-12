from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

import collections
import itertools
import regex as re
import textwrap

from commitsan.checks import checker
from commitsan.git import git_show


def split_lines(s):
    return [line.strip() for line in s.split('\n') if line.strip()]

ignores = split_lines('''
    a
    again
    all
    always
    an
    any
    big
    bigger
    bit
    correct
    correctly
    couple
    couple of
    different
    differently
    do
    don't
    example of
    extra
    extreme
    extremely
    few
    good
    great
    greatly
    insignificant
    insignificantly
    less
    little
    lot
    lot of
    lots
    lots of
    major
    minor
    more
    never
    no more
    not anymore
    once again
    once more
    one more time
    one more times
    only
    proper
    properly
    significant
    significantly
    slight
    slightly
    small
    smaller
    some
    the
    various
''')

whitelist = split_lines('''
    ahead
    alone
    bogus
    buf
    buff
    bug
    bulk
    bus
    busy
    callee
    caller
    checksum
    child
    coding
    cold
    compiler
    down
    during
    event
    field
    file
    handler
    head
    help
    hole
    huge
    image
    issue
    killer
    know
    macro
    mgmt
    mode
    model
    nest
    net
    newly
    next
    node
    none
    once
    pending
    prompt
    resource
    role
    route
    scrub
    seen
    sense
    separately
    shared
    shell
    slave
    slot
    spelling
    stat
    status
    string
    stub
    stuck
    stuff
    there
    thread
    three
    trend
    unchanged
    unhandled
    uninitialized
    unsupported
    user
    void
    word
    worker
    zone
''')

blacklist = split_lines('''
    bug
    bugs
    does
    doesn't
    doing
    done
    new
    news
    nothing important
    nothing meaningful
    nothing significant
    nothing special
    now
    old
    optimisation
    optimisations
    optimization
    optimizations
    simplification
    simplifications
    stub
    stubs
''')

verbs = split_lines('''
    add
    adopt
    allow
    append
    avoid
    begin^ : began : begun
    build^ : built
    bump
    call
    change
    check
    clean
    cleanup^
    clear
    clone
    close
    comment
    commit^
    compile
    complain
    consolidate
    convert
    correct
    create
    deal : dealt
    define
    delete
    disable
    document
    drop^ : dropped : dropt
    eliminate
    enable
    ensure
    exchange
    export
    extract
    fix
    fold
    forbid^ : forbad : forbade : forbidden
    forget^ : forgot : forgotten
    get^ : got : gotten
    grow : grew : grown
    handle
    hold : held
    ignore
    implement
    improve
    include
    inform
    initialise
    initialize
    introduce
    issue
    kill
    make : made
    mark
    merge
    move
    need
    optimise
    optimize
    pass
    plug^
    polish
    poll
    port
    prefer^
    prepare
    prevent
    print
    provide
    redefine
    reduce
    reenable
    refactor
    reimplement
    reintroduce
    remove
    rename
    replace
    restore
    restructure
    return
    reverse
    revert
    reword
    rework
    rewrite : rewrote : rewritten
    roll
    save
    send : sent
    separate
    set^ :
    setup^ :
    show : shown
    simplify
    split^
    squash
    start
    startup^
    stop^
    support
    switch
    throw : threw : thrown
    tidy
    try
    turn
    uncomment
    unexport
    unify
    unset^ :
    update
    use
    work
    workaround :
    write : wrote : written
    yield
''')


def verb_forms(s):
    """
    From a given verb makes 4-element tuple of:
        infinitive: The verb itself
                -s: The third form
              -ing: Continuous tense
               -ed: Past simple tense
        """
    words = s.split()
    verb = words.pop(0)
    third = cont = past = None

    if verb[-1] == '^':
        verb = verb[:-1]
        cont = past = verb + verb[-1]  # stop-s   # stop-P-ing # stop-P-ed
    elif verb[-1] == 'e':
        cont = past = verb[:-1]        # merge-s  # merg-ing   # merg-ed
    elif verb[-1] in 'sxz' or verb[-2:] in ('ch', 'sh'):
        third = verb + 'e'             # fix-e-s  # fix-ing    # fix-ed
    elif verb[-1] == 'y':
        third = verb[:-1] + 'ie'       # tr-ie-s  # try-ing    # tr-i-ed
        past = verb[:-1] + 'i'

    return tuple(' '.join([form] + words)
                 for form in ((verb),
                              (third or verb) + 's',
                              (cont or verb) + 'ing',
                              (past or verb) + 'ed'))

def to_ident(word, prefix=''):
    if word is not None:
        return prefix + re.sub(r'\W', '', word).lower()

def make_verb_forms(verb_lines):
    """
    Constructs a pair of lists:
        1. Containing verbs in imperative mood (like 'fix')
        2. Forms considered wrong ('fixes / fixing / fixed')
    """
    good_list = []
    bad_list = []
    bad_idents = {}  # bad-to-good form mapping

    for line in verb_lines:
        phrases = [phrase.strip() for phrase in line.split(':')]
        if not any(phrases):
            continue

        verb, third, cont, past = verb_forms(phrases[0])
        good_list.append(verb)
        for bad_form in filter(bool, (phrases[1:] or [past]) + [third, cont]):
            bad_list.append(bad_form)
            bad_idents[to_ident(bad_form, prefix='bad_')] = verb

    return good_list, bad_list, bad_idents


good_verb_forms, bad_verb_forms, bad_idents_mapping = make_verb_forms(verbs)

# These are not verbs, but verb_forms is used to make a plural form of nouns.
whitelist = list(itertools.chain.from_iterable(verb_forms(word)[:2]
                                               for word in whitelist))


def to_regex(*word_lists, **name_prefix_kw):
    name_prefix = name_prefix_kw.pop('name_prefix', 'word_')
    words = sorted(itertools.chain.from_iterable(word_lists), key=len)
    return r'(?:{})'.format('|'.join('(?<{}>{})'
                                     .format(to_ident(word, name_prefix),
                                             r'\s+'.join(word.split()))
                                     for word in words))


FUZZINESS = {
    0: '{i<=1,s<=1,e<=1}',
    4: '{i<=1,d<=1,2i+2d+3s<=4}',
    8: '{i<=2,d<=2,2i+2d+3s<=6}',
}

FUZZY_PAT_TMPL = r'''(?x:
\m (?&{group}) \M
| (?: (?= \m (?&{group}){fuzzy[0]} \M (?<__f_la>.*)$) .{{0,}}
    | (?= \m (?&{group}){fuzzy[4]} \M (?<__f_la>.*)$) .{{4,}}
    | (?= \m (?&{group}){fuzzy[8]} \M (?<__f_la>.*)$) .{{8,}} ) (?=\g<__f_la>$)
)'''

class Fuzzifier(object):
    def __init__(self, fuzziness={}):
        super(Fuzzifier, self).__init__()
        self.fuzziness = dict(FUZZINESS)
        self.fuzziness.update(fuzziness)
    def __getitem__(self, name):
        return FUZZY_PAT_TMPL.format(group=name, fuzzy=self.fuzziness)
    def __call__(self, pat, name):
        return (r'''(?x: (?<{group}> {pat} ){{0}} )'''
                .format(group=name, pat=pat) + self[name])

fuzzify = Fuzzifier()


#   - Bullets or numbered list
# ^^^^
INDENT_RE = re.compile(r'''(?x)^
  (?<bullet> \s{0,3} ( [*\-] | \d [:.)] | [^\W_] [.)] ) )? \s*
''')

# [old-style] topic: (label) ...
# ^^^^^^^^^^^ ^^^^^^ ^^^^^^^
TOPIC_RE = re.compile(r'''(?x)^
  (?: \s{0,2}
    (?<topic>
        (?<brackets> (?=\[) (\[+ \S+? \]+){i<=1} (\s? :)? )
      | (?<parens>   (?=\() (\(+ \S+? \)+){i<=1} (\s? :)? )
      | (?<plain>    (?=\S) (    \S+?    ){i<=2} (\s? :)  )
      | (?<plain>   ([^\s;]+?) (?<!\(\)) (?<semi> \s? ;) ) )
    (?<= [\]):;] ) )*+
  \s*
''')

# Some text; and more; ';' is ignored; func(); too; and also an orphan ; alone
# ^^^^^^^^^  ^^^^^^^^  ^^^^^^^^^^^^^^  ^^^^^^^^^^^  ^^^^^^^^^^^^^^^^^^^^^^^^^^
SEMI_RE = re.compile(r'''(?x)^
  (?: \s*
    (?<sentence> ( (?<!\\)(';'|";") | \(\); | \w+\(.*?\); | \s+; | . )*? )
    ( ; | \s* $ ) )*+
$''')

# Here goes the sentence itself.
SENTENCE_RE = re.compile(r'''(?x)^
  (?<head>
    (?<skipping>
      ( (?<skip> \m {skip_pat} \M ) \s* )*+ )

    (?<verb> (?<head_verb>
        (?<good> \m .{{0,2}}  # This compensates fuzziness, for example,
                              # in "xxx's fix", where "s fix" ~ "fixes".
                 \m {good_pat} \M )

      | (?<bad>  \m {bad_pat}  \M ) ) )?+ )

  (?<tail>
    (?(head_verb)|  # Don't match if there was a verb at the beginning.

      # Also give up if some part of a sentence starts with a good verb.
      ( (?! [:;,.?!+] \s* (?<!\.) (?&skipping) (?&good) ) . )*?

      # Grab an auxiliary verb, if any,
      # but filter out a subordinating clause.
      (?<= (?<! \m (that|which)('?s)? \M \s* )
        (?<aux>
          (?: \m
            (?: (are|is|was|were)(\s*not|n't)? (\s+being)?
              | (?: (have|has|had)?(\s*not|n't)? | (\s+ been) )+ )
            \M \s*)?+ ) )

      (?<verb> (?<tail_verb> (?! (?&good)|(?&skip) ) (?&bad) (?<!s|ing|ion) ) )

      (?= \s* ([:;,.?!)](?!\w)|\s\(|$) ) )?+

    .* )  # Consume till the end, for sake of convenience.

$'''.format(good_pat=to_regex(good_verb_forms, whitelist,
                              name_prefix='good_'),
            bad_pat=fuzzify(to_regex(bad_verb_forms, blacklist,
                                     name_prefix='bad_'),
                            name='__bad_pat'),
            skip_pat=fuzzify(to_regex(ignores,
                                      name_prefix='skip_'),
                             name='__skip_pat')),
    flags=re.I|re.B)

END_PERIOD_RE = re.compile(r'''(?x)
  (?<! \m (?: Co | Ltd | Inc
            | et\ al | etc | e\.g | i\.e | R\.I\.P
            | mgmt | smth | std | stmt )
     | \. )
  \.
$''', flags=re.I)


def non_empty(iterable):
    return list(filter(None, iterable))

def strip_topics(iterable):
    return non_empty(s.strip('[( )]:;') for s in iterable)

def wrap(s, width=32, ending=' ...'):
    lines = textwrap.wrap(s, width,
                          break_long_words=False,
                          break_on_hyphens=False)
    if not lines:
        return ''
    s = lines[0]
    if len(lines) > 1:
        s += ending
    return s


def bad_to_good(sm):
    sc = sm.capturesdict()

    bad = sc['bad'][0] if sc['bad'] else None
    bad_ident = to_ident(bad, prefix='bad_')

    if bad:
        # Find out the exact verb/word.
        if bad not in sc[bad_ident]:
            # fuzzy?
            for bad_ident in bad_idents_mapping:
                if bad in sc[bad_ident]:
                    break
            else:
                bad_ident = None

    return bad, bad_idents_mapping.get(bad_ident)


def msg_regex(repo, commit, lines):
    indent = 0

    for i, line in enumerate(lines or ['']):
        im = INDENT_RE.match(line)
        is_bullet_line = bool(im.group('bullet'))
        is_subject_line = (i == 0)

        is_paragraph_line = (i > 0) and (is_bullet_line or not lines[i-1])

        line_indent = im.end()
        if is_bullet_line or line_indent < indent:
            indent = line_indent  # Zero if the line is blank.

        if len(line) > 72 and not line.startswith(' ' * (indent+4)):
            if is_subject_line:
                yield ('error', 'msg/subj-limit',
                       'Keep the subject concise: 50 characters or less')
            else:
                yield ('error', 'msg/wrap',
                       'Wrap the body at 72 characters')

        if is_subject_line and is_bullet_line:
            yield ('warning', 'msg/subj-list',
                   'Do not put bullets on the subject line')

        if not is_subject_line and not is_paragraph_line:
            # Within a body, only lines starting a paragraph are considered.
            continue

        line = line[line_indent:]

        tm = TOPIC_RE.match(line)
        tc = tm.capturesdict()

        line = line[tm.end():]

        labels = [label.join('()') for label in strip_topics(tc['parens'])]

        colons_topic = ':'.join(strip_topics(tc['brackets'] + tc['plain']))
        orig_topics = non_empty(re.split(r'\s*(?::\s*)+', colons_topic))

        topics = []
        sentence_matches = []

        for topic in orig_topics:
            # Topic regex recognizes up to 3 words (\S+ with {i<=2} fuzziness).
            # Filter out false positives like in 'fixing smth.: works now' and
            # treat them as regular sentences performing additional checks
            # like capitalization or mood of the sentence.
            sm = SENTENCE_RE.match(topic)
            if (sm.captures('verb') and
                len(re.findall(r'\m[\w/.,+\-]+\M', topic)) > 1):
                sentence_matches.append(sm)
            else:
                topics.append(topic)

        if not (is_subject_line or topics or labels):
            # A paragraph looks like and ordinal statement, don't check it.
            continue

        semi_sentences = non_empty(SEMI_RE.match(line).captures('sentence'))
        sentence_matches.extend(map(SENTENCE_RE.match, semi_sentences))

        topic = ': '.join(topics + [''])
        label = ' '.join(labels + [''])

        trunc_topic = ': '.join((topics[:-1] and ['...']) + topics[-1:] + [''])
        trunc_label = ' '.join(labels[:1] + (labels[1:] and ['...']) + [''])

        trunc_sentence = ''  # The wrapped first sentence, if any.

        for j, sm in enumerate(sentence_matches):
            sentence = orig_sentence = sm.string.rstrip()
            is_first_sentence = (j == 0)

            bad, good = bad_to_good(sm)
            if bad:
                if good:
                    if sm['head_verb']:
                        # Fixup the sentence to keep examples used through
                        # remaining unrelated checks consistent. The following
                        # stmt replaces the 'bad' verb with a 'good' one.
                        sentence = sm.expand(r'\g<skipping>{}\g<tail>'
                                             .format(good))
                        example = (": '{}', not '{}'"
                                   .format(good.capitalize(), bad))
                    else:
                        # The sentence ends with some shit, strip it out.
                        sentence = wrap(sentence,
                                        width=max(3, sm.start('aux')))
                        example = (": '{}', not '... {}{}'"
                                   .format(good.capitalize(), sm['aux'], bad))
                else:
                    example = ' mood'

                yield ('error' if is_subject_line else 'warning', 'msg/mood',
                       'Use the imperative'+example)

            if sm['head']:
                sentence = sentence.capitalize()

            if sentence and is_first_sentence:
                trunc_sentence = wrap(sentence, width=3)

                if orig_sentence[0].islower() and sentence[0].isupper():
                    yield ('warning', 'msg/case',
                           "Capitalize the sentence: '{}{}{}'"
                           .format(trunc_topic, trunc_label, sentence))

        if not is_subject_line:
            continue

        if not trunc_sentence:
            yield ('error', 'msg',
                   'Must provide log message')

        elif not topic:
            yield ('warning', 'msg/topic',
                   "Missing topic / subsystem")

        if topic:
            if tc['brackets'] or tc['semi']:
                yield ('error' if tc['brackets'] else 'warning',
                       'msg/brackets',
                       "Use colons inside the topic: '{}{}{}'"
                       .format(topic, trunc_label, trunc_sentence))

            if tc['parens'] and tc['topic'][0].startswith(tc['parens'][0]):
                yield ('warning', 'msg/labels',
                       "Put labels after the topic: '{}{}{}'"
                       .format(trunc_topic, label, trunc_sentence))


def msg_subj(repo, commit, lines):
    if not lines:
        return

    empty_line_idx = lines.index('') if '' in lines else len(lines)
    subj_lines = lines[:empty_line_idx]
    body_lines = lines[empty_line_idx+1:]

    if not subj_lines:
        yield ('warning', 'msg/subj',
               'Put subject on the first line')
        return

    if len(subj_lines) > 1:
        yield ('warning', 'msg/subj-line',
               'Separate subject from body with a blank line')

    if any(END_PERIOD_RE.search(subj_lines[i])
           for i in (0, -1)[len(subj_lines)==1:]):
        yield ('warning', 'msg/subj-period',
               'Do not end the subject line with a period')


@checker
def check_msg(repo, commit):
    lines = [line.expandtabs().rstrip()
             for line in git_show(repo, commit).splitlines()]

    return itertools.chain(msg_subj(repo, commit, lines),
                           msg_regex(repo, commit, lines))

