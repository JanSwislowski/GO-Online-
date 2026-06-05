import pygame
from assets import Board,ServerList
from app import game_setup_screen
W=400
H=700
screen=pygame.display.set_mode((W, H))
running=True
padding=50
SL=ServerList(W-padding*2,H-padding*2,padding,padding)
SL.add_server("nigger")
SL.add_server("nigger")
SL.add_server("nigger")
SL.add_server("nigger")
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running=False
        SL.handle_event(event)
    screen.fill(0)
    screen.blit(SL.draw(),(padding,padding))
    pygame.display.flip()