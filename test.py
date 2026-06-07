import pygame
from assets import Board,ServerList
from app import game_setup_screen,loading_screen,game_screen,end_game_screen
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

es=end_game_screen(W,H)
es.load("Porażka!",gs.draw(),67,lambda: print("clicked"))
es.activate()
clock=pygame.time.Clock()
while running:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running=False
        es.handle_event(event)
    screen.fill(0)
    es.update()
    screen.blit(es.draw(),(0,0))
    pygame.display.flip()