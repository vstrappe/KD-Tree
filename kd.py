from __future__ import annotations
import json
import math
from typing import List

# Datum class.
# DO NOT MODIFY.
class Datum():
    def __init__(self,
                 coords : tuple[int],
                 code   : str):
        self.coords = coords
        self.code   = code
    def to_json(self) -> str:
        dict_repr = {'code':self.code,'coords':self.coords}
        return(dict_repr)

# Internal node class.
# DO NOT MODIFY.
class NodeInternal():
    def  __init__(self,
                  splitindex : int,
                  splitvalue : float,
                  leftchild,
                  rightchild):
        self.splitindex = splitindex
        self.splitvalue = splitvalue
        self.leftchild  = leftchild
        self.rightchild = rightchild

# Leaf node class.
# DO NOT MODIFY.
class NodeLeaf():
    def  __init__(self,
                  data : List[Datum]):
        self.data = data

# KD tree class.
class KDtree():
    def  __init__(self,
                  k    : int,
                  m    : int,
                  root = None):
        self.k    = k
        self.m    = m
        self.root = root

    # For the tree rooted at root, dump the tree to stringified JSON object and return.
    # DO NOT MODIFY.
    def dump(self) -> str:
        def _to_dict(node) -> dict:
            if isinstance(node,NodeLeaf):
                return {
                    "p": str([{'coords': datum.coords,'code': datum.code} for datum in node.data])
                }
            else:
                return {
                    "splitindex": node.splitindex,
                    "splitvalue": node.splitvalue,
                    "l": (_to_dict(node.leftchild)  if node.leftchild  is not None else None),
                    "r": (_to_dict(node.rightchild) if node.rightchild is not None else None)
                }
        if self.root is None:
            dict_repr = {}
        else:
            dict_repr = _to_dict(self.root)
        return json.dumps(dict_repr,indent=2)

    # Insert the Datum with the given code and coords into the tree.
    # The Datum with the given coords is guaranteed to not be in the tree.
    def insert(self,point:tuple[int],code:str):
        data = Datum(point, code)
        if self.root == None:
            self.root = NodeLeaf([data])
        else:
            current = self.root
            parent = None
            while current != None:
                if type(current) == NodeLeaf:
                    if len(current.data) < self.m:
                        (current.data).append(data)
                        return self
                    else:
                        (current.data).append(data)
                        left = False
                        if parent != None and type(parent) == NodeInternal and parent.leftchild == current:
                            left = True
                        KDtree.split(self, parent, current, left)
                        return self
                else:
                    if point[current.splitindex] < current.splitvalue:
                        parent = current
                        current = current.leftchild
                    else:
                        parent = current
                        current = current.rightchild

    def split(self, parent, node, left):
        k = self.k
        max_coord = 0
        max_spread = 0
        for i in range(k):
            min = 100000000
            max = 0
            n = node.data
            for j in n:
                if j.coords[i] < min:
                    min = j.coords[i]
                if j.coords[i] > max:
                    max = j.coords[i]
            spread = max - min
            if spread > max_spread:
                max_coord = i
                max_spread = spread
        order = []
        counter = max_coord
        for l in range(k):
            order.append(counter)
            if counter == k - 1:
                counter = 0
            else:
                counter += 1
        node.data = sorted(node.data, key=lambda point: tuple(point.coords[i] for i in order))
        median = KDtree.find_median(max_coord, node.data)
        left_half = node.data[:int(len(node.data) / 2)]
        right_half = node.data[int(len(node.data) / 2):]
        left_node = NodeLeaf(left_half)
        right_node = NodeLeaf(right_half)
        internal = NodeInternal(max_coord, float(median), left_node, right_node)
        if left == True and parent != None and type(parent) == NodeInternal:
            parent.leftchild = internal
        elif parent != None and type(parent) == NodeInternal:
            parent.rightchild = internal
        else:
            self.root = internal

    def find_median(max_coord, data):
        length = len(data)
        middle = length / 2
        rem = length % 2
        if rem == 0:
            return ((data[int(middle - 1)]).coords[max_coord] + (data[int(middle)]).coords[max_coord]) / 2
        else:
            return (data[int(middle - 0.5)]).coords[max_coord]

    # Delete the Datum with the given point from the tree.
    # The Datum with the given point is guaranteed to be in the tree.
    def delete(self,point:tuple[int]):
        current = self.root
        parent = None
        grandparent = None
        while current != None:
            if type(current) == NodeLeaf:
                if len(current.data) > 1:
                    i = KDtree.search(current, point)
                    current.data.remove(current.data[i])
                    return self
                else:
                    if parent == None:
                        self.root = None
                    elif grandparent == None:
                        if parent.leftchild == current:
                            self.root = parent.rightchild
                        else:
                            self.root = parent.leftchild
                    else:
                        if grandparent.leftchild == parent and parent.leftchild == current:
                            grandparent.leftchild = parent.rightchild
                        elif grandparent.rightchild == parent and parent.leftchild == current:
                            grandparent.rightchild = parent.rightchild
                        elif grandparent.leftchild == parent and parent.rightchild == current:
                            grandparent.leftchild = parent.leftchild
                        else:
                            grandparent.rightchild = parent.leftchild
                    return self
            else:
                if point[current.splitindex] < current.splitvalue:
                    grandparent = parent
                    parent = current
                    current = current.leftchild
                else:
                    grandparent = parent
                    parent = current
                    current = current.rightchild

    def search(current, point):
        length = len(current.data)
        for i in range(length):
            if current.data[i].coords == point:
                return i

    # Find the k nearest neighbors to the point.
    def knn(self,k:int,point:tuple[int]) -> str:
        leaveschecked = 0
        knnlist = []

        res = KDtree.knn_helper(self, self.root, k, point, leaveschecked, knnlist)

        leaveschecked = res[0]
        knnlist = res[1]

        return(json.dumps({"leaveschecked":leaveschecked,"points":[datum.to_json() for datum in knnlist]},indent=2))
    
    def knn_helper(self, current, k, point, leaves, lst):
        result = (leaves, lst)
        if type(current) == NodeLeaf:
            distances = current.data
            leaves += 1
            distances = sorted(distances, key=lambda x: (KDtree.point_distance(point, x.coords, self.k), x.code))
            if len(lst) >= k:
                for i in distances:
                    if KDtree.point_distance(point, i.coords, self.k) < KDtree.point_distance(point, lst[k-1].coords, self.k):
                        lst[k-1] = i
                        lst = sorted(lst, key=lambda x: (KDtree.point_distance(point, x.coords, self.k), x.code))
                    elif KDtree.point_distance(point, i.coords, self.k) == KDtree.point_distance(point, lst[k-1].coords, self.k):
                        val = 0
                        for elem in range(3):
                            if i.code[elem] != lst[k-1].code[elem]:
                                val = ord(i.code[elem]) - ord(lst[k-1].code[elem])
                                break
                        if val < 0:
                            lst[k-1] = i
                            lst = sorted(lst, key=lambda x: (KDtree.point_distance(point, x.coords, self.k), x.code))
                    else:
                        break
            else:
                for d in distances:
                    if len(lst) == k:
                        break
                    else:
                        lst.append(d)
                        lst = sorted(lst, key=lambda x: (KDtree.point_distance(point, x.coords, self.k), x.code))
            return (leaves, lst)
        else:
            if type(current.leftchild) == NodeLeaf:
                box1 = KDtree.get_box_leaf(self, current.leftchild)
            else:
                box1 = KDtree.get_box_internal(self, current.leftchild, [])
            if type(current.rightchild) == NodeLeaf:
                box2 = KDtree.get_box_leaf(self, current.rightchild)
            else:
                box2 = KDtree.get_box_internal(self, current.rightchild, [])
            if KDtree.box_distance(point, box1, self.k) <= KDtree.box_distance(point, box2, self.k):
                if len(lst) < k or KDtree.box_distance(point, box1, self.k) <= KDtree.point_distance(point, lst[k-1].coords, self.k):
                    result = KDtree.knn_helper(self, current.leftchild, k, point, leaves, lst)
                    if len(result[1]) < k or KDtree.box_distance(point, box2, self.k) <= KDtree.point_distance(point, result[1][k-1].coords, self.k):
                        result = KDtree.knn_helper(self, current.rightchild, k, point, result[0], result[1])
            else:
                if len(lst) < k or KDtree.box_distance(point, box2, self.k) <= KDtree.point_distance(point, lst[k-1].coords, self.k):
                    result = KDtree.knn_helper(self, current.rightchild, k, point, leaves, lst)
                    if len(result[1]) < k or KDtree.box_distance(point, box1, self.k) <= KDtree.point_distance(point, result[1][k-1].coords, self.k):
                        result = KDtree.knn_helper(self, current.leftchild, k, point, result[0], result[1])
            return result

    def point_distance(point, coord, k):
        sum = 0
        for i in range(k):
            sum += (point[i] - coord[i]) * (point[i] - coord[i])
        return sum
    
    def get_box_leaf(self, node):
        coords = []
        for i in range(self.k):
            min = 100000000
            max = 0
            n = node.data
            for j in n:
                if j.coords[i] < min:
                    min = j.coords[i]
                if j.coords[i] > max:
                    max = j.coords[i]
            coords.append((min, max))
        return coords
    
    def get_box_internal(self, node, final):
        if type(node) == NodeLeaf:
            box = KDtree.get_box_leaf(self, node)
            if final == []:
                final = box
            else:
                for i in range(self.k):
                    if box[i][0] < final[i][0]:
                        final[i] = (box[i][0], final[i][1])
                    if box[i][1] > final[i][1]:
                        final[i] = (final[i][0], box[i][1])
            return final
        else:
            final = KDtree.get_box_internal(self, node.leftchild, final)
            final = KDtree.get_box_internal(self, node.rightchild, final)
            return final
    
    def box_distance(point, box, k):
        sum = 0
        for i in range(k):
            if point[i] < box[i][0]:
                sum += (box[i][0] - point[i]) * (box[i][0] - point[i])
            elif point[i] > box[i][1]:
                sum += (point[i] - box[i][1]) * (point[i] - box[i][1])
            else:
                sum += 0
        return sum
        