import pygame.transform

from assets import TextBox, Button, Label,Icon,Picker,Slider,Board,ServerList,Picker2,SimpleButton,ScoreLabel,Pass_confirm
from functions import *
from setup import running,incoming_queue,outgoing_queue
import random

font=pygame.font.SysFont("TimesNewRoman", 20)
font_mid=pygame.font.SysFont("TimesNewRoman", 30)
font_mid_bold=pygame.font.SysFont("TimesNewRoman", 30,bold=True)

small=pygame.font.SysFont("TimesNewRoman", 18)
font_big=pygame.font.SysFont("TimesNewRoman", 40)
font_verybig=pygame.font.SysFont("TimesNewRoman", 50)
font_extremely_humongous=pygame.font.SysFont("TimesNewRoman", 65)
font_large = pygame.font.SysFont("Arial", 40, bold=True)
arial_mid=pygame.font.SysFont("Arial", 30, bold=True)
arial=pygame.font.SysFont("Arial", 33)
class ChooseScreen:
    def __init__(self,width, height,host_page,join_page):
        self.login=True
        self.active=False
        self.width = width
        self.height = height
        self.host_page=host_page
        self.join_page=join_page
        self.color=(200, 200, 200)
    def load(self):

        self.surface = pygame.surface.Surface((self.width, self.height))

        button_width = 200
        button_height = 50
        diff=45
        self.host_button = Button(self.width//2-button_width//2, self.height//2-diff, button_width, button_height, "Host",callback=self.host_page,pos_type="centery")
        self.join_button = Button(self.width//2-button_width//2, self.height//2+diff, button_width, button_height, "Join",callback=self.join_page,pos_type="centery")

    def close(self):
        #set all to None
        self.surface=None
        self.host_button=None
        self.join_button=None
        self.active=False

    def set_login(self):
        self.login=True
    def set_register(self):
        self.login=False
    def update(self):
        if not self.active:
            return

        self.host_button.update()
        self.join_button.update()

    def draw(self):
        self.surface.fill(self.color)

        self.host_button.draw(self.surface)
        self.join_button.draw(self.surface)


        return self.surface
    def activate(self):
        self.active=True

    def handle_event(self,event):
        if not self.active:
            return
        self.host_button.handle_event(event)
        self.join_button.handle_event(event)
class StartScreen:
    def __init__(self,width, height,next_page):
        self.width = width
        self.height = height
        self.next_page=next_page
        self.active=False
    def load(self):
        self.surface = pygame.surface.Surface((self.width, self.height))
        self.color=(200, 200, 200)

        button_width = 200
        button_height = 50
        self.name_text_box=TextBox(self.width//2-button_width//2, 200, button_width, button_height,placeholder="Name",max_length=20)
        self.start_button = Button(self.width//2-button_width//2, 320, button_width, button_height, "Start",callback=self.next_page)

        self.title=Label(self.width//2, 60, "GO", font=font_verybig,pos_type="center")

    def close(self):
        #set all to none
        self.surface=None
        self.start_button=None
        self.name_text_box=None
        self.title=None
    def update(self):
        if not self.active:
            return

        self.name_text_box.update()
        self.start_button.update()
    def draw(self):
        self.surface.fill(self.color)
        self.name_text_box.draw(self.surface)
        self.start_button.draw(self.surface)
        self.title.draw(self.surface)

        return self.surface
    def activate(self):
        self.active=True

    def handle_event(self,event):
        if not self.active:
            return
        self.name_text_box.handle_event(event)
        self.start_button.handle_event(event)



class game_setup_screen:
    def __init__(self,width, height,prev_page,next_page):
        self.h=height
        self.w=width
        self.color=(200, 200, 200)
        self.active=False
        self.next_page=next_page
        self.prev_page=prev_page
    def load(self):
        self.surface=pygame.surface.Surface((self.w, self.h))
        self.label=Label(self.w//2, 40, "Game Setup", font=font_verybig,pos_type="center")
        max_tiles=20
        dist=60
        y=120
        width=200
        self.tiles_slider=Slider(self.w//2-width//2, y, width, 20,min_val=2,max_val=max_tiles,
                                 initial=10,label="Tiles",show_value=True,text_color=(0,0,0),font=small)
        max_bias=40
        self.white_bias_slider=Slider(self.w//2-width//2, y+dist, width, 20,min_val=0,max_val=max_bias,
                                      initial=7.5,label="White Bias",show_value=True,value_format="{:.1f}",step=0.5,text_color=(0,0,0),font=small)

        self.black_bias_slider=Slider(self.w//2-width//2, y+dist*2, width, 20,min_val=0,max_val=max_bias,
                                      initial=0,label="Black Bias",show_value=True,value_format="{:.1f}",step=0.5,text_color=(0,0,0),font=small)

        color=(100,149,237)
        alpha=0.7
        w=280
        self.color_label=Label(self.w//2, y+dist*3, "Color:", font=font_mid,pos_type="center",color_text=(0,0,0))
        self.color_picker=Picker2(self.w//2, y+dist*3+24, w, 35,font, options=["Random","Black","White"],color=darken_rgb(color,alpha),chosen_color=color,text_color=(0,0,0))

        w=200
        self.rules=Label(self.w//2, y+dist*4+35, "Rules:", font=font_mid,pos_type="center")
        self.rule_picker=Picker2(self.w//2, y+dist*4+35+24, w, 35, options=["SuperIdol","Samurai"],font=font,color=darken_rgb(color,alpha),chosen_color=color,text_color=(0,0,0))

        h=45
        padding=20
        padding2=20
        w=140
        self.accept_button=Button(self.w-w-padding2,self.h-h-padding,w,h,"Accept",callback=self.next_page)
        self.back_button=Button(padding2,self.h-h-padding,w,h,"Back",callback=self.prev_page)
    def update(self):
        if not self.active:
            return
        self.rule_picker.update()
        self.accept_button.update()
        self.back_button.update()
        self.color_picker.update()
    def handle_event(self,event):
        if not self.active:
            return
        self.accept_button.handle_event(event)
        self.white_bias_slider.handle_event(event)
        self.black_bias_slider.handle_event(event)
        self.tiles_slider.handle_event(event)
        self.back_button.handle_event(event)
    def draw(self):
        self.surface.fill(self.color)
        self.label.draw(self.surface)
        self.tiles_slider.draw(self.surface)
        self.white_bias_slider.draw(self.surface)
        self.black_bias_slider.draw(self.surface)
        self.rules.draw(self.surface)
        self.rule_picker.draw(self.surface)
        self.accept_button.draw(self.surface)
        self.back_button.draw(self.surface)
        self.color_picker.draw(self.surface)
        self.color_label.draw(self.surface)
        return self.surface
    def close(self):
        #set all to None
        self.surface=None
        self.back_button=None
        self.accept_button=None
        self.rule_picker=None
        self.rules=None
        self.white_bias_slider=None
        self.black_bias_slider=None
        self.tiles_slider=None
        self.label=None
        self.color_picker=None
        self.color_label=None
    def activate(self):
        self.active=True

class game_screen:
    def __init__(self,width, height):
        self.color=(200, 200, 200)
        self.w=width
        self.h=height

        self.active=False
        self.color_game=None
        self.white_bias=None
        self.black_bias=None

        self.white_prisoners=0
        self.black_prisoners=0

        self.turn=""
        self.tiles=7
        self.loaded=False

    def load(self):
        self.surface=pygame.surface.Surface((self.w, self.h))


        y=115
        dur=200
        self.stone_y=y

        self.b_x=100
        self.w_x=290

        self.white_prisoners_label=ScoreLabel(self.w_x,y,font_large,(255,255,255),0,bump_duration_ms=dur,)
        self.black_prisoners_label=ScoreLabel(self.b_x,y,font_large,(0,0,0),0,bump_duration_ms=dur,)

        board_width=300
        board_height=300
        stone_r=0.33
        dy=30
        self.board=Board(self.w//2-board_width//2,self.h//2-board_height//2+dy,board_width,board_height,self.tiles,
                         self.tiles,stone_r,player=self.color_game,increase_black=lambda:self.black_prisoners_label.increase_by_one(),
                         increase_white=lambda:self.white_prisoners_label.increase_by_one(),rules="China" if self.rule=="SuperIdol" else "Japan")
        width=100
        height=50
        diff=30
        y=self.h-80
        # color=(100,149,237)

        color=(100,109,240)
        self.show_territory=SimpleButton(self.w//2+diff,y,width,height,color,"images/eye.png",5,call_back=lambda: self.switch_show_territory())
        self.pass_button=SimpleButton(self.w//2-diff-width,y,width,height,color,"images/pass.png",5,call_back=lambda: self.confirm_turn_pass())

        a=50
        self.black_stone=pygame.transform.smoothscale(pygame.image.load("images/black.png"),(a,a)).convert_alpha()
        self.white_stone=pygame.transform.smoothscale(pygame.image.load("images/white.png"),(a,a)).convert_alpha()

        paddingx=50
        paddingy=190
        self.pass_turn_window=Pass_confirm(self.w-paddingx*2,self.h-paddingy*2,paddingx,paddingy,lambda: self.pass_turn(),lambda:self.back_to_game())
        self.pass_turn_confirm=False

        self.dx=20+a

    def load_game(self,color,white_bias,black_bias,rule,tiles,player1,player2,hosting):
        self.tiles=tiles
        self.color_game=color
        self.white_bias=white_bias
        self.black_bias=black_bias
        self.rule=rule
        self.turn="Black"
        self.my_turn=self.color_game==self.turn
        self.load()
        print(f"Game loaded with color: {color}, white bias: {white_bias}, black bias: {black_bias}, rule: {rule}, tiles: {tiles}")
        self.loaded=True
        label_y=20
        self.inactive_player_color=(100,100,100)
        self.active_player_color=(0, 200, 0)
        self.player1_label=Label(self.w//4,label_y,player1,color_text=(0,0,0),font=arial,fade_in=True,pos_type="center")
        self.player2_label=Label(self.w//4*3,label_y,player2,color_text=(0,0,0),font=arial,fade_in=True,pos_type="center")
        self.hosting=hosting

        self.vs_label=Label(self.w//4*2,label_y,"vs",color_text=(0,0,0),font=arial_mid,pos_type="center")


        dx=33
        intervals=5
        y=80
        self.score_count_label=ScoreLabel(self.w//2+dx,y+2,font_mid,(0,0,0),0,anchor="center",count_interval_ms=intervals,)
        self.score_label=Label(self.w//2-dx,y,"Score:",color_text=(0,0,0),font=font_mid_bold ,pos_type="center")

        self.set_active_colors()
    def close(self):
        self.surface=None
        self.board=None
        self.active=False
        self.loaded=False
        self.pass_button=None
        self.show_territory=None
        self.white_prisoners_label=None
        self.black_stone=None
        self.white_stone=None
        self.black_prisoners_label=None
        self.player1_label =None
        self.player2_label =None
        self.vs_label=None
        self.score_label=None
        self.score_count_label=None
    def get_score(self):
        return self.score_count_label.score
    def move(self):
        self.turn="White" if self.turn=="Black" else "Black"
        self.my_turn=self.color_game==self.turn
        self.set_active_colors()
    def switch_show_territory(self):
        self.board.show_ter^=1
    def pass_turn(self):
        incoming_queue.put({"type":"pass turn"})
        self.board.prev_move=None
        self.move()
        self.back_to_game()
    def confirm_turn_pass(self):
        if self.my_turn:
            self.pass_turn_confirm=True
    def back_to_game(self):
        self.pass_turn_confirm=False
    def set_move(self,pos):
        self.move()
        self.board.set_move(pos)
    def set_pass(self):
        self.move()

    def set_active_colors(self):
        if self.hosting:
            if self.my_turn:
                self.player1_label.set_color(self.active_player_color)
                self.player2_label.set_color(self.inactive_player_color)
            else:
                self.player2_label.set_color(self.active_player_color)
                self.player1_label.set_color(self.inactive_player_color)
        else:
            if self.my_turn:
                self.player2_label.set_color(self.active_player_color)
                self.player1_label.set_color(self.inactive_player_color)
            else:
                self.player1_label.set_color(self.active_player_color)
                self.player2_label.set_color(self.inactive_player_color)

    def update(self):
        if not self.active or not self.loaded:
            return

        if self.pass_turn_confirm:
            return

        self.board.turn=self.my_turn
        self.white_prisoners_label.update()
        self.black_prisoners_label.update()


        self.score_count_label.set_score(self.board.get_score(self.white_bias,self.black_bias))
        self.score_count_label.update()


        move=self.board.update()
        if move:
            self.move()
            return move
    def handle_event(self,event):
        if not self.active:
            return
        if self.pass_turn_confirm:
            self.pass_turn_window.handle_event(event)
            return
        self.pass_button.handle_event(event)
        self.show_territory.handle_event(event)
        pass
    def draw(self):
        self.surface.fill((200, 200, 200))
        color=(186, 161, 124)
        h=50
        pygame.draw.rect(self.surface,color,(0,0,self.w,h))
        b=5
        color2=(117, 86, 39)
        pygame.draw.rect(self.surface,color2,(-b,-b,self.w+b*2,h+b),width=b)

        self.show_territory.draw(self.surface)
        self.pass_button.draw(self.surface)

        self.surface.blit(self.white_stone,(self.w_x-self.dx,self.stone_y))
        self.surface.blit(self.black_stone,(self.b_x-self.dx,self.stone_y))

        self.black_prisoners_label.draw(self.surface)
        self.white_prisoners_label.draw(self.surface)
        self.player1_label.draw(self.surface)
        self.player2_label.draw(self.surface)
        self.vs_label.draw(self.surface)

        self.score_label.draw(self.surface)
        self.score_count_label.draw(self.surface)

        self.board.draw(self.surface)

        if self.pass_turn_confirm:
            self.pass_turn_window.draw(self.surface)

        return self.surface
    def activate(self):
        self.active=True

class join_screen:
    def __init__(self,width, height,back_func,refresh_func):
        self.color=(200, 200, 200)
        self.w=width
        self.h=height
        self.active=False
        self.back_func=back_func
        self.refresh=refresh_func
    def load(self):
        self.surface=pygame.surface.Surface((self.w, self.h))
        padding_x=50
        padding_y=20
        h=50
        padding=10
        self.list=ServerList(self.w-padding_x*2,self.h-padding_y*2-h-padding,padding_x,padding_y)

        button_w=130
        color=(100,149,237)
        padding_y=10
        padding_x=20
        self.refresh_button=SimpleButton(self.w-button_w-padding_x,self.h-padding_y-h,button_w,h,color,"images/refresh.png",5,call_back=self.refresh)
        self.back_button=SimpleButton(padding_x,self.h-padding_y-h,button_w,h,color,"images/exit.png",5,call_back=self.back_func)

    def close(self):
        self.surface=None
        self.list=None
        self.active=False
        self.refresh_button=None
        self.refresh_button=None
    def update(self):
        if not self.active:
            return
    def handle_event(self,event):
        if not self.active:
            return
        self.list.handle_event(event)
        self.refresh_button.handle_event(event)
        self.back_button.handle_event(event)
    def draw(self):
        self.surface.fill((200, 200, 200))
        self.list.draw(self.surface)
        self.refresh_button.draw(self.surface)
        self.back_button.draw(self.surface)
        return self.surface
    def activate(self):
        self.active=True
    def add_server(self,name,join_callback,room_id):
        self.list.add_server(name,join_callback,room_id)
    def clear(self):
        self.list.clear_servers()
class loading_screen:
    def __init__(self,width,height):
        self.color=(200, 200, 200)
        self.width=width
        self.height=height
        self.alpha=150
        self.active=False
        self.surface=pygame.surface.Surface((self.width, self.height), pygame.SRCALPHA)
        a=100
        self.img=pygame.transform.smoothscale(pygame.image.load("images/jingjang.png"),(a,a))
        self.da=8
    def load(self,text,prev_surface):
        dy=120
        self.label=Label(self.width//2, self.height//2-dy, text, font=font_extremely_humongous,pos_type="center",color_text=(255,255,255))
        self.bg = prev_surface.copy()
        dark_overlay = pygame.Surface(self.bg.get_size(), pygame.SRCALPHA)
        dark_overlay.fill((0, 0, 0, self.alpha))
        self.bg.blit(dark_overlay, (0, 0))
        self.angle=0
    def close(self):
        self.label=None
        self.bg=None
        self.angle=0
    def update(self):
        self.angle+=self.da
        self.angle%=360
    def draw(self):
        self.surface.fill((0,0,0,0))
        self.surface.blit(self.bg,(0,0))

        rotated_img=pygame.transform.rotate(self.img,self.angle)
        rect=rotated_img.get_rect(center=(self.width//2,self.height//2+50))

        self.surface.blit(rotated_img,rect)
        self.label.draw(self.surface)
        return self.surface
    def activate(self):
        pass
    def handle_event(self,event):
        pass


class end_game_screen:
    def __init__(self,width,height,home_page):
        self.color=(200, 200, 200)
        self.width=width
        self.height=height
        self.alpha=150
        self.active=False

        padding_x=30
        padding_y=50
        self.rect=pygame.Rect(padding_x,padding_y,width-2*padding_x,height-2*padding_y)
        self.home_func=home_page

    def load(self,text,prev_surface,score):
        self.surface=pygame.surface.Surface((self.width, self.height), pygame.SRCALPHA).convert_alpha()

        dy=200
        self.label=Label(self.width//2, self.height//2-dy, text, font=font_extremely_humongous,pos_type="center",color_text=(0,0,0))
        self.point_label=Label(self.width//2, self.height//2-dy+100, "Punktacja:", font=font_big,pos_type="center",color_text=(0,0,0))
        self.score_label=Label(self.width//2, self.height//2-dy+150, f"{score}", font=font_big,pos_type="center",color_text=(0,0,0))

        button_w=200
        h=50
        color=(100,149,237)
        self.home_button=SimpleButton(self.width//2-button_w//2,self.rect.bottom-h-20,button_w,h,color,"images/exit.png",5,self.home_func)


        bg = prev_surface.copy()
        dark_overlay = pygame.Surface(bg.get_size(), pygame.SRCALPHA)
        dark_overlay.fill((0, 0, 0, self.alpha))
        bg.blit(dark_overlay, (0, 0))
        self.surface.blit(bg,(0,0))

        self.surface=self.surface.convert_alpha()




    def close(self):
        self.label=None
        self.surface=None
        self.label=None
        self.point=None
        self.score=None
        self.home_=None

    def update(self):
        pass
    def draw(self):
        color=(186, 161, 124)
        color2=(117, 86, 39)
        r=20
        w=5
        pygame.draw.rect(self.surface,color,self.rect,border_radius=r)
        pygame.draw.rect(self.surface,color2,self.rect,border_radius=r,width=w)
        self.label.draw(self.surface)
        self.point_label.draw(self.surface)
        self.score_label.draw(self.surface)
        self.home_button.draw(self.surface)

        return self.surface
    def activate(self):
        self.active=True
    def handle_event(self,event):
        if not self.active:
            return
        self.home_button.handle_event(event)
from mouse import mouse
class App:
    def __init__(self):



        ratio=4/3
        x=450
        W=int(x*(1/ratio))
        H=(x*ratio)
        self.width = W
        self.height = H
        self.screen=pygame.display.set_mode((self.width, self.height),
    pygame.SCALED | pygame.FULLSCREEN)

        self.pages={
                "start": StartScreen(self.width, self.height,lambda: self.switch_page("load")),
                "choose": ChooseScreen(self.width, self.height,lambda: self.switch_page("host"),lambda: self.switch_page("join")),
                "host": game_setup_screen(self.width, self.height,lambda: self.switch_page("choose"),lambda: self.switch_page("load")),
                "game": game_screen(self.width, self.height),
                "join": join_screen(self.width, self.height,back_func=lambda:self.switch_page("choose"),refresh_func=lambda: self.refresh_join()),
                "load": loading_screen(self.width, self.height),
                "end game":end_game_screen(self.width,self.height,lambda: self.switch_page("choose"))
        }


        self.next_page=None

        self.start_fade=None
        self.fade_duration=500
        self.fade_out=False
        self.prev_surface=None
        self.next_surface=None

        self.token=-1
        self.room_id=-1
        self.username=-1

        self.host_wait=False

        self.first_poll_game=True
    def get_surfaces_to_fade(self,prev_page,next_page,reverse=False):
        surface1=pygame.surface.Surface((self.width, self.height))
        surface2=pygame.surface.Surface((self.width, self.height))
        surface1.blit(self.pages[prev_page].draw(),(0,0))
        surface2.fill(self.pages[next_page].color)

        if reverse:
            self.prev_surface,self.next_surface=surface2, surface1
            return
        self.prev_surface, self.next_surface= surface1, surface2

    def handle_networking_out(self,page_name):
        if page_name=="load" and self.current_page=="host":
            outgoing_queue.put({"type": "create room", "token": self.token,})
            self.host_wait=True
        if page_name=="join":
            outgoing_queue.put({"type": "get rooms", "token": self.token})
        if self.current_page=="start":
            username=self.pages["start"].name_text_box.get_text().strip()
            if username=="":
                username=random.choice(["TuffBoi67","Nilly Oigga","GOść","MamMałego","Jeff","John Pork","SixSeven","Mirosław","Respect"])
            outgoing_queue.put({"type": "login","username": username})
    def host_game(self,player1,player2):
        host_color = self.pages["host"].color_picker.get_selected()
        tiles=self.pages["host"].tiles_slider.value
        white_bias=self.pages["host"].white_bias_slider.value
        black_bias=self.pages["host"].black_bias_slider.value
        rule=self.pages["host"].rule_picker.get_selected()
        if host_color == "Random":
            host_color = random.choice(["Black", "White"])
            print(host_color)
        outgoing_queue.put({"type": "start game", "token": self.token, "room_id": self.room_id,
                            "host_color": host_color,
                            "settings": {
                                "tiles": tiles,
                                "white_bias": white_bias,
                                "black_bias": black_bias,
                                "rule": rule,
                            }
        })
        self.pages["game"].load_game(tiles=tiles,white_bias=white_bias,black_bias=black_bias,rule=rule,color=host_color,player1=player1,player2=player2,hosting=True)
    def join_room(self,room_id):
        outgoing_queue.put({"type": "join room", "token": self.token, "room_id": room_id})
    def server_event_handler(self,event):
        if event["type"]=="logged_in":
            self.token=event["token"]
            self.switch_page("choose")
        elif event["type"]=="room_created":
            self.room_id=event["room_id"]
            outgoing_queue.put({"type": "poll host room", "token": self.token, "room_id": self.room_id})
        elif event["type"]=="rooms_list":
            for room_id, info in event["rooms"].items():
                self.pages["join"].add_server(f"{info['host']}",lambda: self.join_room(room_id),room_id)

        elif event["type"]=="join_room_response":
            if event["response"]["status"]=="ok":
                self.room_id=event["response"]["roomid"]
                outgoing_queue.put({"type": "poll start game", "token": self.token, "room_id": self.room_id})


        elif event["type"]=="poll_host_response":

            if event["player2_joined"]:
                self.host_game(event["player1"],event["player2"])
            else:
                outgoing_queue.put({"type": "poll host room", "token": self.token, "room_id": self.room_id})

        elif event["type"]=="start_game_response":
            if event["success"]:
                self.host_wait=False
                self.switch_page("game")

        elif event["type"]=="poll_start_game_response":
            if event["response"]["status"]=="ok":
                self.pages["game"].load_game(tiles=event["response"]["settings"]["tiles"],
                                        white_bias=event["response"]["settings"]["white_bias"],
                                        black_bias=event["response"]["settings"]["black_bias"],
                                        rule=event["response"]["settings"]["rule"],
                                        color=event["response"]["p2 color"],player1=event["response"]["player1"],
                                        player2=event["response"]["player2"],hosting=False)
                self.switch_page("game")
            else:
                outgoing_queue.put({"type": "poll start game", "token": self.token, "room_id": self.room_id})
        elif event["type"]=="make_move_response":
            if not event["success"]:
                print("Move failed")
        elif event["type"]=="poll_move_response":
            if event["move"]:
                self.pages["game"].set_move(event["move"])
            elif event["pass"]:
                print("enemy pass")
                self.pages["game"].set_pass()
            else:
                print("Polling move...")
                outgoing_queue.put({"type": "poll move", "token": self.token, "room_id": self.room_id, "color": self.pages["game"].color_game})
        elif event["type"]=="pass turn":
            outgoing_queue.put({"type":"pass turn", "token": self.token, "gameid": self.room_id})
        elif event["type"]=="make pass response":
            if not event["success"]:
                print("pass failed")
        elif event["type"]=="game_finished":
            self.end_game()
            print("finishing game")
    def refresh_join(self):
        self.pages["join"].clear()
        outgoing_queue.put({"type": "get rooms", "token": self.token})
    def end_game(self):
        score=self.pages["game"].get_score()
        if score>0 and self.pages["game"].color_game=="Black":
            txt="Wygrana!"
        elif score<0 and  self.pages["game"].color_game=="White":
            txt="Wygrana!"
        else:
            txt="Porażka"
        self.pages["end game"].load(txt,self.pages[self.current_page].draw(),score)
        self.switch_page("end game")
    def handle_networking_in(self):
        if self.start_fade is not None:
            return
        while not incoming_queue.empty():
            event = incoming_queue.get()
            self.server_event_handler(event)
    def switch_page(self,page_name):

        if page_name not in self.pages:
            return
        if page_name=="load":
            if self.current_page =="host":
                txt="Waiting..."
            else:
                txt="Loading"
            self.pages["load"].load(txt,self.pages[self.current_page].draw(),)
        elif page_name=="end game":
            self.first_poll_game=True
        else: self.pages[page_name].load()

        self.handle_networking_out(page_name)

        self.start_fade=pygame.time.get_ticks()
        self.get_surfaces_to_fade(self.current_page,page_name)

        self.next_page=page_name
    def update_fade(self):
        t = pygame.time.get_ticks() - self.start_fade
        if (not self.fade_out) and t > self.fade_duration // 2:
            print("Fading out...")
            self.get_surfaces_to_fade(self.next_page,self.next_page,reverse=True)
            self.fade_out=True
        if pygame.time.get_ticks() - self.start_fade >= self.fade_duration:
            if self.current_page not in ["host"]:
                self.pages[self.current_page].close()
            self.start_fade = None
            self.current_page = self.next_page
            self.prev_surface = None
            self.next_surface = None
            self.pages[self.current_page].activate()
            self.fade_out = False
    def update_game(self):
        move=self.pages["game"].update()
        if move:
            print(f"Move made: {move}")
            outgoing_queue.put({"type": "make move", "token": self.token, "room_id": self.room_id, "move": move})

        if self.pages["game"].my_turn==False:
            if not self.first_poll_game:
                return
            self.first_poll_game=False
            move=outgoing_queue.put({"type": "poll move", "token": self.token, "room_id": self.room_id, "color": self.pages["game"].color_game})
            print("Polling move...")
            if move:
                self.pages["game"].set_move(move)
        else:
            self.first_poll_game=True



    def update(self):
        if self.start_fade is not None:
            self.update_fade()
            return
        if self.current_page=="game" and not self.host_wait:
            self.update_game()
        else:
            self.pages[self.current_page].update()


    def draw(self,surface):
        if self.start_fade is not None:
            if not self.fade_out: ratio=(pygame.time.get_ticks()-self.start_fade)*2/(self.fade_duration)
            else: ratio=(pygame.time.get_ticks()-self.start_fade)*2/(self.fade_duration)-1
            surface.blit(fade_surfaces(self.prev_surface,self.next_surface,ratio),(0,0))
            return
        surface.blit(self.pages[self.current_page].draw(),(0,0))

    def run(self):
        global running
        clock=pygame.time.Clock()
        self.current_page="start"
        self.pages[self.current_page].activate()
        self.pages[self.current_page].load()
        fps=60
        while running:
            clock.tick(fps)
            keys=pygame.key.get_pressed()
            self.update()
            self.handle_networking_in()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                self.pages[self.current_page].handle_event(event)

            if keys[pygame.K_ESCAPE]:
                running=False

            self.draw(self.screen)
            pygame.display.flip()
        pygame.quit()