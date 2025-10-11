import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import time
import threading
import webbrowser
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem, QLabel,
    QCheckBox, QTextBrowser, QTabWidget
)
from PyQt6.QtCore import QObject, QThread, pyqtSignal, QTimer, QSettings
from PyQt6.QtWidgets import QDialog, QFormLayout, QDialogButtonBox

# a qdialog is used for the advanced settings to make it a blocking window
class AdvancedSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Advanced Settings")

        self.layout = QFormLayout(self)

        self.arxiv_limit_input = QLineEdit("20")

        self.pubmed_limit_input = QLineEdit("20")
        self.ddg_limit_input = QLineEdit("20")

        self.layout.addRow("arXiv Limit:", self.arxiv_limit_input)

        self.layout.addRow("PubMed Limit:", self.pubmed_limit_input)
        self.layout.addRow("DuckDuckGo Limit:", self.ddg_limit_input)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.layout.addWidget(self.buttons)

    def get_limits(self):
        return {
            "arxiv": self.arxiv_limit_input.text(),
            "pubmed": self.pubmed_limit_input.text(),
            "ddg": self.ddg_limit_input.text(),
        }


from agents.search_agent import SearchAgent
from agents.extraction_agent import ExtractionAgent
from agents.storage_agent import StorageAgent

from logging_config import logger

# this worker runs in a separate thread to prevent the gui from freezing during searches
class AgentWorker(QObject):
    # pyqtsignals are used to communicate between the worker thread and the main gui thread
    finished = pyqtSignal()
    status_changed = pyqtSignal(str)

    pubmed_search_finished = pyqtSignal()
    general_web_papers_found = pyqtSignal(list)
    general_web_search_finished = pyqtSignal()

    def __init__(self, query, search_arxiv, search_pubmed, search_general, arxiv_limit, pubmed_limit, ddg_limit):
        super().__init__()
        self.query = query
        self.search_arxiv = search_arxiv
        self.search_pubmed = search_pubmed
        self.search_general = search_general
        self.arxiv_limit = arxiv_limit
        self.pubmed_limit = pubmed_limit
        self.ddg_limit = ddg_limit

    def run(self):
        logger.info("AgentWorker running...")
        blackboard = {
            "query": self.query,
            "papers": None,
            "extracted_data": [],
            "status": "running",
            "search_arxiv": self.search_arxiv,
            "search_pubmed": self.search_pubmed,
            "search_web": self.search_general,
            "arxiv_limit": self.arxiv_limit,
            "pubmed_limit": self.pubmed_limit,
            "ddg_limit": self.ddg_limit
        }
        search_agent = SearchAgent()
        extraction_agent = ExtractionAgent()
        pubmed_event = threading.Event()
        arxiv_event = threading.Event()
        web_event = threading.Event()



        def pubmed_callback(papers):
            logger.info("PubMed search finished.")
            total = len(papers)
            self.status_changed.emit(f"PubMed search returned {total} results. Now extracting details...")

            for i, paper in enumerate(papers):
                extraction_blackboard = {"papers": [paper]}
                extraction_agent.run(extraction_blackboard)

                self.pubmed_papers_found.emit([paper])
                self.status_changed.emit(f"Extracting PubMed paper {i+1} of {total}...")

            self.status_changed.emit("PubMed extraction complete.")
            self.pubmed_search_finished.emit()
            pubmed_event.set()

        def arxiv_callback(papers):
            logger.info("arXiv search finished.")
            self.status_changed.emit(f"arXiv search complete. Found {len(papers)} papers.")
            self.arxiv_papers_found.emit(papers)
            self.arxiv_search_finished.emit()
            arxiv_event.set()

        def web_callback(papers):
            logger.info("Web search finished.")
            total = len(papers)
            self.status_changed.emit(f"Web search returned {total} results. Now extracting details...")

            for i, paper in enumerate(papers):
                extraction_blackboard = {"papers": [paper]}
                extraction_agent.run(extraction_blackboard)

                abstract = paper.get('abstract')
                if abstract and abstract not in ['N/A', 'Fetch/Parse Error', 'API Error', 'Extraction Error', 'Fetch Error']:
                    self.general_web_papers_found.emit([paper])

                self.status_changed.emit(f"Extracting web paper {i+1} of {total}...")

            self.status_changed.emit("Web extraction complete.")
            self.general_web_search_finished.emit()
            web_event.set()

        logger.info("Starting search sources...")
        search_agent.search_sources(blackboard, pubmed_callback=pubmed_callback, pubmed_event=pubmed_event, arxiv_callback=arxiv_callback, arxiv_event=arxiv_event, web_callback=web_callback, web_event=web_event)

        def wait_for_all():
            logger.info("Waiting for all search threads to complete...")
            if self.search_arxiv:
                logger.info("Waiting for arXiv thread...")
                arxiv_event.wait()

            if self.search_pubmed:
                logger.info("Waiting for PubMed thread...")
                pubmed_event.wait()
            if self.search_general:
                logger.info("Waiting for web thread...")
                web_event.wait()
            self.status_changed.emit("All searches complete.")
            self.finished.emit()

        wait_thread = threading.Thread(target=wait_for_all)
        wait_thread.start()

# a custom widget is used for each paper to create a more complex layout than a simple list item
class PaperItemWidget(QWidget):
    def __init__(self, paper_data):
        super().__init__()
        self.paper_data = paper_data
        layout = QVBoxLayout()
        title = paper_data.get('title', 'No Title')
        source = paper_data.get('source', 'N/A')
        authors = paper_data.get('authors', [])
        abstract = paper_data.get('abstract', 'N/A')

        self.checkbox = QCheckBox(title)
        self.checkbox.setChecked(False)

        self.open_link_button = QPushButton("Open Link")
        self.open_link_button.clicked.connect(self.open_link)
        self.open_link_button.setFixedWidth(100)

        source_label = QLabel(f"<i>Source: {source}</i>")
        authors_label = QLabel(f"<i>Authors: {', '.join(authors) if authors else 'N/A'}</i>")

        self.setToolTip(abstract)

        layout.addWidget(self.checkbox)
        layout.addWidget(self.open_link_button)
        layout.addWidget(source_label)
        layout.addWidget(authors_label)
        self.setLayout(layout)

    def open_link(self):
        webbrowser.open(self.paper_data.get('url'))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Academic Research Assistant")
        self.setGeometry(100, 100, 800, 600)

        # qsettings is used to persist user settings across sessions
        self.settings = QSettings("MyCompany", "AcademicResearchAssistant")

        self.arxiv_limit = self.settings.value("arxiv_limit", 20, type=int)
        self.pubmed_limit = self.settings.value("pubmed_limit", 20, type=int)
        self.ddg_limit = self.settings.value("ddg_limit", 20, type=int)

        self.unique_papers = set()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        search_layout = QHBoxLayout()
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("Enter your research query...")
        self.search_button = QPushButton("Search")
        search_layout.addWidget(self.query_input)
        search_layout.addWidget(self.search_button)
        main_layout.addLayout(search_layout)

        options_layout = QHBoxLayout()
        self.arxiv_checkbox = QCheckBox("arXiv")
        self.arxiv_checkbox.setChecked(False)
        self.arxiv_loading_label = QLabel()

        self.pubmed_checkbox = QCheckBox("PubMed")
        self.pubmed_checkbox.setChecked(False)
        self.pubmed_loading_label = QLabel()
        self.general_web_checkbox = QCheckBox("DuckDuckGo")
        self.general_web_checkbox.setChecked(False)
        self.general_web_loading_label = QLabel()
        options_layout.addWidget(self.arxiv_checkbox)
        options_layout.addWidget(self.arxiv_loading_label)
        options_layout.addWidget(self.pubmed_checkbox)
        options_layout.addWidget(self.pubmed_loading_label)
        options_layout.addWidget(self.general_web_checkbox)
        options_layout.addWidget(self.general_web_loading_label)
        main_layout.addLayout(options_layout)

        self.advanced_settings_button = QPushButton("Advanced Settings")
        self.advanced_settings_button.clicked.connect(self.open_advanced_settings)
        main_layout.addWidget(self.advanced_settings_button)

        self.arxiv_loading_label.hide()
        self.pubmed_loading_label.hide()
        self.general_web_loading_label.hide()

        self.spinner_timer = QTimer(self)
        self.spinner_timer.timeout.connect(self.update_spinner)
        self.animation_chars = ["|", "/", "-", "\\"]
        self.char_index = 0

        # a qlistwidget is used to display the results as it is simple and efficient
        self.results_list = QListWidget()
        main_layout.addWidget(self.results_list)

        self.save_button = QPushButton("Save Selected to JSON")
        main_layout.addWidget(self.save_button)

        self.statusBar = self.statusBar()

        self.search_button.clicked.connect(self.start_search)
        self.query_input.returnPressed.connect(self.start_search)
        self.save_button.clicked.connect(self.save_selected)

    def open_advanced_settings(self):
        dialog = AdvancedSettingsDialog(self)
        dialog.arxiv_limit_input.setText(str(self.arxiv_limit))
        dialog.pubmed_limit_input.setText(str(self.pubmed_limit))
        dialog.ddg_limit_input.setText(str(self.ddg_limit))

        if dialog.exec():
            limits = dialog.get_limits()
            self.arxiv_limit = int(limits["arxiv"])
            self.pubmed_limit = int(limits["pubmed"])
            self.ddg_limit = int(limits["ddg"])

            self.settings.setValue("arxiv_limit", self.arxiv_limit)
            self.settings.setValue("pubmed_limit", self.pubmed_limit)
            self.settings.setValue("ddg_limit", self.ddg_limit)

    def start_search(self):
        query = self.query_input.text()
        if not query: return

        search_arxiv = self.arxiv_checkbox.isChecked()
        search_pubmed = self.pubmed_checkbox.isChecked()
        search_general = self.general_web_checkbox.isChecked()

        arxiv_limit = self.arxiv_limit
        pubmed_limit = self.pubmed_limit
        ddg_limit = self.ddg_limit

        self.search_button.setEnabled(False)
        self.results_list.clear()
        self.unique_papers.clear()
        self.statusBar.showMessage("Starting search...")

        if search_arxiv:
            self.arxiv_loading_label.show()
        if search_pubmed:
            self.pubmed_loading_label.show()

        self.spinner_timer.start(100)

        # each search is run in a separate thread to avoid blocking the gui
        self.thread = QThread()
        self.worker = AgentWorker(query, search_arxiv, search_pubmed, search_general, arxiv_limit, pubmed_limit, ddg_limit)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.arxiv_papers_found.connect(self.add_arxiv_papers)
        self.worker.pubmed_papers_found.connect(self.add_pubmed_papers)
        self.worker.general_web_papers_found.connect(self.add_general_web_papers)
        self.worker.status_changed.connect(self.handle_status_change)
        self.thread.finished.connect(lambda: self.search_button.setEnabled(True))

        self.worker.arxiv_search_finished.connect(self.handle_arxiv_finished)
        self.worker.pubmed_search_finished.connect(self.handle_pubmed_finished)
        self.worker.general_web_search_finished.connect(self.handle_general_web_finished)

        self.thread.start()

    def update_spinner(self):
        self.char_index = (self.char_index + 1) % len(self.animation_chars)
        char = self.animation_chars[self.char_index]
        if self.arxiv_loading_label.isVisible():
            self.arxiv_loading_label.setText(char)
        if self.pubmed_loading_label.isVisible():
            self.pubmed_loading_label.setText(char)

    def handle_arxiv_finished(self):
        self.arxiv_loading_label.hide()
        self.check_all_searches_finished()



    def handle_pubmed_finished(self):
        self.pubmed_loading_label.hide()
        self.check_all_searches_finished()

    def handle_general_web_finished(self):
        self.general_web_loading_label.hide()
        self.check_all_searches_finished()

    def check_all_searches_finished(self):
        if not self.arxiv_loading_label.isVisible() and \
           not self.pubmed_loading_label.isVisible() and \
           not self.general_web_loading_label.isVisible():
            self.spinner_timer.stop()

    def handle_status_change(self, status):
        if status == "clear_results":
            self.results_list.clear()
        else:
            self.statusBar.showMessage(status)

    def add_paper_item(self, paper_data):
        title = paper_data.get('title', 'No Title')
        authors = tuple(paper_data.get('authors', []))
        paper_tuple = (title, authors)

        if paper_tuple in self.unique_papers:
            return

        self.unique_papers.add(paper_tuple)

        logger.info(f"Adding paper to GUI: {paper_data.get('title')} - {paper_data.get('url')}")
        item = QListWidgetItem(self.results_list)
        widget = PaperItemWidget(paper_data)
        item.setSizeHint(widget.sizeHint())
        self.results_list.addItem(item)
        self.results_list.setItemWidget(item, widget)

    def add_arxiv_papers(self, papers):
        if not papers:
            return
        for paper in papers:
            self.add_paper_item(paper)



    def add_pubmed_papers(self, papers):
        if not papers:
            return
        for paper in papers:
            self.add_paper_item(paper)

    def add_general_web_papers(self, papers):
        if not papers:
            return
        for paper in papers:
            self.add_paper_item(paper)

    def save_selected(self):
        selected_papers = []
        for i in range(self.results_list.count()):
            item = self.results_list.item(i)
            widget = self.results_list.itemWidget(item)
            if widget.checkbox.isChecked():
                selected_papers.append(widget.paper_data)

        if not selected_papers:
            self.statusBar.showMessage("No papers selected to save.")
            return

        storage_agent = StorageAgent()
        blackboard = {"extracted_data": selected_papers}
        storage_agent.run(blackboard)
        self.statusBar.showMessage(f"Successfully saved {len(selected_papers)} papers.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
