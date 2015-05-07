# 2015.03.10 14:42:13 UTC
import sys
import os
path = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(path + '/utils/Python_Utils')
sys.path.append(path + '../utils/Python_Utils')
sys.path.append(path + '/utils/liac-arff')
sys.path.append(path + '../utils/liac-arff')
import numpy as np
import scipy as sc
import scipy.sparse as sp
import arff
import logging,Logger

label_flag = u'multi_label_';

class ArffWriter:
    def __init__(self, filename):
        self.encoder = arff.ArffEncoder();
        self.file    = open(filename, "w");

    def write(self, obj, is_first_call = True):
        gen = self.encoder.iter_encode(obj, is_first_call);
        for row in gen:
            self.file.write(row + u'\n');

    def close(self):
        self.file.close();
         

class ArffReader:

    def __init__(self, filename, batch = 50):
        self.arff_file     = open(filename, 'rb')
        self.decoder       = arff.ArffDecoder()
        self.batch         = batch
        self.num_class     = 0
        self.num_feature   = 0
        self.num_attribute = 0
        self.classes       = []
        self.first         = True
        #nextobj store the next obj. The nextobj is important
        #because arffreader should stop reading when nextobj 
        #has no data.  
        #It prevents [] from where the number of instances is 
        #a multiple of the size of batch.  
         
        self.nextobj = None


    def full_read_sparse(self):
        x, y, has_next = self.read_sparse()
        ##setting the larger batch
        m1,n1 = x.shape
        m2,n2 = y.shape
        num = n1 + n2
        self.batch = max( 100000000 / num, self.batch)

        while True == has_next:
            ix, iy, has_next = self.read_sparse()
            x = sp.vstack([x,ix], 'csr')
            y = sp.vstack([y,iy], 'csr')
        return x,y

    def full_read(self):
        x, y, has_next = self.read()
        while has_next:
            ix, iy, has_next = self.read()
            x = np.vstack([x,ix])
            y = np.vstack([y,iy])
        return x,y;

    def read_sparse(self):
        x, y, has_next = self.read()
        return sp.csr_matrix(x), sp.csr_matrix(y), has_next

    def read(self):
        x = None
        y = None

        if None != self.nextobj:
            data = self.nextobj["data"];
            obj  = dict();
            obj["data"] = data;
        
        self.nextobj = self.decoder.iter_decode(self.arff_file, \
                                                  obj = self.nextobj, \
                                                  batch = self.batch)

        if True == self.first:
            self.first = False;
            
            self.num_attribute = len( self.nextobj['attributes'] )
            self.classes = [ 0 for i in xrange(self.num_attribute) ]
            for i in xrange(self.num_attribute):
                feat = self.nextobj["attributes"][i][0];
                type = self.nextobj["attributes"][i][1];

                ## only support NUMERIC attributes
                if u'NUMERIC' != type:
                    logger = logging.getLogger(Logger.project_name);
                    logger.error("Only support NUMERIC attributes, "
                                 "but the %s feature is %s."%(feat,type));
                    raise Exception("Only support NUMERIC attributes, "
                                 "but the %s feature is %s."%(feat, type) );

                if label_flag in feat:
                    self.classes[i] = 1
                    self.num_class += 1


            self.num_feature = self.num_attribute - self.num_class
        
            data         = self.nextobj["data"];
            obj          = dict();
            obj["data"]  = data;
            self.nextobj = self.decoder.iter_decode(self.arff_file, \
                                                    obj   = self.nextobj, \
                                                    batch = self.batch);
 
        num_instance = len(obj['data'])
        x = [ [ 0 for col in xrange(self.num_feature) ] \
              for row in xrange(num_instance) ]
        y = [ [ 0 for col in xrange(self.num_class) ] \
              for row in xrange(num_instance) ]
        for i in xrange(num_instance):
            idx_x = 0
            idx_y = 0
            for j in xrange(self.num_attribute):
                if 1 == self.classes[j]:
                    y[i][idx_y] = obj['data'][i][j]
                    idx_y += 1
                else:
                    x[i][idx_x] = obj['data'][i][j]
                    idx_x += 1

        has_next = len(self.nextobj["data"]) != 0;
        return np.array(x), np.array(y), has_next;

    

    def close(self):
        self.arff_file.close()




