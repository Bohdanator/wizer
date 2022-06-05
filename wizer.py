import tkinter as tk
import tkinter.font as tkfont
from PIL import Image, ImageTk, ImageDraw
from math import floor

_log = []
ind = 0

zoom = 100
cam_x = -100
cam_y = -100
point_r = 5
call_x = 30
call_y = 30
call_tab = 50
font_height = 20
height = 1080
width = 1920
entities = []
mouse_x = 0
mouse_y = 0
entities = []
images = []

root = tk.Tk()
root.title('Wizer')
font = tkfont.Font(
    root=root,
    family="Times",
    size=-font_height,
    weight=tkfont.BOLD,
    slant=tkfont.ROMAN,
)

def computed_x(x):
    cx = float(str(x))
    return floor(zoom*cx - cam_x)

def computed_y(y):
    cy = float(str(y))
    return floor(height - (zoom*cy - cam_y))

def computed_coordinates(x, y):
    return computed_x(x), computed_y(y)

def extract_image_dimensions(xy):
    xs = list(map(lambda x: x[0], xy))
    ys = list(map(lambda x: x[1], xy))
    minx = min(xs)
    maxx = max(xs)
    miny = min(ys)
    maxy = max(ys)
    return (minx, maxx, miny, maxy)

def prepare_kwargs(kwargs: dict):
    kw = {}
    kw['fill'] = kwargs.get('fill', (255, 255, 255, 32))
    kw['outline'] = kwargs.get('outline', (255, 255, 255, 255))
    kw['width'] = kwargs.get('width', floor(zoom/10))
    return kw

def create_transparent_polygon(canvas: tk.Canvas, xy, **kwargs):
    minx, maxx, miny, maxy = extract_image_dimensions(xy)
    im = Image.new('RGBA', (maxx - minx, maxy - miny), (255, 255, 255, 0))
    d = ImageDraw.Draw(im)
    nxy = list(map(lambda x: (x[0] - minx, x[1] - miny), xy))
    d.polygon(nxy, **prepare_kwargs(kwargs))
    image = ImageTk.PhotoImage(im)
    images.append(image)
    return canvas.create_image(minx, miny, image=image, anchor='nw')

def create_transparent_segment(canvas: tk.Canvas, xy, **kwargs):
    minx, maxx, miny, maxy = extract_image_dimensions(xy)
    nxy = list(map(lambda x: (x[0] - minx, x[1] - miny), xy))
    im = Image.new('RGBA', (maxx - minx, maxy - miny), (255, 255, 255, 0))
    d = ImageDraw.Draw(im)
    kw = prepare_kwargs(kwargs)
    kw.pop('outline')
    d.line(nxy, **kw)
    image = ImageTk.PhotoImage(im)
    images.append(image)
    return canvas.create_image(minx, miny, image=image, anchor='nw')

def create_transparent_point(canvas: tk.Canvas, xy, **kwargs):
    minx, maxx, miny, maxy = extract_image_dimensions(xy)
    nxy = list(map(lambda x: (x[0] - minx, x[1] - miny), xy))
    im = Image.new('RGBA', (maxx - minx, maxy - miny), (255, 255, 255, 0))
    d = ImageDraw.Draw(im)
    kw = prepare_kwargs(kwargs)
    kw.pop('outline')
    d.arc(nxy, start=0, end=360, **kw)
    image = ImageTk.PhotoImage(im)
    images.append(image)
    return canvas.create_image(minx, miny, image=image, anchor='nw')

def draw_point(canvas: tk.Canvas, rep, **kwargs):
    cx, cy = computed_coordinates(*rep)
    kwargs['fill'] = (*root.winfo_rgb(kwargs.pop('color', 'black')), 192)
    kwargs['outline'] = ""
    w = floor(kwargs['width'])
    return create_transparent_point(canvas, [(cx - w, cy - w), (cx + w, cy + w)], **kwargs)

def draw_segment(canvas:tk.Canvas, rep, **kwargs):
    s, t = rep
    sx, sy = computed_coordinates(*s)
    tx, ty = computed_coordinates(*t)
    kwargs['fill'] = (*root.winfo_rgb(kwargs.pop('color', 'black')), 192)
    return create_transparent_segment(canvas, [(sx, sy), (tx, ty)], **kwargs)

def draw_polygon(canvas: tk.Canvas, rep, **kwargs):
    coords = list(map(lambda x: tuple(computed_coordinates(*x)), rep))
    color = kwargs.pop('color', 'black')
    kwargs['outline'] = (*root.winfo_rgb(color), 192)
    kwargs['fill'] = (*root.winfo_rgb(color), 32)
    return create_transparent_polygon(canvas, coords, **kwargs)

def draw_call(canvas: tk.Canvas, origin, call, args=[], kwargs={}, result=None):
    def draw_text(text='', dx=0, color='black'):
        canvas.create_text(call_x + dx, draw_text.y, font=font, fill=color, anchor='nw', text=text)
        draw_text.y += call_y
    draw_text.y = call_y

    draw_text(text=f'{origin}', color='red')
    draw_text(text=f'.{call}', color='red')
    if len(args) > 0:
        draw_text(text='args')
        for (i, arg) in enumerate(args):
            draw_text(str(arg), call_x/2)
    if len(kwargs) > 0:
        draw_text(text='kwargs')
        for (i, arg) in enumerate(kwargs):
            draw_text(str(arg), call_x/2)
    if result is not None:
        draw_text(str(result))

default_colors = {'point': 'black', 'segment': 'black', 'polygon': 'black'}
def draw_entity(canvas: tk.Canvas, t, rep, **kwargs):
    global entities
    kwargs['width'] = floor(zoom/10)
    kwargs.setdefault('color', default_colors[t])
    if t == 'point':
        entities.append(draw_point(canvas, rep, **kwargs))
    elif t == 'segment':
        entities.append(draw_segment(canvas, rep, **kwargs))
    elif t == 'polygon':
        entities.append(draw_polygon(canvas, rep, **kwargs))
    else:
        raise KeyError(f'Type {t} not supported.')


def draw_frame(canvas: tk.Canvas, entry):
    global entities, images
    canvas.delete("all")
    originator_key, call, args, kwargs, result, affected, state, call_type = entry
    entities = []
    images = []
    affected_color = 'red' if call_type == 'return' else '#FFBF00'
    for key in state:
        if key == originator_key or key in affected or key == result:
            continue
        t, rep = state[key]
        draw_entity(canvas, t, rep)
    if originator_key in state:
        ot, orep = state[originator_key]
        draw_entity(canvas, ot, orep, color="blue", width=20)
    try:
        if result in state:
            rt, rrep = state[result]
            draw_entity(canvas, rt, rrep, color="green", width=20)
    except TypeError as e:
        pass
    for key in affected:
        if key == originator_key or key == result:
            continue
        at, arep = state[key]
        draw_entity(canvas, at, arep, color=affected_color)
    if originator_key == '___call':
        draw_call(canvas, f'function call ({call_type})', call, args, kwargs, result)
    else:
        draw_call(canvas, state[originator_key], call, args, kwargs, result)


cvs = tk.Canvas(
    root,
    background="white",
    height=height,
    width=width,
)
cvs.pack()
def handle_right(event): 
    global ind
    ind = min(ind + 1, len(_log)-1)
    draw_frame(cvs, _log[ind])

def handle_left(event): 
    global ind
    ind = max(ind - 1, 0)
    draw_frame(cvs, _log[ind])

def handle_mouse_wheel(event):
    global zoom
    if event.num == 5 or event.delta == -120:
        zoom = max(20, zoom - 10)
    elif event.num == 4 or event.delta == 120:
        zoom += 10
    draw_frame(cvs, _log[ind])

def handle_mouse_move(clicked):
    def callback(event):
        global mouse_x, mouse_y, cam_x, cam_y, entities
        dx = (mouse_x - event.x)
        dy = (mouse_y - event.y)
        if clicked:
            cam_x += dx
            cam_y -= dy
            for e in entities:
                cvs.move(e, -dx, -dy)
        mouse_x = event.x
        mouse_y = event.y
    return callback

def change_zoom(d):
    global zoom
    zoom = max(20, zoom + d)
    draw_frame(cvs, _log[ind])

root.bind("<Key-d>", handle_right)
root.bind("<Key-a>", handle_left)
root.bind("<Key-Right>", handle_right)
root.bind("<Key-Left>", handle_left)
root.bind('<Control-Button-4>', handle_mouse_wheel)
root.bind('<Control-Button-5>', handle_mouse_wheel)
root.bind('<B1-Motion>', handle_mouse_move(True))
root.bind('<Motion>', handle_mouse_move(False))
root.bind('<Key-Up>', lambda event: change_zoom(10))
root.bind('<Key-Down>', lambda event: change_zoom(-10))

def visualize(log):
    global _log
    _log = log
    draw_frame(cvs, _log[ind])
    tk.mainloop()
