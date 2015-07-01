#!/usr/bin/env python
from __future__ import print_function
import argparse

import six


parser = argparse.ArgumentParser(
    descriptor='Download a Caffe reference model')
parser.add_argument('model_type',
                    help='Model type (alexnet, caffenet, googlenet)')
args = parser.parse_args()

if args.model_type == 'alexnet':
    url = 'http://dl.caffe.berkeleyvision.org/bvlc_alexnet.caffemodel'
    name = 'bvlc_alexnet.caffemodel'
elif args.model_type == 'caffenet':
    url = 'http://dl.caffe.berkeleyvision.org/' \
          'bvlc_reference_caffenet.caffemodel'
    name = 'bvlc_reference_caffenet.caffemodel'
elif args.model_type == 'googlenet':
    url = 'http://dl.caffe.berkeleyvision.org/bvlc_googlenet.caffemodel'
    name = 'bvlc_googlenet.caffemodel'
else:
    raise RuntimeError('Invalid model type. Choose from '
                       'alexnet, caffenet, and googlenet.')

print('Downloading model file...')
six.moves.urllib.request.urlretrieve(url, name)
print('Done')
