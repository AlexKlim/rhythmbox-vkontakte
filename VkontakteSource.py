from gi.repository import GObject, Gio, GLib, Peas, Gtk
from gi.repository import RB

from VkontakteSearch import VkontakteSearch

class VkontakteSource(RB.Source):
  def __init__(self, **kwargs):
    super(VkontakteSource, self).__init__(kwargs)
    self.initialised = False
    self.downloading = False
    self.download_queue = []
    self.__load_current_size = 0
    self.__load_total_size = 0
    self.error_msg = ''

  def initialise(self):
    shell = self.props.shell

    entry_view = RB.EntryView.new(db=shell.props.db, shell_player=shell.props.shell_player, is_drag_source=True, is_drag_dest=False)
    #entry_view.activate()
    #entry_view.add_events(0)
    entry_view.append_column(RB.EntryViewColumn.TITLE, True)
    entry_view.append_column(RB.EntryViewColumn.ARTIST, True)
    entry_view.append_column(RB.EntryViewColumn.DURATION, True)
    entry_view.set_sorting_order("Title", Gtk.SortType.ASCENDING)
    entry_view.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    self.entry_view = entry_view

    search_entry = Gtk.Entry()
    search_entry.set_width_chars(20)
    search_entry.set_activates_default(True)

    search_by_name = Gtk.Entry()
    search_by_name.set_width_chars(20)
    search_by_name.set_activates_default(False)

    self.search_entry = search_entry
    self.search_by_name = search_by_name

    search_button = Gtk.Button("Search")
    search_button.connect("clicked", self.on_search_button_clicked)
    search_button_by_name = Gtk.Button("Search User's Music")
    search_button_by_name.connect("clicked", self.on_search_button_clicked_by_name)

    search_button.set_can_default(True)
    self.search_button = search_button
    search_button_by_name.set_can_default(False)
    self.search_button_by_name = search_button_by_name

    hbox = Gtk.HBox()
    hbox.pack_start(search_entry, False, False, 0)
    hbox.pack_start(search_button, False, False, 5)
    hbox.pack_start(search_by_name, False, False, 5)
    hbox.pack_start(search_button_by_name, False, False, 5)

    vbox = Gtk.VBox()
    vbox.pack_start(hbox, False, False, 0)
    vbox.pack_start(entry_view, True, True, 5)

    self.pack_start(vbox, True, True, 0)
    self.show_all()

    #shell.get_ui_manager().ensure_update()
    self.initialised = True

  def do_impl_get_entry_view(self):
    return self.entry_view

  # rhyhtmbox api break up (0.13.2 - 0.13.3)
  def do_impl_activate(self):
    self.do_selected()

  def do_selected(self):
    if not self.initialised:
      self.initialise()
    self.search_button.grab_default()

  # rhyhtmbox api break up (0.13.2 - 0.13.3)
  def do_impl_get_status(self):
    return self.do_get_status()

  def do_get_status(self):
    if self.error_msg:
      error_msg = self.error_msg
      self.error_msg = ''
      return (error_msg, "", 1)
    if self.downloading:
      if self.__load_total_size > 0:
        # Got data
        progress = min (float(self.__load_current_size) / self.__load_total_size, 1.0)
      else:
        # Download started, no data yet received
        progress = -1.0
      str = "Downloading %s" % self.filename[:70]
      if self.download_queue:
        str += " (%s files more in queue)" % len(self.download_queue)
      return (str, "", progress)
    if self.current_search:
      if self.searches[self.current_search].is_complete():
        return (self.props.query_model.compute_status_normal("Found %d result", "Found %d results"), "", 1)
      else:
        return ("Searching for \"{0}\"".format(self.current_search), "", -1)

    else:
      return ("", "", 1)

  def do_impl_delete_thyself(self):
    if self.initialised:
      self.props.shell.props.db.entry_delete_by_type(self.props.entry_type)
    RB.Source.do_impl_delete_thyself(self)

  def do_impl_can_add_to_queue(self):
    return True

  def do_impl_can_pause(self):
    return True

  def on_search_button_clicked(self, button):
    entry = self.search_entry
    if entry.get_text():
      search = VkontakteSearch(entry.get_text(), self.props.shell.props.db, self.props.entry_type)
      # Start the search asynchronously
      GLib.idle_add(search.start, priority=GLib.PRIORITY_HIGH_IDLE)
      self.props.query_model = search.query_model
      self.entry_view.set_model(self.props.query_model)

  def on_search_button_clicked_by_name(self, button):
    entry = self.search_by_name
    if entry.get_text():
      search = VkontakteSearch(entry.get_text(), self.props.shell.props.db, self.props.entry_type)
      GLib.idle_add(search.start_by_name, priority=GLib.PRIORITY_HIGH_IDLE)
      self.props.query_model = search.query_model
      self.entry_view.set_model(self.props.query_model)

GObject.type_register(VkontakteSource)
