import pygame
from assets import Board,ServerList,Go_particles
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

a=50
w=pygame.transform.smoothscale(pygame.image.load("images/White.png"),(a,a))
b=pygame.transform.smoothscale(pygame.image.load("images/black.png"),(a,a))
gp=Go_particles(w,b,(0,0),(W,0),10,20,lambda: print("white"),lambda: print("black"))


clock=pygame.time.Clock()
while running:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running=False
        if event.type==pygame.MOUSEBUTTONDOWN:
            pos=event.pos
            gp.add_particle(pos[0],pos[1],"White")
            gp.add_particle(pos[0],pos[1],"Black")
        # es.handle_event(event)
    screen.fill(0)
    gp.update()
    gp.draw(screen)
    # screen.blit(es.draw(),(0,0))
    pygame.display.flip()