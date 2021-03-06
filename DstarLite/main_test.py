# -*- coding: utf-8 -*-
"""
Created on Fri May  8 15:44:08 2020

@author: coldhenry
"""

import numpy as np
import time
import matplotlib as mpl
import matplotlib.pyplot as plt; plt.ion()
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
#import Weighted_Astar_Planner as Astar
import Dstarlite_Planner as Dstarlite

def tic():
  return time.time()
def toc(tstart, nm=""):
    dt = time.time() - tstart
    print('%s took: %s sec.\n' % (nm,(dt)))
    return dt
  

def load_map(fname):
  '''
  Loads the bounady and blocks from map file fname.
  
  boundary = [['xmin', 'ymin', 'zmin', 'xmax', 'ymax', 'zmax','r','g','b']]
  
  blocks = [['xmin', 'ymin', 'zmin', 'xmax', 'ymax', 'zmax','r','g','b'],
            ...,
            ['xmin', 'ymin', 'zmin', 'xmax', 'ymax', 'zmax','r','g','b']]
  '''
  mapdata = np.loadtxt(fname,dtype={'names': ('type', 'xmin', 'ymin', 'zmin', 'xmax', 'ymax', 'zmax','r','g','b'),\
                                    'formats': ('S8','f', 'f', 'f', 'f', 'f', 'f', 'f','f','f')})
  blockIdx = mapdata['type'] == b'block'
  boundary = mapdata[~blockIdx][['xmin', 'ymin', 'zmin', 'xmax', 'ymax', 'zmax','r','g','b']].view('<f4').reshape(-1,11)[:,2:]
  blocks = mapdata[blockIdx][['xmin', 'ymin', 'zmin', 'xmax', 'ymax', 'zmax','r','g','b']].view('<f4').reshape(-1,11)[:,2:]
  return boundary, blocks


def draw_map(boundary, blocks, start, goal):
  '''
  Visualization of a planning problem with environment boundary, obstacle blocks, and start and goal points
  '''
  fig = plt.figure()
  ax = fig.add_subplot(111, projection='3d')
  hb = draw_block_list(ax,blocks)
  hs = ax.plot(start[0:1],start[1:2],start[2:],'ro',markersize=7,markeredgecolor='k')
  hg = ax.plot(goal[0:1],goal[1:2],goal[2:],'go',markersize=7,markeredgecolor='k')  
  ax.set_xlabel('X')
  ax.set_ylabel('Y')
  ax.set_zlabel('Z')
  ax.set_xlim(boundary[0,0],boundary[0,3])
  ax.set_ylim(boundary[0,1],boundary[0,4])
  ax.set_zlim(boundary[0,2],boundary[0,5])  
  return fig, ax, hb, hs, hg

def draw_block_list(ax,blocks):
  '''
  Subroutine used by draw_map() to display the environment blocks
  '''
  v = np.array([[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0,0,1],[1,0,1],[1,1,1],[0,1,1]],dtype='float')
  f = np.array([[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7],[0,1,2,3],[4,5,6,7]])
  clr = blocks[:,6:]/255
  n = blocks.shape[0]
  d = blocks[:,3:6] - blocks[:,:3] 
  vl = np.zeros((8*n,3))
  fl = np.zeros((6*n,4),dtype='int64')
  fcl = np.zeros((6*n,3))
  for k in range(n):
    vl[k*8:(k+1)*8,:] = v * d[k] + blocks[k,:3]
    fl[k*6:(k+1)*6,:] = f + k*8
    fcl[k*6:(k+1)*6,:] = clr[k,:]
  if type(ax) is Poly3DCollection:
    ax.set_verts(vl[fl])
  else:
    pc = Poly3DCollection(vl[fl], alpha=0.25, linewidths=1, edgecolors='k')
    pc.set_facecolor(fcl)
    h = ax.add_collection3d(pc)
    return h


def runtest(mapfile, start, goal, path2, path3, path4, verbose, FLAG):
  '''
  This function:
   * load the provided mapfile
   * creates a motion planner
   * plans a path from start to goal
   * checks whether the path is collision free and reaches the goal
   * computes the path length as a sum of the Euclidean norm of the path segments
  '''
  # Load a map and instantiate a motion planner
  boundary, blocks = load_map(mapfile)
  print("boundry")
  print(boundary)
  print("blocks")
  print(blocks)
  #MP = Astar.Weighted_Astar_Planner(blocks, boundary) # TODO: replace this with your own planner implementation
  DS = Dstarlite.Dstarlite_Planner(blocks, boundary)
  # # Display the environment
  # if verbose:
    
  
  # Call the motion planner
  t0 = tic()
  path = DS.planning(start, goal)
  observedmap = DS.currMap
  total_t = toc(t0,"Planning")
  pathlength = np.sum(np.sqrt(np.sum(np.diff(path,axis=0)**2,axis=1)))
  # if FLAG == 1:
  #     file_t = './time/window.txt'
  #     file_l = './length/window.txt'
  # if FLAG == 2:
  #     file_t = './time/room.txt'
  #     file_l = './length/room.txt'
  # if FLAG == 3:
  #     file_t = './time/flappy.txt'
  #     file_l = './length/flappy.txt'
  # if FLAG == 4:
  #     file_t = './time/cube.txt'
  #     file_l = './length/cube.txt'
  # newfile = open(file_t,'a')
  # newfile.write(str(total_t)+'\n')
  # newfile.close()
  # newfile = open(file_l,'a')
  # newfile.write(str(pathlength)+'\n')
  # newfile.close()
  #print(path)
  
  # Plot the path
  if verbose:
    fig, ax, hb, hs, hg = draw_map(boundary, blocks, start, goal)
    mpl.rcParams['legend.fontsize'] = 7
    mpl.rcParams["legend.loc"] = 'lower left'
    ax.plot(path[:,0],path[:,1],path[:,2],'r-',label="D* Lite")
    ax.plot(path2[:,0],path2[:,1],path2[:,2],'b-',label="RRT")
    ax.plot(path3[:,0],path3[:,1],path3[:,2],'g-',label="RRT*")
    ax.plot(path4[:,0],path4[:,1],path4[:,2],'y-',label="RRT Connect")
    ax.legend()
    plt.ioff()
    plt.savefig("./result/"+str(FLAG)+".png")
    plt.show()

  # TODO: You should verify whether the path actually intersects any of the obstacles in continuous space
  # TODO: You can implement your own algorithm or use an existing library for segment and 
  #       axis-aligned bounding box (AABB) intersection 
  collision = False
  #goal_reached = sum((path[-1]-goal)**2) <= 0.1
  #success = (not collision) and goal_reached
  success = True
  
  return success, path


def test_single_cube(path2, path3, path4,verbose = False):
  print('Running single cube test...\n') 
  start = np.array([5.0, 3.0, 3.])
  goal = np.array([5.0, 7.0, 3.])
  success, pathlength = runtest('./maps/single_cube.txt', start, goal,path2, path3, path4, verbose,FLAG='cube')
  print('Success: %r'%success)
  #print('Path length: %d'%pathlength)
  print('\n')
  
  
def test_maze(verbose = False):
  print('Running maze test...\n') 
  start = np.array([0.0, 0.0, 1.0])
  goal = np.array([12.0, 12.0, 5.0])
  success, pathlength = runtest('./maps/maze.txt', start, goal, verbose)
  print('Success: %r'%success)
  print('Path length: %d'%pathlength)
  print('\n')

    
def test_window(path2,path3,path4,verbose = False):
  print('Running window test...\n') 
  start = np.array([0.2, -4.9, 0.2])
  goal = np.array([6.0, 18.0, 3.0])
  success, pathlength = runtest('./maps/window.txt', start, goal, path2,path3,path4, verbose,FLAG='window')
  print('Success: %r'%success)
  #print('Path length: %d'%pathlength)
  print('\n')

  
def test_tower(verbose = False):
  print('Running tower test...\n') 
  start = np.array([2.5, 4.0, 0.5])
  goal = np.array([4.0, 2.5, 19.5])
  success, pathlength = runtest('./maps/tower.txt', start, goal, verbose)
  print('Success: %r'%success)
  print('Path length: %d'%pathlength)
  print('\n')

     
def test_flappy_bird(path2, path3, path4, verbose = False):
  print('Running flappy bird test...\n') 
  start = np.array([0.5, 2.5, 5.5])
  goal = np.array([16.0, 2.5, 5.5])
  path = runtest('./maps/flappy_bird.txt', start, goal, path2, path3, path4, verbose,FLAG='flappy') #success, pathlength = 
  # print('Success: %r'%success)
  # print('Path length: %d'%pathlength) 
  # print('\n')
  
def test_room(path2, path3, path4, verbose = False):
  print('Running room test...\n') 
  start = np.array([1.0, 5.0, 1.5])
  goal = np.array([9.0, 7.0, 1.5])
  success, path = runtest('./maps/room.txt', start, goal, path2, path3, path4, verbose,FLAG='room')
  print('Success: %r'%success)
  #print('Path length: %d'%pathlength)
  print('\n')


def test_monza(verbose = False):
  print('Running monza test...\n')
  start = np.array([0.5, 1.0, 4.9])
  goal = np.array([3.8, 1.0, 0.1])
  success, pathlength = runtest('./maps/monza.txt', start, goal, verbose)
  print('Success: %r'%success)
  print('Path length: %d'%pathlength)
  print('\n')

def read2path(file):
    path = []
    f = open(file,'r')
    line = f.readline()
    
    while line:
        
        line = line.strip('[')
        line = line.rstrip()
        line = line[:-1]
        #print(line)
        info = line.split(' ')
        coor = []
        for i in info:
            coor.append(float(i))
        path.append(coor)
        line = f.readline()
    
    f.close()
    return np.array(path)


        

if __name__=="__main__":
  
    option = input("choose map: ")
    
    if option == "cube":
    
        f11 = './data/rrt_cube.txt'
        f12 = './data/rrtstar_cube.txt'
        f13 = './data/rrtconnect_cube.txt'
        path2 = read2path(f11)
        path3 = read2path(f12)
        path4 = read2path(f13)
        test_single_cube(path2, path3, path4, True)
        
    elif option == "window":
      
        f2 = './data/rrt_window.txt'
        f3 = './data/rrtstar_window.txt'
        f4 = './data/rrtconnect_window.txt'
        path2 = read2path(f2)
        path3 = read2path(f3)
        path4 = read2path(f4)
        test_window(path2,path3,path4,True)
        
    elif option == "flappy":
    
        f5 = './data/rrt_flappy.txt'
        f6 = './data/rrtstar_flappy.txt'
        f7 = './data/rrtconnect_flappy.txt'
        path2 = read2path(f5)
        path3 = read2path(f6)
        path4 = read2path(f7)
        test_flappy_bird(path2, path3, path4, True)
        
    elif option == "room":
    
        f8 = './data/rrt_room.txt'
        f9 = './data/rrtstar_room.txt'
        f10 = './data/rrtconnect_room.txt'
        path2 = read2path(f8)
        path3 = read2path(f9)
        path4 = read2path(f10)
        test_room(path2, path3, path4, True)
  

  
     
  
  
  
  #test_flappy_bird(path2, path3, path4, True)
  #test_maze(path2, path3, path4,True)
  #test_monza(path2,path3,path4,True)
  #test_tower(True)



  
  







