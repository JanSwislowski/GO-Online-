import os
import pygame
import numpy as np


from assets import ComentSection
def generate_coment_section(comments: list[dict],width, height):
    c=ComentSection(width, height)
    for comment in comments:
        c.add_comment(user=comment["user"], text=comment["text"])
    return c


def fade_surfaces(surface1: pygame.Surface, surface2: pygame.Surface, ratio: float) -> pygame.Surface:
    ratio = max(0.0, min(1.0, ratio))

    arr1 = pygame.surfarray.array3d(surface1).astype(np.float32)
    arr2 = pygame.surfarray.array3d(surface2).astype(np.float32)

    blended = ((arr1 * (1.0 - ratio)) + (arr2 * ratio)).astype(np.uint8)

    return pygame.surfarray.make_surface(blended)
def darken_rgb(color, factor):
    r = max(0, min(255, int(color[0] * factor)))
    g = max(0, min(255, int(color[1] * factor)))
    b = max(0, min(255, int(color[2] * factor)))
    return (r, g, b)
def get_color_leaderboard(i):
    if i==0:
        color=(255,215,0) #gold
    elif i==1:
        color=(192,192,192) #silver
    elif i==2:
        color=(205,127,50) #bronze
    else:
        color=(100,100,100)
    return color

def scale_rect(rect:pygame.Rect,dx,dy,dw,dh):
    return pygame.Rect(rect.x-dx,rect.y-dy,rect.w+dw+dx,rect.h+dh+dy)
def normalise_scroll(scroll, content_height, view_height):
    if content_height <= view_height:
        return 0
    max_scroll = content_height - view_height
    return max(0, min(scroll, max_scroll))
def cords_to_str(cords):
    return f"N{cords[0][0]}°{cords[0][1]}',E{cords[1][0]}°{cords[1][1]}"
def scale_surface_proportionally(img, max_width, max_height):
    width, height = img.get_size()
    ratio = min(max_width / width, max_height / height)
    new_size = (int(width * ratio), int(height * ratio))
    return pygame.transform.smoothscale(img, new_size)

def create_gradient_numpy(width, height, direction='bottom',
                          color=(0, 0, 0), max_alpha=180, strength=1.0):
    """
    strength < 1.0  → gentle, slow buildup  (e.g. 0.5)
    strength = 1.0  → natural smootherstep
    strength > 1.0  → fast, aggressive fade that still merges cleanly (e.g. 2.0)
    """
    surface = pygame.Surface((width, height), pygame.SRCALPHA)

    size = height if direction in ('bottom', 'top') else width
    t = np.linspace(0.0, 1.0, size)

    if direction in ('top', 'left'):
        t = 1.0 - t

    # shift t by strength, then re-normalize to [0, 1] so it always
    # starts at 0 alpha and ends at max_alpha cleanly
    t_shaped = np.power(t, 1.0 / strength)   # bias the input
    t_smooth = t_shaped * t_shaped * t_shaped * (t_shaped * (t_shaped * 6 - 15) + 10)  # smootherstep

    gradient = (t_smooth * max_alpha).astype(np.uint8)

    arr = pygame.surfarray.pixels_alpha(surface)
    if direction in ('bottom', 'top'):
        arr[:] = gradient[np.newaxis, :]
    else:
        arr[:] = gradient[:, np.newaxis]
    del arr

    rgb_arr = pygame.surfarray.pixels3d(surface)
    rgb_arr[:] = color
    del rgb_arr
    return surface
def create_fade_mask(width, height, direction='right', strength=1.0):
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    surface.fill((255, 255, 255, 255))  # white, fully opaque — RGB won't affect MULT blend
    size = height if direction in ('top', 'bottom') else width

    t = np.linspace(0.0, 1.0, size)
    if direction in ('bottom', 'right'):
        t = 1.0 - t

    t = np.power(np.clip(t, 0, 1), 1.0 / strength)
    gradient = (t**3 * (t * (t * 6 - 15) + 10) * 255).astype(np.uint8)

    arr = pygame.surfarray.pixels_alpha(surface)
    arr[:] = gradient[np.newaxis, :] if direction in ('top', 'bottom') else gradient[:, np.newaxis]
    del arr

    return surface
def twodistance(cord1, cord2):
    lat1, lon1 = cord1
    lat2, lon2 = cord2
    return ((lat2 - lat1) ** 2 + (lon2 - lon1) ** 2) ** 0.5
def twodistance_sq(cord1, cord2):
    lat1, lon1 = cord1
    lat2, lon2 = cord2
    return (lat2 - lat1) ** 2 + (lon2 - lon1) ** 2
def alpha_surface(surface, alpha):
    new_surface = surface.copy()
    new_surface.fill((255, 255, 255, alpha), special_flags=pygame.BLEND_RGBA_MULT)
    return new_surface
dirs=[(0,1),(1,0),(0,-1),(-1,0)]
def dfs_go_board(board,x,y,vis,cur,group):
    if x<0 or x>=len(board) or y<0 or y>=len(board[0]) or vis[x][y]:
        return 0
    if board[x][y]==-1:
        return 1
    if board[x][y]!=cur:
        return 0
    group.append((x,y))
    vis[x][y]=True
    count=0
    for dx,dy in dirs:
        count+=dfs_go_board(board,x+dx,y+dy,vis,cur,group)
    return count
def check_legal_move(board,x,y,player):
    b=[row[:] for row in board]
    b[x][y]=player
    update_board(b,player)
    d=dfs_go_board(b,x,y,[[False for _ in range(len(board[0]))] for _ in range(len(board))],player,[])
    if d==0:
        return False
    return True

def update_board(board,player):
    vis=[[False for _ in range(len(board[0]))] for _ in range(len(board))]
    taken=[]
    player^=1
    for i in range(len(board)):
        for j in range(len(board[0])):
            if board[i][j]==player and not vis[i][j]:
                group=[]
                count=dfs_go_board(board,i,j,vis,board[i][j],group)
                if count==0:
                    for x,y in group:
                        board[x][y]=-1
                        taken.append((x,y))
    return taken

def dfs_score(board,x,y,vis,group):
    if x<0 or x>=len(board) or y<0 or y>=len(board[0]) or vis[x][y] or board[x][y]!=-1:
        return 0
    vis[x][y]=True
    count=1
    group.add((x,y))
    for dx,dy in dirs:
        count+=dfs_score(board,x+dx,y+dy,vis,group)
    return count
# 0,1 niczyje
# 2 białe
# 3 czarne

def dfs_ter(board,x,y,vis):
    if x<0 or x>=len(board) or y<0 or y>=len(board[0]) or vis[x][y]:
        return 0
    if board[x][y]==0:
        return 3
    if board[x][y]==1:
        return 2
    vis[x][y]=True
    cur=0
    for dx,dy in dirs:
        d=dfs_ter(board,x+dx,y+dy,vis)
        if d==0:
            continue
        if d==1:
            return 1
        if cur==0:
            cur=d
        elif cur!=d:
            return 1
    return cur
def check_vis(board,x,y,vis,vis2,vis3):
    if x<0 or x>=len(board) or y<0 or y>=len(board[0]) or vis3[x][y] or board[x][y]!=-1:
        return
    vis[x][y]=True
    vis2[x][y]=True
    vis3[x][y]=True
    for dx,dy in dirs:
        check_vis(board,x+dx,y+dy,vis,vis2,vis3)


def ch_score_board(board):
    score=0
    vis=[[False for _ in range(len(board[0]))] for _ in range(len(board))]
    vis2=[[False for _ in range(len(board[0]))] for _ in range(len(board))]
    white_ter=set([])
    black_ter=set([])
    for i in range(len(board)):
        for j in range(len(board[0])):
            if board[i][j]==-1 and not vis[i][j]:
                group=dfs_ter(board,i,j,vis)
                if group in (0,1):
                    check_vis(board,i,j,vis,vis2,[[False for _ in range(len(board[0]))] for _ in range(len(board))])
                    continue
                if group==2:
                    score-=dfs_score(board,i,j,vis2,white_ter)
                else:
                    score+=dfs_score(board,i,j,vis2,black_ter)
                check_vis(board,i,j,vis,vis2,[[False for _ in range(len(board[0]))] for _ in range(len(board))])
            elif board[i][j]==0:
                score+=1
            elif board[i][j]==1:
                score-=1
    return score,white_ter,black_ter
