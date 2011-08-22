#! /usr/bin/env python
# -*- coding: utf-8 -*-

import re
import io
import os
import ConfigParser
import threading
import time
import textwrap
import math
import gtk
import glib
import pyglet.media

class gmgbAudioPlayer():
	
	def __init__(self, file_path):
		#pyglet.media.Player.__init__(self)
		self.pyglet_player = pyglet.media.Player()
		self.load_file( file_path )
		
	
	def load_file(self, file_path):
		self.pyglet_player.mediaSource = pyglet.media.load(file_path)
		self.pyglet_player.next()
	
	def play(self):
		self.pyglet_player.play()
		 

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
		
		# get config reference
		conf = gmgbConfig()
		
		# Window Details
		
		self.set_title("Game Master Ghetto Blaster")
		self.icon_play = self.render_icon(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_DIALOG)
		self.set_icon(self.icon_play)
		self.connect("destroy", self.quit)
		#self.set_position(gtk.WIN_POS_CENTER)
		self.set_size_request(512,256)
		self.set_default_size(conf._conf['window_width'], conf._conf['window_height'])
		self.move(conf._conf['window_pos_x'], conf._conf['window_pos_y'])
		self.connect('configure-event',self.configure_event)
		
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
	
	def configure_event(self,window,new_param):
		conf = gmgbConfig()
		conf._conf['window_width']  = new_param.width
		conf._conf['window_height'] = new_param.height
		conf._conf['window_pos_x']  = new_param.x
		conf._conf['window_pos_y']  = new_param.y
	
	def quit(self,arg1=None,arg2=None,arg3=None):
		
		conf = gmgbConfig()
		
		# save all changes in program state and configuration
		conf.save()
		
		gtk.main_quit()
	
	def tick(self):
		#pyglet.clock.tick()
		for i, p in self.playerSlots.iteritems():
			if p.playbackSlider_dragged == False:
				#p.playbackSlider.set_value(p.mediaPlayer.time)
				p.tick()
				#print "gmgb tick "+str(p.mediaPlayer.time)
		return True

class PygletTicker(threading.Thread):
	'''
		This class ticks pyglet.
		It has to be ticked because pyglet fills the audio playback buffers from
		within it's main loop. Since we use gtks main loop we have to tick
		pyglet manual.
	'''
	
	def __init__(self):
		threading.Thread.__init__(self)
		self.daemon = True
	
	def run(self):
		try:
			while True:
				time.sleep(0.01)
				pyglet.clock.tick()
		except:
			pass




class gmgbConfig():
	'''
		this class offers a persistant storage for playlists and configurations.
		(singleton)
	'''
	def __init__(self):
			
		self.__conf_path = os.path.expanduser('~/.gmgb.conf')
			
		# initial load, also sets up _conf and _playlists!
		self.load()
		
	
	def load(self):
		'''
			loads all data from the config file into this object
		'''
		
		self._conf = {}
		self._playlists = {}
		
		scp = ConfigParser.SafeConfigParser()
		
		# default config
		scp.readfp(io.BytesIO(textwrap.dedent('''
			[__gmgb_config]
			window_width=512
			window_height=512
			window_pos_x=100
			window_pos_y=20
			
			[blaafoo]
			0_path=/home/michl/Musik/liam lynch - whatever.ogg
			0_repeat=true'''
		)))
		
		# parse config file
		scp.read(self.__conf_path) 
		
		
		# copy configuration
		self._conf['window_width']  = scp.getint('__gmgb_config','window_width')
		self._conf['window_height'] = scp.getint('__gmgb_config','window_height')
		
		self._conf['window_pos_x'] = scp.getint('__gmgb_config','window_pos_x')
		self._conf['window_pos_y'] = scp.getint('__gmgb_config','window_pos_y')
		
		# copy playlists
		scp.remove_section('__gmgb_config')
		for playlist_name in scp.sections():
			self._playlists[playlist_name] = []
			#print 'playlist: '+playlist_name
			for (key, value) in scp.items(playlist_name):
				key_split = re.split('_',key,maxsplit=1)
				if len(key_split) == 2:
					try:
						self._playlists[playlist_name][int(key_split[0])]
					except:
						self._playlists[playlist_name].insert(int(key_split[0]),{})
						#print 'fail ' + key_split[0]
					finally:
						self._playlists[playlist_name][int(key_split[0])][key_split[1]] = value
						#print key+': '+value

	
	def save(self):
		'''
			saves all data to the config file
		'''
		
		scp = ConfigParser.ConfigParser()
		
		for (playlist_name, playlist) in self._playlists.items():
			scp.add_section(playlist_name)
			for playlist_index in range(len(playlist)):
				for (key, value) in playlist[playlist_index].items():
					scp.set(playlist_name,str(playlist_index)+'_'+key,value)
		
		scp.add_section('__gmgb_config')
		for (key, value) in self._conf.items():
			scp.set('__gmgb_config',str(key),str(value))
		
		print 'saving state and configuration to ' + self.__conf_path
		with open(self.__conf_path, 'wb') as configfile:
			scp.write(configfile)
		
# singleton constructor fake function for gmgbConfig
gmgbConfig = lambda single_gmgbConfig=gmgbConfig(): single_gmgbConfig



if __name__ == "__main__":
	
	# prevent gtk form blocking our threads.
	gtk.gdk.threads_init()
	
	# get config handler
	conf = gmgbConfig()
	
	# initialize our gtk gui
	gmgb_gui = GameMasterGhettoBlasterGUI()
	
	# make pyglet audio playback capeable.
	pyglet_ticker = PygletTicker()
	pyglet_ticker.start()
	
	gtk.main()
	
	

