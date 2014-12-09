from subprocess import call, getoutput
from tempfile import TemporaryDirectory


xmas_dir = "../naxos/static/img/xmas/smileys/"
smileys_dir = "../naxos/static/img/smileys/"
xmas_sm = getoutput('ls ' + xmas_dir).split("\n")
regular_sm = getoutput('ls ' + smileys_dir).split("\n")

for sm in xmas_sm:
    if sm not in regular_sm:
        raise FileNotFoundError(sm)

with TemporaryDirectory() as tmp:
    for sm in xmas_sm:
        call(["mv", smileys_dir+sm, tmp])
        call(["mv", xmas_dir+sm, smileys_dir])
        call(["mv", tmp+'/'+sm, xmas_dir])
