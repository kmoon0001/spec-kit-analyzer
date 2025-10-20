import React, { Component, ErrorInfo, ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo);

    this.setState({
      error,
      errorInfo,
    });

    // Report error to monitoring service
    this.props.onError?.(error, errorInfo);

    // Report to diagnostics store
    import("../../store/useDiagnosticsStore")
      .then(({ useDiagnosticsStore }) => {
        useDiagnosticsStore.getState().pushEvent({
          message: error.message,
          severity: "error",
          source: "window-error",
          stack: error.stack,
          context: {
            componentStack: errorInfo.componentStack,
            errorBoundary: true,
          },
        });
      })
      .catch((e) =>
        console.warn("Failed to report error to diagnostics store:", e),
      );
  }

  private handleRetry = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
  };

  private handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="error-boundary">
          <div className="error-boundary__container">
            <h2 className="error-boundary__title">Something went wrong</h2>
            <p className="error-boundary__message">
              An unexpected error occurred. You can try to recover or reload the
              application.
            </p>

            {process.env.NODE_ENV === "development" && this.state.error && (
              <details className="error-boundary__details">
                <summary>Error Details (Development)</summary>
                <pre className="error-boundary__stack">
                  {this.state.error.toString()}
                  {this.state.errorInfo?.componentStack}
                </pre>
              </details>
            )}

            <div className="error-boundary__actions">
              <button
                onClick={this.handleRetry}
                className="error-boundary__button error-boundary__button--primary"
              >
                Try Again
              </button>
              <button
                onClick={this.handleReload}
                className="error-boundary__button error-boundary__button--secondary"
              >
                Reload Application
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Network Error Boundary for API-related errors
interface NetworkErrorBoundaryProps {
  children: ReactNode;
  fallback?: (error: Error, retry: () => void) => ReactNode;
}

interface NetworkErrorBoundaryState {
  hasNetworkError: boolean;
  networkError?: Error;
}

export class NetworkErrorBoundary extends Component<
  NetworkErrorBoundaryProps,
  NetworkErrorBoundaryState
> {
  constructor(props: NetworkErrorBoundaryProps) {
    super(props);
    this.state = { hasNetworkError: false };
  }

  static getDerivedStateFromError(error: Error): NetworkErrorBoundaryState {
    // Check if this is a network-related error
    const isNetworkError =
      error.message.includes("Network Error") ||
      error.message.includes("fetch") ||
      error.message.includes("connection") ||
      error.name === "NetworkError";

    if (isNetworkError) {
      return {
        hasNetworkError: true,
        networkError: error,
      };
    }

    // Re-throw non-network errors
    throw error;
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error(
      "NetworkErrorBoundary caught a network error:",
      error,
      errorInfo,
    );
  }

  private handleRetry = () => {
    this.setState({ hasNetworkError: false, networkError: undefined });
  };

  render() {
    if (this.state.hasNetworkError && this.state.networkError) {
      if (this.props.fallback) {
        return this.props.fallback(this.state.networkError, this.handleRetry);
      }

      return (
        <div className="network-error-boundary">
          <div className="network-error-boundary__container">
            <h3 className="network-error-boundary__title">
              Connection Problem
            </h3>
            <p className="network-error-boundary__message">
              Unable to connect to the server. Please check your connection and
              try again.
            </p>
            <button
              onClick={this.handleRetry}
              className="network-error-boundary__button"
            >
              Retry Connection
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Async Error Boundary Hook for handling promise rejections
export const useAsyncError = () => {
  const [, setError] = React.useState();

  return React.useCallback(
    (error: Error) => {
      setError(() => {
        throw error;
      });
    },
    [setError],
  );
};

// Global error handler setup
export const setupGlobalErrorHandlers = () => {
  // Handle unhandled promise rejections
  window.addEventListener("unhandledrejection", (event) => {
    console.error("Unhandled promise rejection:", event.reason);

    // Report to diagnostics store
    import("../../store/useDiagnosticsStore")
      .then(({ useDiagnosticsStore }) => {
        useDiagnosticsStore.getState().pushEvent({
          message: event.reason?.message || "Unhandled promise rejection",
          severity: "error",
          source: "unhandled-rejection",
          stack: event.reason?.stack,
          context: {
            reason: event.reason,
            promise: event.promise,
          },
        });
      })
      .catch((e) =>
        console.warn("Failed to report error to diagnostics store:", e),
      );
  });

  // Handle general errors
  window.addEventListener("error", (event) => {
    console.error("Global error:", event.error);

    // Report to diagnostics store
    import("../../store/useDiagnosticsStore")
      .then(({ useDiagnosticsStore }) => {
        useDiagnosticsStore.getState().pushEvent({
          message: event.error?.message || event.message,
          severity: "error",
          source: "window-error",
          stack: event.error?.stack,
          context: {
            filename: event.filename,
            lineno: event.lineno,
            colno: event.colno,
          },
        });
      })
      .catch((e) =>
        console.warn("Failed to report error to diagnostics store:", e),
      );
  });
};
