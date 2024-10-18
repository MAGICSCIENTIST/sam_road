import pickle

import matplotlib.pyplot as plt

filepath = "D:\learn\sam_road\save\lyzt-g-dl2-origin-merge-penglai\spacenet_vitb_256_e10_change\graph\\967_1344_9600.png.p"

pkl = open(filepath, 'rb')

im = pickle.load(pkl)



plt.imshow(im)

pass