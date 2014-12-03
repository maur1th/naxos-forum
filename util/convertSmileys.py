import re
from subprocess import call


f = open('FoRuM.html', 'rU')
text = f.read()

m = re.findall(
    r"<img src=\"FoRuM_files/([\d|\w]+.gif)[\s|\S]+?class=\"lien\">([\:|\;|\w|\d]+)",
    text)

for name, smiley in m:
    smiley = smiley.strip(":;")
    smiley = smiley if smiley or len(smiley) == 1 else name.strip(".gif")
    print("Moving", 'files/' + name, 'to',
          'files/' + str(smiley) + '.gif')
    call(['mv', 'files/' + name, 'files/' + str(smiley) + '.gif'])
