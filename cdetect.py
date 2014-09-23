#!/usr/bin/python

"""
Script to aid in finding cyclic dependencies in C/C++ code.
Usage: cdetect [target_directory]

Author: Max Carvajal

When pointed to a directory with .h or .hpp files, this module constructs
a directed graph with the header files as nodes and their dependencies as
edges.  It then performs Tarjan's algorithm on each node, revealing any
cycles in the dependencies.

Any cycles the program detects will be output as

a.hpp <- c.hpp <- b.hpp <- a.hpp

which should be read from right to left as "a.hpp includes b.hpp which includes
c.hpp, which includes a.hpp again."

"""

import os
import re
import sys

# commentRE finds both /*...*/ comments (right part) and // ... comments (left part)
commentRE = re.compile(r"(/\*(?:.|[\r\n])*?\*/)|(//.*[\r\n])")
includeRE = re.compile(r'#include \".*\"')
filenameRE = re.compile(r'[a-zA-z]*\.(hpp|h)')

cyclesDetected = False

class Node(object):

    """
    Node object used in constructing the directed graph of header file dependencies.
    
    Node.nodes - a list of all nodes in the graph
    Node.nodeStack - a list used as a FILO stack during Tarjan's algorithm
    Node.indexCount - keeps track of what index to assign to a node during
                      Tarjan's algorithm

    self.name - name of the header file this node is representing
    self.links - a list of nodes that the header file #includes
    self.index - counts how far this node is from the root in Tarjan's algorithm
    self.lowlink - determines if this node is the root of a strongly connected
                   component in Tarjan's algorithm

    """

    nodes = [] # list of all nodes being considered
    nodeStack = [] # stack of nodes for use during Tarjan's algorithm
    indexCount = 0

    def __init__(self, n):
        self.name = n  # name of the file this node represents
        self.links = []
        self.index = -1  # used during Tarjan's algorithm
        self.lowlink = 0 # used during Tarjan's algorithm


    def __str__(self):
        val = self.name + '\n'
        for link in self.links:
             val += "\t" + link.name + '\n'
        return val

    @classmethod
    def inNodes(cls, n):
        """
        Returns an existing node if the given node is already Node.nodes,
        returns False otherwise
        
        n - name of the prospective node

        """
        for node in Node.nodes:
            if n == node.name:
                return node
        # loop completed; no match found
        return False

    def addLink(self, n):
        """adds a new outgoing link to this node"""
        test = Node.inNodes(n)
        if test:
            self.links.append(test)
        else:
            newNode = Node(n)
            Node.nodes.append(newNode)
            self.links.append(newNode)




def isValidFile(file):
    """Tests if a file ends in a '.h' or '.hpp' extension."""
    return file.endswith('.h') or file.endswith('.hpp')



def stripComments(input):
    """removes all comments from the input string."""
    return re.sub(commentRE, "", input)



def constructGraph(target):
    """
    Constructs a graph of all the .h/.hpp files in the target directory,
    where the links are the file's local #include dependencies.
    
    target - the directory to be examined.

    """
    # find all .h or .hpp files in the target directory
    os.chdir(target)
    for filename in filter(isValidFile, os.listdir(os.getcwd())):
        #print filename
        input = open(filename)
        node = Node.inNodes(filename) # test if this node already exists

        if node == False: # if it doesn't, create a new one and add it to Node.nodes
            node = Node(filename)
            Node.nodes.append(node)

        # find all #include statements outside of comments
        for inc in re.findall(includeRE, stripComments(input.read())):
            node.addLink(re.search(filenameRE, inc).group())



def tarjan(n):
    """
    Implementation of Tarjan's algorithm (see Google)
    
    n - the node to be considered.

    """
    global cyclesDetected
    n.index = Node.indexCount # set the depth index for n
    n.lowlink = Node.indexCount
    Node.indexCount += 1
    Node.nodeStack.append(n)

    for child in n.links:
        if child.index == -1:
            tarjan(child) # if the child has a cycle, this would change the result
            n.lowlink = min(n.lowlink, child.lowlink)
        elif child in Node.nodeStack:
            n.lowlink = min(n.lowlink, child.index)

    if n.lowlink == n.index:
        cycle = []
        cycle.append(Node.nodeStack.pop())

        while(cycle[-1] != n):
            cycle.append(Node.nodeStack.pop())

        if len(cycle) > 1: # we have a cycle
            print "Cyclic dependency detected:"
            for node in cycle:
                print "%s <-" % node.name,
            print cycle[0].name
            cyclesDetected = True



def main():
    # sanity check
    if(len(sys.argv) is not 2):
        print "Usage: %s [target_directory]" % sys.argv[0]
        exit()

    target = sys.argv[1]

    if(not os.path.isdir(target)):
        print "Error: %s is not a directory" % target
        exit()

    # sanity check passed, now construct the graph
    constructGraph(target)

    # run Tarjan's algorithm for every node in the list
    for node in Node.nodes:
        tarjan(node)

    if not cyclesDetected:
        print "No cyclic dependencies detected."


if __name__ == '__main__':
    main()
    


