import pygame
from assets import Board,ServerList
from app import game_setup_screen,loading_screen
ratio=4/3
x=450
W=int(x*(1/ratio))
H=(x*ratio)
print(W/H,9/16)
screen=pygame.display.set_mode((W, H))
running=True
padding=50
ss=game_setup_screen(W,H,lambda: print("test"),lambda: print("test"))
ss.load()
ss.active=True
ls=loading_screen(W,H)
ls.load("loading",ss.draw())
clock=pygame.time.Clock()
while running:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running=False
        # ls.handle_event(event)
    screen.fill(0)
    screen.blit(ls.draw(),(0,0))
    ls.update()
    pygame.display.flip()