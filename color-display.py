import pygcurse
import pygame

colornames = {}
for cname, colortuple in pygame.colordict.THECOLORS.items():
    colornames[cname] = pygame.Color(*colortuple)

screen = pygcurse.PygcurseWindow(150, 51)
screen._autoupdate = False
screen.font = pygame.font.Font('assets/clacon.ttf', 24)

colors = colornames.keys()
colors.sort()

x = 0
y = 1
for name in colors:
    screen.write(name, x=x, y=y, fgcolor=name)
    y += 1
    if y % 50 == 0:
        x += 10
        y = 0

screen.update()
pygcurse.waitforkeypress()