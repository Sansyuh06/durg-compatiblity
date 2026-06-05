"use client";
export default function LoadingBar() {
  return (
    <div className="fixed top-0 left-0 right-0 z-[100] h-[2px]">
      <div className="h-full bg-[#4AFA9A] animate-loading-bar rounded-full" />
      <style jsx>{`
        @keyframes loading-bar {
          0% { width: 0%; margin-left: 0; }
          50% { width: 60%; margin-left: 20%; }
          100% { width: 0%; margin-left: 100%; }
        }
        .animate-loading-bar { animation: loading-bar 1.5s ease infinite; }
      `}</style>
    </div>
  );
}
