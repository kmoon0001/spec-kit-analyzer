# ⚙️ Performance Guide

This guide provides a comprehensive overview of the performance management features in the Therapy Compliance Analyzer. These features are designed to optimize the application for a wide range of hardware configurations, from business laptops to high-end workstations, while ensuring a smooth user experience.

## Overview of Performance Management

The application includes a sophisticated performance management system that automatically adapts to your computer's capabilities. It balances resource usage (RAM, CPU, GPU) to provide the best possible performance without slowing down your system.

Key components of the performance system include:
-   **Adaptive Performance Profiles**: Automatically configures the application based on your system's hardware.
-   **Real-time Monitoring**: Provides live feedback on memory usage and system status.
-   **Intelligent Caching**: Speeds up repetitive tasks by caching frequently accessed data.
-   **Advanced Optimizations**: Includes features like GPU acceleration, model quantization, and parallel processing.

## Performance Profiles

The application uses three performance profiles to manage resource consumption. These profiles are set automatically based on your system's available RAM, but can be manually adjusted.

-   **Conservative (6-8GB RAM)**:
    -   **Processing**: CPU-only
    -   **Models**: Quantized for lower memory usage
    -   **Caching**: Minimal (up to 1GB)
    -   **Best for**: Laptops or systems with limited resources.

-   **Balanced (8-12GB RAM)**:
    -   **Processing**: CPU-based with optional GPU acceleration
    -   **Models**: Efficient processing models
    -   **Caching**: Moderate (up to 2GB)
    -   **Best for**: Standard workstations and most users.

-   **Aggressive (12-16GB+ RAM)**:
    -   **Processing**: Full GPU acceleration
    -   **Models**: High-performance models
    -   **Caching**: Large (4GB+)
    -   **Best for**: High-end systems where maximum performance is desired.

## How to Configure Performance Settings

You can access and customize the performance settings in the application:

1.  **Menu Access**: Navigate to `Tools → Performance Settings` from the main menu.
2.  **Status Bar**: Click the gear icon (⚙️) in the performance status widget at the bottom of the window.

### Performance Settings Dialog

The settings dialog is organized into three tabs:

-   **Performance Profiles**:
    -   Select one of the predefined profiles (Conservative, Balanced, Aggressive).
    -   View system recommendations based on your detected hardware.
    -   Use the "Auto-Detect Optimal" button to have the application choose the best settings for you.

-   **Advanced Settings**:
    -   **Memory Management**: Fine-tune cache sizes and memory limits.
    -   **AI/ML Settings**: Toggle GPU usage, model quantization, and adjust batch sizes.
    -   **Processing**: Configure parallel processing and chunk sizes.
    -   **Database**: Adjust connection pooling settings.

-   **System Monitor**:
    -   View real-time information about your system's hardware.
    -   Monitor live memory usage and other performance metrics.

## Best Practices for Optimal Performance

-   **For Business Laptops (6-8GB RAM)**:
    -   Use the **Conservative** profile.
    -   Keep cache sizes small (1GB or less).
    -   If the system feels slow, disable parallel processing in the Advanced Settings.

-   **For Workstations (8-12GB RAM)**:
    -   The **Balanced** profile is the recommended default.
    -   Enable GPU acceleration in the Advanced Settings if you have a supported GPU.

-   **For High-End Systems (12-16GB+ RAM)**:
    -   Use the **Aggressive** profile for the fastest analysis times.
    -   Ensure you have the latest GPU drivers installed for the best results.

## Troubleshooting Performance Issues

-   **High Memory Usage**:
    -   Switch to a more conservative performance profile.
    -   Reduce the cache size in the Advanced Settings.
    -   Close other resource-intensive applications.

-   **Slow Analysis Performance**:
    -   If your hardware supports it, switch to the **Aggressive** profile.
    -   Enable GPU acceleration in the Advanced Settings.

-   **Application Freezing**:
    -   Reduce the number of workers or disable parallel processing in the Advanced Settings.
    -   Restart the application to clear caches and reset the system.