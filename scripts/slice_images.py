#!/usr/bin/python

"""
Usage: python slice_images.py <input_directory> <output_directory> <n> <optional: stride>
Example: python slice_images.py data data_sliced_512 512
Parameters: 
    <input_directory>: path to .jpg images
    <output_directory>: output path to save image slices
    <n>: dimension of output slices (nxn)
    <OPTIONAL - stride>: how many positions to slide the window when generating slices. This parameter is optional and will
        default to n if not supplied. A stride of n means that the slices fit exactly next to each other with no overlap
Notes: slices are zero-padded if needed at edges
"""

from PIL import Image

import numpy as np
import sys, math, os, glob, argparse


"""
Slices image into patches of size nxn according to stride
Zero pads any patches that are cut off at borders of image
Returns numpy array of image patches
"""
def slice_image(img, n, stride, channels):
    x_dim, y_dim = img.shape[0], img.shape[1]
    
    # calculate number of output slices
    num_x = math.ceil((x_dim-n)/stride + 1)
    num_y = math.ceil((y_dim-n)/stride + 1)

    # iterate through img 
    results = np.zeros((num_x*num_y, n, n, channels), dtype=int)
    counter = 0

    for i in range(num_y):
        y = 0 if i==0 else y + stride
        for j in range(num_x):
            x = 0 if j==0 else x + stride

            im_slice = img[x:x+n, y:y+n]
            
            dims = im_slice.shape
            if channels == 1:
                im_slice = im_slice.reshape((dims[0],dims[1],1))
            results[counter,0:im_slice.shape[0],0:im_slice.shape[1]] = im_slice
            counter += 1
    return results
    
def main(args):
    # parse arguments
    im_dir = args[0]
    im_dir_out = args[1]
    n = int(args[2])
    if len(args) == 4:
        stride = int(args[3])
    else:
        stride = n

    # read images and slice
    im_filenames = glob.glob(im_dir+'/*.jpg', recursive=True)

    if not os.path.exists(im_dir_out):
        os.makedirs(im_dir_out)

    for i, im_filename in enumerate(im_filenames):
        im = Image.open(im_filename)
        im = np.asarray(im)
        filename = im_filename.split('/')[-1] #get image name

        im_slices = slice_image(im, n, stride, 3)
        
        for j, im_slice in enumerate(im_slices):
            result = Image.fromarray(im_slice.astype(np.uint8))
            result.save(os.path.join(im_dir_out,filename.split('.')[0]+'_'+str(j)+'.jpg'))
            
        print("Processed image {}: {} ".format(i+1, filename))
        print("Dim: {}, Slices: {}".format(im.shape, im_slices.shape[0]))

if __name__ == "__main__":
   main(sys.argv[1:])