import pygame
from assets import Board,ServerList
from app import game_setup_screen,loading_screen,game_screen
ratio=4/3
x=450
W=int(x*(1/ratio))
H=(x*ratio)

screen=pygame.display.set_mode((W, H))
running=True
padding=50

gs=game_screen(W,H)
gs.activate()
["SuperIdol","Samurai"]
gs.load_game("White",5,67,"SuperIdol",10,"nick eh","sigma",True)


clock=pygame.time.Clock()
while running:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running=False
        gs.handle_event(event)
    screen.fill(0)
    gs.update()
    screen.blit(gs.draw(),(0,0))
    pygame.display.flip()