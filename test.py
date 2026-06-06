import pygame
from assets import Board,ServerList
from app import game_setup_screen
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
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running=False
        ss.handle_event(event)
    screen.fill(0)
    screen.blit(ss.draw(),(0,0))
    ss.update()
    pygame.display.flip()