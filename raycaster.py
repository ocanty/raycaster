import sys
import ctypes
import sdl2
import sdl2.ext
import math

textures = [ ]


# A world is a matrix of tuples
# which store like so (wall_texture_id, roof_texture_id, floor_texture_id)
# where id is the index in the texture array
# World starts from top left at (0,0)
# and increases +x, +y
world = [
    [ (None, None, None),  (True, None, None),  (True, None, None),  (True, None, None),  (True, None, None) ],
    [ (None, None, None),  (None, None, None),  (None, None, None),  (True, None, None),  (True, None, None) ],
    [ (None, None, None),  (None, None, None),  (None, None, None),  (None, None, None),  (True, None, None) ],
    [ (None, None, None),  (True, None, None),  (None, None, None),  (None, None, None),  (None, None, None) ],
    [ (None, None, None),  (None, None, None),  (None, None, None),  (None, None, None),  (None, None, None) ],
    [ (None, None, None),  (None, None, None),  (None, None, None),  (None, None, None),  (None, None, None) ],
    [ (None, None, None),  (None, None, None),  (None, None, None),  (None, None, None),  (None, None, None) ],
]

def test_grid(x,y):
    print(x,y)
    if len(world) > (y):
        if len(world[y]) > (x):
            return world[y][x]

    return (None,None,None)

def distance(coord1,coord2):
    return math.sqrt(math.pow(coord1[0]-coord2[0],2) + math.pow(coord1[1]-coord2[1],2))


def trace_ray(ray_pos, ray_angle):
    ray_slope = math.tan(math.radians(ray_angle))
    ray_pos_grid = tuple(map(math.floor,ray_pos))

    
    # note these are offsets to the first HORIZONTAL intersection
    x_offset_to_first_intersection = (ray_pos[1] - ray_pos_grid[1])/ray_slope
    x_offset_to_next_intersection = 1/ray_slope

    # these offsets, like above are offsets to the first VERTICAL intersection
    y_offset_to_first_intersection = (ray_pos[0] - ray_pos_grid[0])*ray_slope
    y_offset_to_next_intersection = 1*ray_slope

    # if they're facing north
    if(ray_angle < 180): 
        # if camera is facing north, the first horizontal grid intersection of a ray
        # will be the camera grid pos - 1
        # SOHCAHTOA
        first_horiz_intersection = (
            ray_pos[0] + x_offset_to_first_intersection, 
            ray_pos_grid[1] - 1
        )

    else: # facing south
        first_horiz_intersection = (
            ray_pos_pos[0] + x_offset_to_first_intersection, 
            ray_pos_pos_grid[1] + 1
        )

    # if the ray is facing right
    if(ray_slope > 270 and ray_slope < 90):
        first_vert_intersection = (
            ray_pos[0] + 1, 
            ray_pos_grid[1] + y_offset_to_first_intersection
        )
    else:
        first_vert_intersection = (
            ray_pos[0] - 1, 
            ray_pos_grid[1] + y_offset_to_first_intersection
        )



    horiz_intersection = tuple(first_horiz_intersection)
    vert_intersection = tuple(first_vert_intersection)
    num_intersections = 1
    while(num_intersections < 10):
        if(ray_angle < 180): 
            # if camera is facing north, the first horizontal grid intersection of a ray
            # will be the camera grid pos - 1
            # SOHCAHTOA
            horiz_intersection = (
                horiz_intersection[0] + x_offset_to_next_intersection, 
                horiz_intersection[1] - 1
            )

        else: # facing south
            horiz_intersection = (
                horiz_intersection[0] + x_offset_to_next_intersection, 
                horiz_intersection[1] + 1
            )

        # if the ray is facing right
        if(ray_slope > 270 and ray_slope < 90):
            vert_intersection = (
                vert_intersection[0] + 1, 
                vert_intersection[1] + y_offset_to_next_intersection
            )
        else:
            vert_intersection = (
                vert_intersection[0] - 1, 
                vert_intersection[1] + y_offset_to_next_intersection
            )

        vert_intersection_grid = tuple(map(math.floor,vert_intersection))
        horiz_intersection_grid = tuple(map(math.floor,horiz_intersection))

        dist = None
        if test_grid(horiz_intersection_grid[0], horiz_intersection_grid[1]):
            dist = distance(horiz_intersection, ray_pos)

        if test_grid(vert_intersection_grid[0], vert_intersection_grid[1]):
            dist_temp = distance(vert_intersection, ray_pos)
            dist = dist_temp if dist > dist_temp else dist

        if dist != None:
            return dist

        num_intersections = num_intersections + 2

    return None


def renderWalls(renderer, plane_size):
    camera_fov   = 60
    camera_angle = 60
    camera_pos = (5.5,4.5)

    # Find the ray increment required for our FOV

    # -         |\
    # xsize/2   | \ <--- fov angle / 2
    # -         |--. <-- camera
    #           | /
    #           |/
    #       
    #           ^--^
    #           distance from projection plane to camera
    
    # Distance to projection plane
    proj_plane_dist = (plane_size[0]/2) / math.tan(math.radians(camera_fov)/2)

    # Angle between each ray that we will project
    # field of view / plane width
    ray_angle_increment = camera_fov / plane_size[0]

    camera_slope = math.tan(math.radians(camera_angle))

    # The grid area the camera is, cast to int both values
    camera_pos_grid = tuple(map(math.floor,camera_pos))

    x = 0

    ray_angle = camera_angle - (camera_fov//2)
    # for each ray r to l
    while ray_angle < (camera_angle + (camera_fov//2)):
        dist = trace_ray(camera_pos, ray_angle)

        if dist is not None:
            draw_height = 1 / (dist*proj_plane_dist)
            center = plane_size[1] / 2 
            renderer.draw_line(tuple(map(int,(x, center+(draw_height/2), x, center-(draw_height/2)))),
            color=291111)

        x = x + 1
        ray_angle = ray_angle + ray_angle_increment
        



def renderMap(renderer):
    x = 15
    y = 15
    for ytile in world:
        for tile in ytile:
            #tile = y[x]
            renderer.fill((x, x+5, 5, 5),11111111 if tile[0] == True else 444444)
            x = x + 5
        y = y + 5

def run():
    sdl2.ext.init()

    window = sdl2.ext.Window(
        title    = "Raycaster",
        size     = (640,480),
        flags    = sdl2.SDL_WINDOW_SHOWN,
        position =(0,0)
    )

    renderer = sdl2.ext.Renderer(window)

    running = True
    while running:
        renderer.clear(color=8881)
        renderMap(renderer)
        renderWalls(renderer, (640,480))
        renderer.present()
       

        for event in sdl2.ext.get_events():
            if event.type == sdl2.SDL_QUIT:
                running = False
                break

    sdl2.ext.quit()
    print("Exiting!")
    return 0

if __name__ == "__main__":
    sys.exit(run())
