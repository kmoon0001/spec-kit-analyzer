            
try:
                headers = {"Authorization": f"Bearer {self.access_token}"}
                payload = {"current_password": current_password, "new_password": new_password}
                response = requests.post(f"{API_URL}/auth/users/change-password", json=payload, headers=headers)
                response.raise_for_status()
                QMessageBox.information(self, "Success", "Password changed successfully.")
            except requests.exceptions.RequestException as e:
                detail = e.response.json().get('detail', str(e)) if e.response else str(e)
                QMessageBox.critical(self, "Error", f"Failed to change password: {detail}")
    def load_dashboard_data(self):
        self.status_bar.showMessage("Refreshing dashboard data...")
        self.thread = QThread()
        self.worker = DashboardWorker(self.access_token)
        self.worker.moveToThread(self.thread)
        self.worker.success.connect(self.on_dashboard_data_loaded)
        self.worker.error.connect(lambda msg: self.status_bar.showMessage(f"Dashboard Error: {msg}"))
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()
    def on_dashboard_data_loaded(self, data):
        self.dashboard_widget.update_dashboard(data)
        self.status_bar.showMessage("Dashboard updated.", 3000)
    def run_analysis(self):
        if not self._current_file_path:
            return
        self.progress_bar.setRange(0, 0)
        self.progress_bar.show()
        self.run_analysis_button.setEnabled(False)
        self.status_bar.showMessage("Starting analysis...")
        self.thread = QThread()
        self.worker = AnalysisStarterWorker(self._current_file_path, {}, self.access_token)
        self.worker.moveToThread(self.thread)
        self.worker.success.connect(self.handle_analysis_started)
        self.worker.error.connect(self.on_analysis_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()
    def handle_analysis_started(self, task_id: str):
        self.status_bar.showMessage(f"Analysis in progress... (Task ID: {task_id})")
        self.run_analysis_threaded(task_id)
    def run_analysis_threaded(self, task_id: str):
        self.thread = QThread()
        self.worker = AnalysisWorker(self._current_file_path, {}, task_id)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.success.connect(self.on_analysis_success)
        self.worker.error.connect(self.on_analysis_error)
        self.worker.progress.connect(self.on_analysis_progress)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()
    def on_analysis_progress(self, progress):
        self.progress_bar.setValue(progress)
    def on_analysis_success(self, result):
        self.progress_bar.hide()
        self.analysis_results_area.setText(result)
        self.status_bar.showMessage("Analysis complete.")
        self.run_analysis_button.setEnabled(True)
    def on_analysis_error(self, error_message):
        self.progress_bar.hide()
        QMessageBox.critical(self, "Analysis Error", error_message)
        self.status_bar.showMessage("Backend analysis failed.")
        self.run_analysis_button.setEnabled(True)
    def open_file_dialog(self):
        file_name, _ = QFileDialog.getOpenFileName(self, 'Select Document', '', 'All Files (*.*)')
        if file_name:
            self._current_file_path = file_name
            self.status_bar.showMessage(f"Loaded document: {os.path.basename(file_name)}")
            self.run_analysis_button.setEnabled(True)
            try:
                with open(file_name, 'r', encoding='utf-8') as f:
                    self.document_display_area.setText(f.read())
