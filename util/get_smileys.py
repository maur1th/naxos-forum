import re
from subprocess import getoutput


f = open('small-panel.txt', 'r')
smileys_in_use = [line[:-1] for line in f]
all_smileys = re.findall(r"[\S]+.gif", getoutput(['ls']))

smileys_not_used = list()
for smiley in all_smileys:
    if smiley not in smileys_in_use:
        smileys_not_used.append(
            ("<span class=\"fake-link\"><img class=\"smiley\""
             "src=\"/static/img/smileys/{:s}\" alt=\":{:s}:\">"
             "</span>").format(smiley, smiley[:-4])
        )

print("\n".join([html for html in smileys_not_used]))
