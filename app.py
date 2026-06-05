from assets import TextBox, Button, Label,Icon,Picker,Slider,Board,ServerList
from functions import *
from setup import running,incoming_queue,outgoing_queue


font=pygame.font.SysFont("TimesNewRoman", 24)
small=pygame.font.SysFont("TimesNewRoman", 18)
font_verybig=pygame.font.SysFont("TimesNewRoman", 60)
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
        self.host_button = Button(100, self.height//2-diff, button_width, button_height, "Host",callback=self.host_page,pos_type="centery")
        self.join_button = Button(100, self.height//2+diff, button_width, button_height, "Join",callback=self.join_page,pos_type="centery")

    def close(self):
        #set all to None
        self.surface=None
        self.host_button=None
        self.join_button=None

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
        self.name_text_box=TextBox(100, 200, button_width, button_height,placeholder="Name",max_length=20)
        self.start_button = Button(100, 320, button_width, button_height, "Start",callback=self.next_page)

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
        self.label=Label(self.w//2, 50, "Game Setup", font=font_verybig,pos_type="center")
        max_tiles=20
        dist=60
        y=150
        x=100
        self.tiles_slider=Slider(x, y, 200, 20,min_val=2,max_val=max_tiles,
                                 initial=10,label="Tiles",show_value=True,text_color=(0,0,0),font=small)
        max_bias=40
        self.white_bias_slider=Slider(x, y+dist, 200, 20,min_val=0,max_val=max_bias,
                                      initial=7.5,label="White Bias",show_value=True,value_format="{:.1f}",step=0.5,text_color=(0,0,0),font=small)

        self.black_bias_slider=Slider(x, y+dist*2, 200, 20,min_val=0,max_val=max_bias,
                                      initial=0,label="Black Bias",show_value=True,value_format="{:.1f}",step=0.5,text_color=(0,0,0),font=small)
        self.rules=Label(self.w//2, y+dist*3+40, "Rules:", font_size=30,pos_type="center")
        self.rule_picker=Picker(100, y+dist*4+10, 200, 30, options=["SuperIdol","Samurai"],font=font)
        h=50
        padding=50
        padding2=30
        w=160
        self.accept_button=Button(self.w-w-padding2,self.h-h-padding,w,h,"Accept",callback=self.next_page)
        self.back_button=Button(padding2,self.h-h-padding,w,h,"Back",callback=self.prev_page)
    def update(self):
        if not self.active:
            return
        self.rule_picker.update()
        self.accept_button.update()
        self.back_button.update()
    def handle_event(self,event):
        if not self.active:
            return
        self.rule_picker.handle_event(event)
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
    def activate(self):
        self.active=True

class game_screen:
    def __init__(self,width, height):
        self.color=(200, 200, 200)
        self.w=width
        self.h=height
        self.active=False
    def load(self,tiles,white_bias,black_bias,rule):
        self.surface=pygame.surface.Surface((self.w, self.h))
        board_width=300
        board_height=300
        stone_r=0.33
        self.board=Board(self.w//2-board_width//2,self.h//2-board_height//2,board_width,board_height,tiles,tiles,stone_r)
    def close(self):
        self.surface=None
        self.board=None
        self.active=False
    def update(self):
        if not self.active:
            return
        self.board.update()
    def handle_event(self,event):
        if not self.active:
            return
        pass
    def draw(self):
        self.surface.fill((200, 200, 200))
        self.board.draw(self.surface)
        return self.surface
    def activate(self):
        self.active=True

class join_screen:
    def __init__(self,width, height):
        self.color=(200, 200, 200)
        self.w=width
        self.h=height
        self.active=False
    def load(self):
        self.surface=pygame.surface.Surface((self.w, self.h))
        padding_x=50
        padding_y=20
        self.list=ServerList(self.w-padding_x*2,self.h-padding_y*2,padding_x,padding_y)
    def close(self):
        self.surface=None
        self.list=None
        self.active=False
    def update(self):
        if not self.active:
            return
    def handle_event(self,event):
        if not self.active:
            return
        self.list.handle_event(event)
    def draw(self):
        self.surface.fill((200, 200, 200))
        self.list.draw(self.surface)
        return self.surface
    def activate(self):
        self.active=True
    def add_server(self,name):
        self.list.add_server(name)
class App:
    def __init__(self):
        pygame.init()
        self.width = 400
        self.height = 600
        self.screen=pygame.display.set_mode((self.width, self.height))

        self.pages={
                "start": StartScreen(self.width, self.height,lambda: self.switch_page("choose")),
                "choose": ChooseScreen(self.width, self.height,lambda: self.switch_page("host"),lambda: self.switch_page("join")),
                "host": game_setup_screen(self.width, self.height,lambda: self.switch_page("choose"),lambda: self.switch_page("game")),
                "game": game_screen(self.width, self.height),
                "join": join_screen(self.width, self.height)
        }


        functions=[lambda: self.switch_page("profile"),lambda: self.switch_page("feed"),lambda: self.switch_page("battle"),lambda: print("add")]
        self.next_page=None

        self.start_fade=None
        self.fade_duration=500
        self.fade_out=False
        self.prev_surface=None
        self.next_surface=None

        self.token=-1
        self.room_id=-1
        self.username=-1
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
        if page_name=="game" and self.current_page=="host":
            outgoing_queue.put({"type": "create room", "token": self.token})
        if page_name=="join":
            outgoing_queue.put({"type": "get rooms", "token": self.token})
        if page_name=="choose":
            outgoing_queue.put({"type": "login","username": self.pages["start"].name_text_box.get_text()})

    def server_event_handler(self,event):
        if event["type"]=="logged_in":
            self.token=event["token"]
        elif event["type"]=="room_created":
            self.room_id=event["room_id"]
        elif event["type"]=="rooms_list":
            for room_id, info in event["rooms"].items():
                self.pages["join"].add_server(f"{room_id}: {info['host']}")
        elif event["type"]=="join_room_response":
            if event["response"]["status"]=="ok":
                self.room_id=event["response"]["roomid"]
                self.switch_page("game")
    def handle_networking_in(self):
        while not incoming_queue.empty():
            event = incoming_queue.get()
            self.server_event_handler(event)
    def switch_page(self,page_name):

        if page_name not in self.pages:
            return
        if page_name=="game":
            self.pages[page_name].load(tiles=self.pages["host"].tiles_slider.value,white_bias=self.pages["host"].white_bias_slider.value,black_bias=self.pages["host"].black_bias_slider.value,rule=self.pages["host"].rule_picker.get_selected())
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
            self.pages[self.current_page].close()
            self.start_fade = None
            self.current_page = self.next_page
            self.prev_surface = None
            self.next_surface = None
            self.pages[self.current_page].activate()
            self.fade_out = False
    def update(self):
        if self.start_fade is not None:
            self.update_fade()
            return
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
            self.handle_networking_in()
            self.update()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                self.pages[self.current_page].handle_event(event)

            if keys[pygame.K_ESCAPE]:
                running=False

            self.draw(self.screen)
            pygame.display.flip()
        pygame.quit()