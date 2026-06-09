class Mouse:
    def __init__(self):
        self.pos=(0,0)
        self.pressed=(0,0,0)
    def update_pos(self,pos):
        self.pos=pos
    def update_pressed(self,pressed):
        self.pressed=pressed
mouse=Mouse