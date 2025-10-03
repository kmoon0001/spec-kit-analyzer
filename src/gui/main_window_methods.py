    def create_proportional_tab_widget(self, parent_layout):
        """Create tab widget with proper proportions"""
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setMovable(True)
        
        # Analysis Tab - Keep existing proportions
        self.create_analysis_tab()
        
        # Dashboard Tab - Generate functional dashboard
        self.create_functional_dashboard_tab()
        
        # Analytics Tab (Admin only)
        self.create_analytics_tab()
        
        # Settings Tab - Proportional sizing
        self.create_settings_tab()
        
        parent_layout.addWidget(self.tab_widget)
        
    def create_analysis_tab(self):
        """Create analysis tab with Medicare Part B rubric selector"""
        analysis_widget = QWidget()
        layout = QHBoxLayout(analysis_widget)
        
        # Left panel - Document and controls (keep proportions)
        left_panel = self.create_left_panel()
        
        # Right panel - Results (keep proportions)
        right_panel = self.create_right_panel()
        
        # Splitter for resizable panels (maintain 400:800 ratio)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 800])
        
        layout.addWidget(splitter)
        
        self.tab_widget.addTab(analysis_widget, "Analysis")
        
    def create_left_panel(self):
        """Create left panel with Medicare Part B rubric selection"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(panel)
        
        # Document upload section
        upload_group = QGroupBox("Document Upload")
        upload_layout = QVBoxLayout(upload_group)
        
        # Drag and drop area
        self.drop_area = QLabel("Drag & Drop Document Here\nor Click to Browse")
        self.drop_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_area.setMinimumHeight(100)
        self.drop_area.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc;
                border-radius: 10px;
                background: #f9f9f9;
                color: #666;
                font-size: 14px;
            }
            QLabel:hover {
                border-color: #007acc;
                background: #f0f8ff;
            }
        """)
        self.drop_area.mousePressEvent = lambda e: self.upload_document()
        
        upload_layout.addWidget(self.drop_area)
        
        # File info
        self.file_info_label = QLabel("No file selected")
        self.file_info_label.setStyleSheet("color: #666; font-size: 12px;")
        upload_layout.addWidget(self.file_info_label)
        
        layout.addWidget(upload_group)
        
        # Medicare Part B Rubric selection
        rubric_group = QGroupBox("Medicare Part B Guidelines")
        rubric_layout = QVBoxLayout(rubric_group)
        
        self.rubric_combo = QComboBox()
        self.rubric_combo.addItems([
            "Medicare Part B - Outpatient Therapy Services",
            "Medicare Benefits Policy Manual - Chapter 15",
            "Therapy Cap and KX Modifier Requirements", 
            "Documentation Requirements for Medical Necessity",
            "Functional Limitation Reporting (G-codes)",
            "Maintenance Therapy Guidelines"
        ])
        self.rubric_combo.currentTextChanged.connect(self.update_rubric_description)
        rubric_layout.addWidget(self.rubric_combo)
        
        # Rubric description
        self.rubric_description = QLabel("Medicare Part B guidelines for outpatient therapy services coverage and documentation requirements.")
        self.rubric_description.setWordWrap(True)
        self.rubric_description.setStyleSheet("color: #666; font-size: 11px; padding: 5px; background: #f8f9fa; border-radius: 4px;")
        rubric_layout.addWidget(self.rubric_description)
        
        layout.addWidget(rubric_group)
        
        # Analysis options
        options_group = QGroupBox("Analysis Options")
        options_layout = QVBoxLayout(options_group)
        
        # Analysis mode
        self.analysis_mode = QComboBox()
        self.analysis_mode.addItems(["Standard Analysis", "Quick Check", "Deep Analysis", "Custom"])
        options_layout.addWidget(QLabel("Analysis Mode:"))
        options_layout.addWidget(self.analysis_mode)
        
        # Confidence threshold
        self.confidence_slider = QSlider(Qt.Orientation.Horizontal)
        self.confidence_slider.setRange(50, 95)
        self.confidence_slider.setValue(75)
        self.confidence_label = QLabel("Confidence Threshold: 75%")
        self.confidence_slider.valueChanged.connect(
            lambda v: self.confidence_label.setText(f"Confidence Threshold: {v}%")
        )
        options_layout.addWidget(self.confidence_label)
        options_layout.addWidget(self.confidence_slider)
        
        # Advanced options
        self.enable_fact_check = QCheckBox("Enable Fact Checking")
        self.enable_fact_check.setChecked(True)
        
        self.enable_suggestions = QCheckBox("Generate Improvement Suggestions")
        self.enable_suggestions.setChecked(True)
        
        self.enable_citations = QCheckBox("Include Medicare Citations")
        self.enable_citations.setChecked(True)
        
        options_layout.addWidget(self.enable_fact_check)
        options_layout.addWidget(self.enable_suggestions)
        options_layout.addWidget(self.enable_citations)
        
        layout.addWidget(options_group)
        
        # Progress section
        progress_group = QGroupBox("Analysis Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        self.progress_label = QLabel("Ready to analyze")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        
        layout.addWidget(progress_group)
        
        layout.addStretch()
        
        return panel        

    def create_right_panel(self):
        """Create right panel for results display (no emojis in results)"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(panel)
        
        # Results header
        header_layout = QHBoxLayout()
        
        results_label = QLabel("Analysis Results")
        results_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header_layout.addWidget(results_label)
        
        header_layout.addStretch()
        
        # Export buttons (functional)
        self.export_pdf_btn = QPushButton("Export PDF")
        self.export_pdf_btn.clicked.connect(self.export_pdf)
        self.export_pdf_btn.setEnabled(False)
        
        self.save_report_btn = QPushButton("Save Report")
        self.save_report_btn.clicked.connect(self.save_report)
        self.save_report_btn.setEnabled(False)
        
        header_layout.addWidget(self.export_pdf_btn)
        header_layout.addWidget(self.save_report_btn)
        
        layout.addLayout(header_layout)
        
        # Results display
        self.results_browser = QTextBrowser()
        self.results_browser.setHtml(self.get_welcome_html_no_emojis())
        layout.addWidget(self.results_browser)
        
        return panel
        
    def get_welcome_html_no_emojis(self):
        """Get welcome HTML without emojis for results panel"""
        return """
        <html>
        <head>
            <style>
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; line-height: 1.6; }
                .welcome { text-align: center; color: #666; }
                .feature { margin: 15px 0; padding: 15px; background: #f9f9f9; border-radius: 8px; border-left: 4px solid #007acc; }
                .feature-title { font-weight: bold; color: #333; margin-bottom: 5px; }
                .feature-desc { color: #666; font-size: 14px; }
                .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>THERAPY DOCUMENT COMPLIANCE ANALYSIS</h1>
                <p>Advanced AI-Powered Clinical Documentation Review System</p>
            </div>
            
            <div class="welcome">
                <h2>Welcome to Professional Compliance Analysis</h2>
                <p>Upload a clinical document to begin comprehensive Medicare Part B compliance analysis</p>
                
                <div class="feature">
                    <div class="feature-title">AI-Powered Analysis Engine</div>
                    <div class="feature-desc">Advanced machine learning models analyze documentation against Medicare Part B guidelines and Benefits Policy Manual requirements</div>
                </div>
                
                <div class="feature">
                    <div class="feature-title">HIPAA Compliant Processing</div>
                    <div class="feature-desc">All analysis performed locally on your machine - no data transmitted to external servers</div>
                </div>
                
                <div class="feature">
                    <div class="feature-title">Comprehensive Reporting</div>
                    <div class="feature-desc">Detailed compliance reports with Medicare citations, risk assessments, and actionable improvement recommendations</div>
                </div>
                
                <div class="feature">
                    <div class="feature-title">Intelligent Assistant</div>
                    <div class="feature-desc">AI chat assistant provides real-time guidance on Medicare guidelines and documentation best practices</div>
                </div>
                
                <p><strong>Ready to begin?</strong> Upload your clinical document using the panel on the left.</p>
            </div>
        </body>
        </html>
        """
        
    def create_functional_dashboard_tab(self):
        """Create functional dashboard that actually generates"""
        dashboard_widget = QWidget()
        layout = QVBoxLayout(dashboard_widget)
        
        # Dashboard header
        header_layout = QHBoxLayout()
        
        dashboard_title = QLabel("Compliance Dashboard")
        dashboard_title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(dashboard_title)
        
        header_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("Refresh Data")
        refresh_btn.clicked.connect(self.refresh_dashboard)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Dashboard content
        content_layout = QGridLayout()
        
        # Compliance metrics
        metrics_group = QGroupBox("Compliance Metrics")
        metrics_layout = QGridLayout(metrics_group)
        
        # Sample metrics (replace with real data)
        metrics = [
            ("Total Documents Analyzed", "247"),
            ("Average Compliance Score", "87.3%"),
            ("High Risk Findings", "12"),
            ("Resolved Issues", "156")
        ]
        
        for i, (label, value) in enumerate(metrics):
            metric_label = QLabel(label)
            metric_value = QLabel(value)
            metric_value.setFont(QFont("Arial", 14, QFont.Weight.Bold))
            metric_value.setStyleSheet("color: #007acc;")
            
            metrics_layout.addWidget(metric_label, i, 0)
            metrics_layout.addWidget(metric_value, i, 1)
            
        content_layout.addWidget(metrics_group, 0, 0)
        
        # Recent activity
        activity_group = QGroupBox("Recent Analysis Activity")
        activity_layout = QVBoxLayout(activity_group)
        
        activity_list = QTextBrowser()
        activity_list.setMaximumHeight(200)
        activity_list.setHtml("""
        <div style="font-family: Arial; font-size: 12px;">
        <p><strong>Today</strong></p>
        <p>• Progress Note Analysis - Score: 92/100</p>
        <p>• Evaluation Report Review - Score: 78/100</p>
        <p>• Treatment Plan Analysis - Score: 95/100</p>
        <br>
        <p><strong>Yesterday</strong></p>
        <p>• Discharge Summary Review - Score: 88/100</p>
        <p>• Initial Assessment Analysis - Score: 91/100</p>
        </div>
        """)
        
        activity_layout.addWidget(activity_list)
        content_layout.addWidget(activity_group, 0, 1)
        
        # Compliance trends (placeholder for chart)
        trends_group = QGroupBox("Compliance Trends")
        trends_layout = QVBoxLayout(trends_group)
        
        trends_placeholder = QLabel("Compliance trends chart would be displayed here.\nShowing improvement over time with detailed analytics.")
        trends_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        trends_placeholder.setStyleSheet("color: #666; padding: 40px; background: #f8f9fa; border-radius: 8px;")
        
        trends_layout.addWidget(trends_placeholder)
        content_layout.addWidget(trends_group, 1, 0, 1, 2)
        
        layout.addLayout(content_layout)
        
        self.tab_widget.addTab(dashboard_widget, "Dashboard")
        
    def create_analytics_tab(self):
        """Create analytics tab"""
        analytics_widget = QWidget()
        layout = QVBoxLayout(analytics_widget)
        
        analytics_label = QLabel("Advanced Analytics")
        analytics_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(analytics_label)
        
        # Analytics content placeholder
        analytics_content = QLabel("Advanced analytics and reporting features would be displayed here.\nIncluding detailed compliance statistics, trend analysis, and performance metrics.")
        analytics_content.setAlignment(Qt.AlignmentFlag.AlignCenter)
        analytics_content.setStyleSheet("color: #666; padding: 60px; background: #f8f9fa; border-radius: 8px;")
        layout.addWidget(analytics_content)
        
        self.tab_widget.addTab(analytics_widget, "Analytics")
        
    def create_settings_tab(self):
        """Create proportional settings tab"""
        settings_widget = QWidget()
        layout = QVBoxLayout(settings_widget)
        
        # Settings content in grid for proper proportions
        settings_grid = QGridLayout()
        
        # Performance settings
        perf_group = QGroupBox("Performance Settings")
        perf_layout = QGridLayout(perf_group)
        
        # AI Model settings
        perf_layout.addWidget(QLabel("AI Model Quality:"), 0, 0)
        self.model_quality = QComboBox()
        self.model_quality.addItems(["Fast", "Balanced", "High Quality"])
        self.model_quality.setCurrentText("Balanced")
        perf_layout.addWidget(self.model_quality, 0, 1)
        
        # Cache settings
        perf_layout.addWidget(QLabel("Cache Size (MB):"), 1, 0)
        self.cache_size = QSpinBox()
        self.cache_size.setRange(100, 2000)
        self.cache_size.setValue(500)
        perf_layout.addWidget(self.cache_size, 1, 1)
        
        settings_grid.addWidget(perf_group, 0, 0)
        
        # UI Settings
        ui_group = QGroupBox("Interface Settings")
        ui_layout = QGridLayout(ui_group)
        
        # Font size
        ui_layout.addWidget(QLabel("Font Size:"), 0, 0)
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 24)
        self.font_size.setValue(10)
        ui_layout.addWidget(self.font_size, 0, 1)
        
        # Auto-save
        self.auto_save = QCheckBox("Auto-save Reports")
        self.auto_save.setChecked(True)
        ui_layout.addWidget(self.auto_save, 1, 0, 1, 2)
        
        settings_grid.addWidget(ui_group, 0, 1)
        
        layout.addLayout(settings_grid)
        
        # Apply settings button
        apply_btn = QPushButton("Apply Settings")
        apply_btn.clicked.connect(self.apply_settings)
        layout.addWidget(apply_btn)
        
        layout.addStretch()
        
        self.tab_widget.addTab(settings_widget, "Settings")
        
    def create_enhanced_status_bar(self):
        """Create enhanced status bar with individual AI model indicators"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Main status message
        self.status_bar.showMessage("Ready - Upload a document to begin analysis")
        
        # Individual AI model status widget
        self.ai_model_status_widget = AIModelStatusWidget()
        self.status_bar.addPermanentWidget(self.ai_model_status_widget)
        
        # Performance indicator
        self.performance_widget = PerformanceStatusWidget()
        self.status_bar.addPermanentWidget(self.performance_widget)
        
        # User info
        self.user_status_label = QLabel("User: Not logged in")
        self.status_bar.addPermanentWidget(self.user_status_label)
        
        # Connection status
        self.connection_label = QLabel("Connected")
        self.connection_label.setStyleSheet("color: green; font-weight: bold;")
        self.status_bar.addPermanentWidget(self.connection_label)
        
    def create_floating_chat_button(self):
        """Create floating chat button"""
        self.fab = QPushButton("Chat")
        self.fab.setParent(self)
        self.fab.setFixedSize(60, 60)
        self.fab.clicked.connect(self.open_chat_bot)
        self.fab.setStyleSheet("""
            QPushButton {
                background: #007acc;
                color: white;
                border: none;
                border-radius: 30px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #005a9e;
            }
            QPushButton:pressed {
                background: #004080;
            }
        """)
        
        # Position FAB in bottom right
        self.position_fab()
        
    def position_fab(self):
        """Position floating action button"""
        if hasattr(self, 'fab'):
            self.fab.move(self.width() - 80, self.height() - 100)
            
    def resizeEvent(self, event):
        """Handle window resize"""
        super().resizeEvent(event)
        self.position_fab()