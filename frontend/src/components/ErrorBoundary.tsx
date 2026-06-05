"use client";
import { Component, type ReactNode } from "react";

interface Props { children: ReactNode; fallbackLabel?: string }
interface State { hasError: boolean; message: string }

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, message: "" };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, message: error.message || "An unexpected error occurred." };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center py-16 text-center gap-3">
          <span className="text-2xl opacity-30">⚠</span>
          <p className="text-sm text-white/40 max-w-md">
            {this.props.fallbackLabel ?? "Something went wrong loading this section."}
          </p>
          <p className="font-mono text-xs text-white/20">{this.state.message}</p>
          <button
            onClick={() => this.setState({ hasError: false, message: "" })}
            className="mt-2 text-xs font-mono text-[#4AFA9A]/70 hover:text-[#4AFA9A] transition-colors"
          >
            Try Again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
