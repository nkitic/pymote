# -*- coding: utf-8 -*-
"""
Created on Mon May 28 22:58:09 2018

@author: Nikol
"""

from PyQt4 import QtCore
from PyQt4.QtGui import QFileDialog, QMessageBox, QApplication, QMainWindow, QGraphicsScene, QPen, QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsTextItem, QGraphicsPixmapItem, QPixmap
from pymote.npickle import read_pickle, write_pickle
from datetime import datetime
from PIL import Image

import sys
import managenetgui
import pymote

class ManageNet(QMainWindow, managenetgui.Ui_MainWindow):
    def __init__(self, net=None):
        super(self.__class__, self).__init__()
        
        self.setupUi(self)
        
        self.scene = Scene(self.lblXY, self.spinId, self.spinX, self.spinY, self.btnAddEdge, self.btnDeleteEdge, self.spinCommRange, self.spinEnvX, self.spinEnvY, self.comboChannelType)
        self.view = self.graphView.setScene(self.scene)
        
        self.btnOpen.clicked.connect(self.open_net)  
        self.btnSave.clicked.connect(self.save_net)
        self.btnClear.clicked.connect(self.clear_scene)
        self.btnMoveNode.clicked.connect(self.scene.move_node)
        self.btnAddNode.clicked.connect(self.scene.add_node)
        self.btnDeleteNode.clicked.connect(self.scene.delete_node)
        self.btnAddEdge.clicked.connect(self.scene.add_edge)
        self.btnDeleteEdge.clicked.connect(self.scene.delete_edge)
        
        self.chkAutoAddEdge.stateChanged.connect(lambda:self.scene.auto_add_edge(self.chkAutoAddEdge))
        self.chkShowRadius.stateChanged.connect(lambda:self.scene.show_radius(self.chkShowRadius))
        
        self.spinCommRange.valueChanged.connect(self.scene.change_comm_range)
        #self.spinId.valueChanged.connect(self.scene.search_node_by_id)
        self.spinX.valueChanged.connect(self.scene.change_node_x)
        self.spinY.valueChanged.connect(self.scene.change_node_y)
        
        self.btnOpenEnv.clicked.connect(self.scene.open_env)
        self.spinEnvX.setValue(self.scene.envX)
        self.spinEnvY.setValue(self.scene.envY)
        self.spinEnvX.valueChanged.connect(self.scene.change_node_env_x)
        self.spinEnvY.valueChanged.connect(self.scene.change_node_env_y)
        self.chkShowEnv.stateChanged.connect(lambda:self.scene.show_env(self.chkShowEnv))
        
        self.comboChannelType.addItems(['Udg', 'SquareDisc'])
        self.comboChannelType.currentIndexChanged.connect(self.scene.change_channel_type)
        
        self.net = None
        self.fname = 0
      
    def open_net(self, *args):
        
        filters = ['Network pickle (*.gz), (*.tar.gz)', 'All files (*)']
        selectedFilter = 'Network pickle (*.gz), (*.tar.gz)'
        filters = ';;'.join(filters)

        fname = QFileDialog.getOpenFileName(
            self, "Choose a file to open", '', filters, selectedFilter)
        
        if fname:
            try:
                print ("open " + fname)
                #self.fname = fname
                self.net = None
                self.net = read_pickle(fname)
                self.scene.draw_net(self.net)
            except Exception as e:
                #print ("Error opening file %s" % str(e)),
                QMessageBox.critical(
                    self, "Error opening file", str(e),
                    QMessageBox.Ok, QMessageBox.NoButton)
               
    def save_net(self, *args):
        
        if self.fname != 0 :
            start = self.fname
        else:
            default_filetype = 'gz'
            start = datetime.now().strftime('%Y%m%d.tar.') + default_filetype

        filters = ['Network pickle (*.gz), (*.tar.gz)', 'All files (*)']
        selectedFilter = 'Network pickle (*.gz), (*.tar.gz)'
        filters = ';;'.join(filters)
                
        fname = QFileDialog.getSaveFileName(
            self, "Choose a filename", start, filters, selectedFilter)
        
        if fname:
            try:
                #print ("save " + fname)
                self.net = self.scene.get_net()
                write_pickle(self.net, str(fname))
            except Exception as e:
                #print ("Error saving file %s" % str(e)),
                QMessageBox.critical(
                    self, "Error saving file", str(e),
                    QMessageBox.Ok, QMessageBox.NoButton)
    
    def clear_scene(self):
        
        self.scene.ini_scene()

class Scene(QGraphicsScene):
    def __init__(self, lblXY, spinId, spinX, spinY, btnAddEdge, btnDeleteEdge, spinCommRange, spinEnvX, spinEnvY, comboChannelType):
        super(self.__class__, self).__init__()
        
        self.net = pymote.Network()
        self.net_dict = {} #for keeping pairs of net_node and scene_node
        
        self.comm_range = 200
        self.curr_id = 1
        self.node_size = 15
        self.node_color = QtCore.Qt.blue
        self.pressed_color = QtCore.Qt.red
        
        self.lblXY = lblXY #shows x,y position on scene
        self.spinId = spinId
        self.spinId.setEnabled(False)
        self.spinX = spinX
        self.spinY = spinY
        self.btnAddEdge = btnAddEdge
        self.btnDeleteEdge = btnDeleteEdge
        self.spinEnvX = spinEnvX
        self.spinEnvY = spinEnvY
        self.comboChannelType = comboChannelType
        self.hide_btn_edge() #on start: auto edge mode selected -> buttons add and delete edge not needed
        self.hide_pressed_item_data() #on start: no item is pressed -> hide item data
        
        self.spinCommRange = spinCommRange
        self.spinCommRange.setValue(self.comm_range)
        
        self.f_show_radius = False
        self.f_auto_edge = True
        self.f_move = False 
        self.f_moved = False
        self.f_show_env = True
        self.f_opening_net = False
        
        self.option = 0
        self.edge_option = 0
        self.last_pressed_node = 0
        self.radius = 0
        
        self.environment = pymote.Environment()
        self.scene_env = 0
        self.envX = 600
        self.envY = 600
        
        self.channel_type = self.comboChannelType.currentText()
        
        self.setSceneRect(QtCore.QRectF(0, -self.envY, self.envX, self.envY))
    
    def ini_scene(self):
        self.clear()
        
        new_net = pymote.Network()
        self.net = new_net
        self.net_dict.clear()
        
        self.curr_id = 1
        self.option = 0
        self.edge_option = 0
        self.last_pressed_node = 0
        self.radius = 0
        
        self.environment = pymote.Environment()
        self.scene_env = 0
    
    def get_net(self):
        return self.net
        
    def hide_pressed_item_data(self):
        #self.spinId.setEnable(False)
        self.spinId.setValue(0)
        self.spinX.setEnabled(False)
        self.spinX.setValue(0)
        self.spinY.setEnabled(False)
        self.spinY.setValue(0)
        
    def show_pressed_item_data(self):
        #self.spinId.setEnable(True)
        self.spinId.setValue(self.last_pressed_node.node_id)
        self.spinX.setEnabled(True)
        self.spinX.setValue(self.last_pressed_node.get_X())
        self.spinY.setEnabled(True)
        self.spinY.setValue(-self.last_pressed_node.get_Y())
    
    def hide_btn_edge(self):
        self.btnAddEdge.setEnabled(False)
        self.btnDeleteEdge.setEnabled(False)
    
    def show_btn_edge(self):
        self.btnAddEdge.setEnabled(True)
        self.btnDeleteEdge.setEnabled(True)
    
    def auto_add_edge(self, toggle):
        if toggle.isChecked() == True:
            self.f_auto_edge = True
            self.hide_btn_edge()
            
            self.delete_all_edges()            
            self.net.recalculate_edges()
            self.draw_all_edges()
        else:
            self.f_auto_edge = False
            self.show_btn_edge()
    
    def show_radius(self, toggle):
        if toggle.isChecked() == True:
            self.f_show_radius = True
            if self.last_pressed_node != 0 and self.option == 0:
                self.draw_radius(self.last_pressed_node.get_X() + self.node_size/2, self.last_pressed_node.get_Y() + self.node_size/2, self.comm_range)
        else:
            self.f_show_radius = False
            if self.radius != 0:
                self.delete_radius()
    
    def show_env(self, toggle):
        if toggle.isChecked() == True:
            self.f_show_env =True
            if self.scene_env != 0:
                self.scene_env.show()
        else:
            self.f_show_env = False
            if self.scene_env != 0:
                self.delete_env()
    
    def draw_radius(self, x, y, comm_range):
        self.radius = Radius(x, y, comm_range)
        self.addItem(self.radius)             
    
    def delete_radius(self):
        self.removeItem(self.radius)
        self.radius = 0

#    def search_node_by_id(self):
#        f_found = False
#        
#        if self.last_pressed_node != 0:
#            if self.last_pressed_node.node_id != self.spinId.value(): 
#                self.last_pressed_node.setBrush(self.node_color)
#                for n in self.items():
#                    if isinstance(n, Node):
#                        if n.node_id == self.spinId.value():
#                            if self.radius != 0 and self.f_show_radius:
#                                size = n.comm_range
#                                self.radius.setRect(n.get_X() - size, n.get_Y() - size, size * 2, size * 2)
#                            self.last_pressed_node = n
#                            n.setBrush(self.pressed_color)
#                            self.spinX.setValue(n.get_X())
#                            self.spinY.setValue(-n.get_Y())
#                            f_found = True
#            
#                if not f_found:
#                    self.last_pressed_node = 0
#                    self.spinX.setValue(0)
#                    self.spinY.setValue(0)
#                    if self.radius != 0:
#                        self.delete_radius()
        
    def change_node_x(self):
        if self.last_pressed_node != 0 and not self.f_move:
            if self.last_pressed_node.get_X() != self.spinX.value():
                self.spin_value_changed(True)
            
    def change_node_y(self):
        if self.last_pressed_node != 0 and not self.f_move:
            if -self.last_pressed_node.get_Y() != self.spinY.value():
                self.spin_value_changed(False)
    
    def spin_value_changed(self, f_isX):
        if not self.f_auto_edge:
            self.move_edges(self.last_pressed_node, self.spinX.value(), self.spinY.value())    
        if self.f_auto_edge and not self.f_moved: #delete edges before node is moved
            edges = list()
            for edge in self.last_pressed_node.edges:
                edges.append(edge)
            
            for edge in edges:
                self._delete_edge(edge, True)   
        
        if f_isX:        
            self.last_pressed_node.setX(self.spinX.value() - self.last_pressed_node.get_iniX())
            self.last_pressed_node.node_label.setX(self.spinX.value())
        else:
            self.last_pressed_node.setY(-self.spinY.value() - self.last_pressed_node.get_iniY())
            self.last_pressed_node.node_label.setY(-self.spinY.value())
            
        net_node, n = self.get_nodes_from_net(self.last_pressed_node, 0)
        self.net.pos[net_node] = [self.spinX.value(), self.spinY.value()]
        
        if self.f_auto_edge and not self.f_moved:
            self.net.recalculate_edges([self.last_pressed_node.net_node])
            self.draw_recalc_edges(self.last_pressed_node.net_node)
    
    def change_comm_range(self):
        self.comm_range = self.spinCommRange.value()
        if self.last_pressed_node != 0:            
            self.last_pressed_node.set_comm_range(self.comm_range)
            
            net_node, n = self.get_nodes_from_net(self.last_pressed_node, 0)
            net_node.commRange = self.comm_range
            
        if self.radius != 0:
            size = self.comm_range
            self.radius.setRect(self.radius.get_iniX() - size, self.radius.get_iniY() - size, size * 2, size * 2)
    
    def change_node_env_x(self):
        self.envX = self.spinEnvX.value()
        #TODO: dodati promjenu velicine env u net.env
        self.setSceneRect(QtCore.QRectF(0, -self.envY, self.envX, self.envY))
    
    def change_node_env_y(self):
        self.envY = self.spinEnvY.value()
        #TODO: dodati promjenu velicine env u net.env
        self.setSceneRect(QtCore.QRectF(0, -self.envY, self.envX, self.envY))
    
    def change_channel_type(self):
        if self.comboChannelType.currentIndex() == 0:
            self.net.channelType = pymote.channeltype.Udg(self.net.environment)            
        elif self.comboChannelType.currentIndex() == 1:
            self.net.channelType = pymote.channeltype.SquareDisc(self.net.environment)
        if not self.f_opening_net and self.f_auto_edge:
            self.delete_all_edges()
            self.net.recalculate_edges()
            self.draw_all_edges()
            
    def draw_net(self, net):
        self.ini_scene()
        self.net = net
        self.f_opening_net = True
        max_id = 0        
        
        for net_node in net:
            node = self.draw_node(net.pos[net_node][0], net.pos[net_node][1], net_node.id, net_node.commRange, net_node) 
            self.net_dict[net_node] = node
            if net_node.id > max_id:
                max_id = net_node.id
                
        self.curr_id = max_id + 1
        
        self.draw_all_edges()
        
        self.environment = net.environment
        img = Image.fromarray(net.environment.im[::-1, :], 'L')
        img.save('env.png')
        self.draw_env('env.png')
        
        combo_index = -1 
        if isinstance(net.channelType, pymote.channeltype.Udg):
            combo_index = 0
        elif isinstance(net.channelType, pymote.channeltype.SquareDisc):
            combo_index = 1
            
        self.comboChannelType.setCurrentIndex(combo_index)
        self.f_opening_net = False
                
    def draw_node(self, x, y, node_id, comm_range, net_node):
        node_label = Label(str(node_id), x, -y)
        self.addItem(node_label)
        
        node = Node(x - self.node_size/2, -y - self.node_size/2, self.node_size, node_id, node_label, comm_range, net_node)        
        node.setBrush(self.node_color)
        self.addItem(node)
        
        return node

    def draw_edge(self, node1, node2):
        edge = Edge(node1, node2)
        self.addItem(edge)
        
        node1.add_edge_to_list(edge)
        node2.add_edge_to_list(edge)
        
        return edge
    
    def draw_all_edges(self):
        net = self.net
        edges = list()
        for net_node in self.net:
            for n in net.adj[net_node].keys():
                f_draw_edge = True
                for e in edges: #check if edge already drawn
                    if (e[0] == net_node.id and e[1] == n.id) or (e[1] == net_node.id and e[0] == n.id):
                        f_draw_edge = False
                
                if f_draw_edge:
                    node = self.net_dict[net_node]
                    adj_node = self.net_dict[n]
                    self.draw_edge(node, adj_node)
                    edges.append((net_node.id, n.id))
                    
    def delete_all_edges(self):
        for item in self.items():
                if isinstance(item, Edge):
                    self._delete_edge(item, True)
                    
    def draw_recalc_edges(self, net_node):
        node = self.net_dict[net_node]
        
        for n in self.net.adj[net_node].keys():
            adj_node = self.net_dict[n]
            self.draw_edge(node, adj_node)
            
    def open_env(self):
        filters = ['Environment image (*.png)', 'All files (*)']
        selectedFilter = 'Environment image (*.png)'
        filters = ';;'.join(filters)

        fname = QFileDialog.getOpenFileName(
            self.parent(), "Choose a file to open", '', filters, selectedFilter)
        
        if fname:
            try:                
                self.environment.__init__(path = str(fname))
                self.net.environment = self.environment
                self.draw_env(fname)
            except Exception as e:
                print ("Error opening file %s" % str(e)),
                QMessageBox.critical(
                    self, "Error opening file", str(e),
                    QMessageBox.Ok, QMessageBox.NoButton)
    
    def draw_env(self, image):
        if self.scene_env == 0:    
            self.scene_env = QGraphicsPixmapItem()
        else:
            self.removeItem(self.scene_env)
        
        self.scene_env.setPixmap(QPixmap(image))
        
        if self.scene_env != 0:
            self.scene_env.setPos(0, -self.environment.im.shape[1])
        
        self.addItem(self.scene_env)
        self.scene_env.setZValue(-1)
            
        if not self.f_show_env:
            self.scene_env.hide()
        
        self.spinEnvX.setValue(self.environment.im.shape[0])
        self.spinEnvY.setValue(self.environment.im.shape[1])
            
        if self.f_auto_edge:
            self.delete_all_edges()
            self.net.recalculate_edges()
            self.draw_all_edges()
        
    def delete_env(self):
        if self.scene_env != 0:
            self.scene_env.hide()
    
    def option_change(self):
        if self.radius != 0:
            self.delete_radius()
        if self.edge_option != 0:
            self.edge_option = 0
            self.deselect_node()
        if self.last_pressed_node != 0:
            self.deselect_node()
    
    def move_node(self):
        self.option_change()
        self.option = 0    
    
    def add_node(self):
        self.option_change()
        self.option = 1
    
    def _add_node(self, x, y):        
        #add node to network
        net_node = pymote.Node()
        self.net.add_node(net_node, (x, y))
        net_node.id = self.curr_id
        net_node.commRange = self.comm_range
        
        #add node to scene
        node = self.draw_node(x, y, self.curr_id, self.comm_range, net_node)
        self.net_dict[net_node] = node
        
        self.curr_id = self.curr_id + 1
        
        '''when adding new node to network pymote calls recalculate_edges,
        if USE MODEL OF COMMUNICATON TO AUTO EDGES is not selected
        then we need to remove those edges'''
        if not self.f_auto_edge:
            self.net.adj[net_node].clear()
            for n in self.net:
                if self.net.adj[n].has_key(net_node):
                    del self.net.adj[n][net_node]
        else:
            self.draw_recalc_edges(net_node)
        
    def delete_node(self):
        self.option_change()
        self.option = 2
    
    def _delete_node(self, node):  
        #delete node edges from scene
        edges = list()
        for edge in node.edges:
            edges.append(edge)
            
        for edge in edges:
            self._delete_edge(edge, False)
            
        self.removeItem(node)
        self.removeItem(node.node_label)
        
        #delete node from network
        self.net.remove_node(node.net_node)
        del self.net_dict[node.net_node] 
        
    def add_edge(self):
        self.option_change()
        self.option = 3
            
    def _add_edge(self, pressed_node):
        if pressed_node != 0:
            if self.edge_option == 0:
                self.select_node(pressed_node)
                self.edge_option = 1
              
            if self.edge_option == 1 and self.last_pressed_node != pressed_node and self.last_pressed_node != 0:                   
                self.edge_option = 2
                edge_exists = self.find_edge(pressed_node, self.last_pressed_node)
                if edge_exists != 0: 
                    self.edge_option = 0 
                    self.deselect_node()
                        
            if self.edge_option == 2:
                self.draw_edge(self.last_pressed_node, pressed_node)
                self.edge_option = 0
                
                #add edge to net.adj            
                node1, node2 = self.get_nodes_from_net(self.last_pressed_node, pressed_node)
                if node1 != 0 and node2 != 0:            
                    self.net.adj[node1][node2] = []
                    self.net.adj[node2][node1] = []
                
                self.deselect_node()
                
        elif pressed_node == 0 and self.edge_option == 1:
            self.edge_option = 0
            self.deselect_node()
    
    def delete_edge(self):
        self.option_change()
        self.option = 4
            
    def _delete_edge(self, edge, f_recal_called):
        n1 = edge.node1
        n2 = edge.node2
        
        n1.remove_edge_from_list(edge)
        n2.remove_edge_from_list(edge)
        self.removeItem(edge)
        
        #delete edge from net.adj
        if not f_recal_called:
            node1, node2 = self.get_nodes_from_net(n1, n2)    
            if node1 != 0 and node2 != 0:
                self.delete_edge_from_adj(node1, node2)
                self.delete_edge_from_adj(node2, node1)
    
    def get_nodes_from_net(self, n1, n2):
        node1 = 0
        node2 = 0
        for n in self.net:
            if n.id == n1.node_id: 
                node1 = n
            if n2 != 0:
                if n.id == n2.node_id:
                    node2 = n
        return (node1, node2)
    
    def delete_edge_from_adj(self, node, del_n):
        del self.net.adj[node][del_n]
            
    def find_edge(self, node, n):
        for e in node.edges:
            if (n.get_X() == e.line().x1() and n.get_Y() == e.line().y1()) or (n.get_X() == e.line().x2() and n.get_Y() == e.line().y2()):
                return e
        return 0
    
    def select_node(self, node):
        self.last_pressed_node = node
        node.setBrush(self.pressed_color)
        
        if self.option == 0:
            self.show_pressed_item_data()
            
            if self.f_show_radius:
                self.draw_radius(node.get_X() + self.node_size/2, node.get_Y() + self.node_size/2, self.last_pressed_node.comm_range)
        
    def deselect_node(self):
        self.last_pressed_node.setBrush(self.node_color)
        self.last_pressed_node = 0
        
        self.hide_pressed_item_data()
        
        if self.radius != 0:
            self.delete_radius()
    
    def move_edges(self, node, x, y):
        for edge in node.edges:
            if edge.line().x1() == node.get_X() and edge.line().y1() == node.get_Y():
                edge.setLine(x, y, edge.line().x2(), edge.line().y2())
            else:
                edge.setLine(edge.line().x1(), edge.line().y1(), x, y)
        
    def mousePressEvent(self, e):
        mouseX = e.scenePos().x()
        mouseY = -e.scenePos().y()
        
        pressed_node = 0
        pressed_edge = 0
        
        self.f_move = True
        
        for item in self.items(e.scenePos()):
            if pressed_node == 0 and isinstance(item, Node):
                pressed_node = item
            if pressed_edge == 0 and isinstance(item, Edge):
                pressed_edge = item
        
        #on new mouse press deselect last node (only if option add edge is not selected)
        if self.last_pressed_node != 0:
            if self.edge_option != 1:
                self.deselect_node()
        
        if self.option == 1: #draw node
            self._add_node(mouseX, mouseY)
        
        elif self.option == 2: #delete node
            if pressed_node != 0:
                self._delete_node(pressed_node)
    
        elif self.option == 3: #add edge  
            self._add_edge(pressed_node)
                                
        elif self.option == 4: #delete edge
            if pressed_edge != 0:
                self._delete_edge(pressed_edge, False)
        
        #select new pressed node and save it
        if pressed_node != 0:
            if self.option == 0:
                self.select_node(pressed_node)
                self.spinCommRange.setValue(pressed_node.comm_range)
        else:
            self.last_pressed_node = 0
    
    def mouseMoveEvent(self, e):
        mouseX = e.scenePos().x()
        mouseY = e.scenePos().y()
        
        self.lblXY.setText('x: ' + str(mouseX) + '  y: ' + str(-mouseY))
        
        if self.last_pressed_node != 0 and self.f_move:
            node = self.last_pressed_node
            self.f_moved = True
            
            if self.option == 0:
                #when moving node, move his edges
                if not self.f_auto_edge:
                    self.move_edges(node, mouseX, mouseY)
                    
                #move node
                node.setX(mouseX - node.get_iniX())
                node.setY(mouseY - node.get_iniY())
                node.node_label.setPos(mouseX, mouseY)
                
                net_node, n = self.get_nodes_from_net(node, 0)
                self.net.pos[net_node][0] = mouseX
                self.net.pos[net_node][1] = -mouseY
                
                if self.f_auto_edge:
                    edges = list()
                    for edge in node.edges:
                        edges.append(edge)
                        
                    for edge in edges:
                        self._delete_edge(edge, True)
                
                self.spinX.setValue(mouseX)
                self.spinY.setValue(-mouseY)
                
        #move radius
        if self.f_show_radius and (self.option == 1 or (self.option == 0 and self.last_pressed_node != 0 and self.f_move)):
            if self.radius == 0 and self.option == 1:
                self.draw_radius(mouseX, mouseY, self.comm_range)
            elif self.radius != 0:
                self.radius.setX(mouseX - self.radius.get_iniX())
                self.radius.setY(mouseY - self.radius.get_iniY())
        
    def mouseReleaseEvent(self, e):        
        if self.f_auto_edge and self.last_pressed_node != 0 and self.option == 0 and self.f_moved:
            self.net.recalculate_edges([self.last_pressed_node.net_node])
            self.draw_recalc_edges(self.last_pressed_node.net_node)
            
        self.f_move = False
        self.f_moved = False
    
class Node(QGraphicsEllipseItem):
    def __init__(self, x, y, size, node_id, node_label, comm_range, net_node):
        super(self.__class__, self).__init__(x, y, size, size)
        
        self.setFlags(QGraphicsEllipseItem.ItemIsMovable)    
        
        self.node_id = node_id
        self.comm_range = comm_range
        self.net_node = net_node
        self.set_iniXY(x + size/2, y + size/2)
        
        self.edges = list()
        self.node_label = node_label

    def get_X(self):
        return self.x() + self.iniX
    
    def get_Y(self):
        return self.y() + self.iniY
        
    def get_iniX(self):
        return self.iniX
    
    def get_iniY(self):
        return self.iniY
        
    def add_edge_to_list(self, edge):
        self.edges.append(edge)
        
    def remove_edge_from_list(self, edge):
        self.edges.remove(edge)

    def set_iniXY(self, iniX, iniY):
        self.iniX = iniX
        self.iniY = iniY
    
    def set_comm_range(self, comm_range):
        self.comm_range = comm_range

class Label(QGraphicsTextItem):
    def __init__(self, text, x, y):
        super(self.__class__, self).__init__(text)
        
        self.setPos(x, y)
  
class Edge(QGraphicsLineItem):
    def __init__(self, node1, node2):
        super(self.__class__, self).__init__(node1.x() + node1.get_iniX(), node1.y() + node1.get_iniY(), node2.x() + node2.get_iniX(), node2.y() + node2.get_iniY())
        
        pen = QPen()
        pen.setWidth(2)
        self.setPen(pen)
        
        self.node1 = node1
        self.node2 = node2
    
class Radius(QGraphicsEllipseItem):
    def __init__(self, x, y, size):
        super(self.__class__, self).__init__(x - size, y - size, size * 2, size * 2)
        
        self.pen = QPen(QtCore.Qt.black, 1, QtCore.Qt.DashLine)
        self.setPen(self.pen)
        
        self.iniX = x
        self.iniY = y
        
    def get_iniX(self):
        return self.iniX
        
    def get_iniY(self):
        return self.iniY
    
    def get_X(self):
        return self.x() + self.iniX
    
    def get_Y(self):
        return self.y() + self.iniY

def main():
    app = QApplication(sys.argv)  
    form = ManageNet()  
    form.show()
    app.exec_() 


if __name__ == '__main__': 
    main()