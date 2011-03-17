# Copyright (c) 2010-2011 Michael Pöhn
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

#! /usr/bin/env python
# -*- coding: utf-8 -*-

import math
import gtk
import glib
import pyglet.media
import xml.dom.minidom

class gmgbPlayer(pyglet.media.Player):
	
	def __init__(self, gui):
		super(gmgbPlayer,self).__init__()
		self.playerGui = gui
		
		self.desired_volume = 0.0
		
		self.current_file = ""
		
	
	def on_eos(self):
		self.seek(0.01) # hack for pyglet, to unskew the Player.time variable after looping
		if self.eos_action == pyglet.media.Player.EOS_PAUSE:
			self.playerGui.playButton.set_active(False)
		elif self.eos_action == pyglet.media.Player.EOS_LOOP:
			self.play()
	
	def load(self, file_path):
		current_file = file_path
		self.mediaSource = pyglet.media.load(file_path)
		self.playerGui.playbackSlider.set_range(0.0,self.mediaSource.duration)
		self.next()
		self.queue(self.mediaSource)
		#self.on_eos = self.on_eos
		self.eos_action = pyglet.media.Player.EOS_PAUSE
		
	def seek(self,timestamp):
		super(gmgbPlayer,self).seek(timestamp)
	
	def play(self):
		super(gmgbPlayer,self).play()
	
	def pause(self):
		super(gmgbPlayer,self).pause()
	
	def set_volume(self, new_volume):
		self.volume = new_volume
		self.desired_volume = new_volume
	
	def tick(self):
		try:
			self.playerGui.playbackSlider.set_value(self.time)
		except:
			pass

class PlayerSlot(gtk.Table):
	def __init__(self, gui):
		super(PlayerSlot, self).__init__(1,15,True)
		
		self.gmgb_gui = gui
				
		self.mediaPlayer = gmgbPlayer(self)
		
		self.fb_needs_reload = False # workaround flag for gtk drag-drop bug
		self.fb = gtk.FileChooserButton("select a audio file", backend=None)
		self.fileFilter = gtk.FileFilter()
		self.fileFilter.set_name("Audio Files")
		self.fileFilter.add_pattern("*.ogg")
		self.fileFilter.add_pattern("*.mp3")
		self.fileFilter.add_pattern("*.wav")
		self.fb.set_filter(self.fileFilter)
		self.fb.connect("file-set",self.load_file)
		#self.fb.connect("drag-motion",self.load_file_drag_motion)
		#self.fb.connect("drag-leave",self.load_file_drag_leave)
		self.attach(self.fb,0,4,0,1)
		
		self.playButton = gtk.ToggleToolButton(gtk.STOCK_MEDIA_PLAY)
		self.playButton.set_sensitive(False)
		self.playButton.connect("toggled",self.toggle_play)
		self.attach(self.playButton,4,5,0,1)
		
		self.loopButton = gtk.ToggleToolButton(gtk.STOCK_UNDO)
		self.loopButton.set_sensitive(False)
		self.loopButton.connect("toggled",self.toggle_loop)
		self.attach(self.loopButton,5,6,0,1)
		
		self.playbackSlider = gtk.HScale()
		self.playbackSlider.set_sensitive(False)
		self.playbackSlider.set_draw_value(False)
		self.playbackSlider.set_update_policy(gtk.UPDATE_DISCONTINUOUS)
		self.playbackSlider_dragged = False
		self.playbackSlider.connect("button-press-event",self.slider_button_press)
		self.playbackSlider.connect("button-release-event",self.slider_button_release)
		self.attach(self.playbackSlider,6,14,0,1)
		
		self.volumeButton = gtk.VolumeButton()
		self.volumeButton.set_sensitive(False)
		self.volumeButton.connect("value-changed",self.volume_change)
		self.attach(self.volumeButton,14,15,0,1)
		
	def slider_button_press(self,ps,evt):
		#print "begin drag"
		self.playbackSlider_dragged = True
	
	def	slider_button_release(self,ps,evt):
		#print "end drag"
		self.playbackSlider_dragged = False
		slider_value = self.playbackSlider.get_value()
		if math.fabs(self.mediaPlayer.time - slider_value) > 1:
			seek_to = min(self.playbackSlider.get_value(),self.mediaPlayer.mediaSource.duration-0.1)
			seek_to = max(seek_to,0.01) # hack for pyglet, to unskew the Player.time variable after looping
			self.mediaPlayer.seek(seek_to)
			if self.playButton.get_active():
				self.mediaPlayer.play()
	
	
	#def load_file_drag_motion(self,fb,drag_context, x, y, timestamp):
	#	#print "drag-motion "+str(drag_context.targets)
	#	return False
	
	#def load_file_drag_leave(self,fb,drag_context, x, y, timestamp):
	#	#print "drag-leave"
	#	return False
	
	def load_file(self,fb):
		
		# set filter again due to gtk drag-drop bug
		self.fileFilter = gtk.FileFilter()
		self.fileFilter.set_name("Audio Files")
		self.fileFilter.add_pattern("*.ogg")
		self.fileFilter.add_pattern("*.mp3")
		self.fileFilter.add_pattern("*.wav")
		self.fb.set_filter(self.fileFilter)
		
		if fb.get_filename() == None:
			self.fb_needs_reload = True
			if self.mediaPlayer.current_file != "":
				fb.set_filename(self.mediaPlayer.current_file)
		else:
			print "load_file: " + fb.get_file().get_path()
			self.playButton.set_sensitive(True)
			self.playButton.set_label(gtk.STOCK_MEDIA_PLAY)
			self.loopButton.set_sensitive(True)
			self.loopButton.set_active(False)
			self.playbackSlider.set_sensitive(True)
			self.volumeButton.set_sensitive(True)
			self.volumeButton.set_value(0.75)
			self.mediaPlayer.load(fb.get_filename())
		
	
	def toggle_play(self,playButton):
		
		if playButton.get_active():
			print "play: " + self.fb.get_filename()
			playButton.set_stock_id(gtk.STOCK_MEDIA_PAUSE)
			self.fb.set_sensitive(False)
			self.mediaPlayer.play()
			
		else:
			print "stop: " + self.fb.get_filename()
			playButton.set_stock_id(gtk.STOCK_MEDIA_PLAY)
			self.fb.set_sensitive(True)
			self.mediaPlayer.pause()
	
	def toggle_loop(self,loopButton):
		if loopButton.get_active():
			self.mediaPlayer.eos_action = pyglet.media.Player.EOS_LOOP
		else:
			self.mediaPlayer.eos_action = pyglet.media.Player.EOS_PAUSE
	
	
	def volume_change(self,volumeButton,new_value):
		self.mediaPlayer.set_volume(new_value)
		
	def get_xml(self):
		r  = "<PlayerSlot>\n"
		if self.fb.get_filename() != None:
			r += "<filePath>"+self.fb.get_filename()+"</filePath>\n"
		else:
			r += "<filePath></filePath>\n"
		r +=     "<loop>"+str(self.loopButton.get_active())+"</loop>\n"
		r +=     "<volume>"+str(self.volumeButton.get_value())+"</volume>\n"
		r += "</PlayerSlot>"
		return r
	
	def tick(self):
		
		if self.fb_needs_reload:
			self.fb_needs_reload = False
			self.load_file(self.fb)
		
		try:
			self.playbackSlider.set_value(self.mediaPlayer.time)
		except:
			pass

class GameMasterGhettoBlasterGUI(gtk.Window):
	def __init__(self):
		super(GameMasterGhettoBlasterGUI, self).__init__()
		
		self.TICK_INTERVAL = 5
		glib.timeout_add(self.TICK_INTERVAL, self.tick)
		
		# Window Details
		
		self.set_title("Game Master Ghetto Blaster")
		self.icon_play = self.render_icon(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_DIALOG)
		self.set_icon(self.icon_play)
		self.connect("destroy", self.quit)
		self.set_size_request(512, 512)
		self.set_position(gtk.WIN_POS_CENTER)
		
		# Menu
		
		self.menu_file_menu = gtk.Menu()
		
		file_open = gtk.ImageMenuItem("gtk-open")
		self.menu_file_menu.append(file_open)
		
		file_save = gtk.ImageMenuItem("gtk-save")
		self.menu_file_menu.append(file_save)
		
		file_quit = gtk.ImageMenuItem("gtk-quit")
		file_quit.connect("activate",self.quit)
		self.menu_file_menu.append(file_quit)
		
		self.menu_file = gtk.MenuItem("_File")
		self.menu_file.set_submenu(self.menu_file_menu)
		
		
		self.menu_bar = gtk.MenuBar()
		self.menu_bar.append(self.menu_file)
		
		# Player List
		
		self.playerList=gtk.Table(1,1,True)
		
		self.playerSlots = {}
		
		for i in range(16):
			self.playerSlots[i] = PlayerSlot(self)
			self.playerList.attach(self.playerSlots[i],0,1,i,i+1)
		
		# assemble Window
		
		vbox = gtk.VBox()
		vbox.pack_start(self.menu_bar, False, False)
		vbox.pack_end(self.playerList, True, True)
		
		self.add(vbox)
		
		self.show_all()
	
	def menu_file_open(self,menuItem):
		print "open"
	
	def menu_file_save(self,menuItem):
		print "save"
	
	#def menu_file_quit(self,menuItem):
	#	self.quit()
	
	def quit(self,arg1=None,arg2=None,arg3=None):
		#TODO: save everthing
		gtk.main_quit()
	
	def tick(self):
		pyglet.clock.tick()
		for i, p in self.playerSlots.iteritems():
			if p.playbackSlider_dragged == False:
				#p.playbackSlider.set_value(p.mediaPlayer.time)
				p.tick()
				#print "gmgb tick "+str(p.mediaPlayer.time)
		return True
	

if __name__ == "__main__":
	
	gmgb_gui = GameMasterGhettoBlasterGUI()
	gtk.main()

