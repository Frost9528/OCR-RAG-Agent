import { Header } from './components/Header';
import { UploadPanel } from './components/UploadPanel';
import { ChatPanel } from './components/ChatPanel';
import { DocumentProvider } from './contexts/DocumentContext';
import { Toaster } from './components/ui/toaster';

export default function App() {
  return (
    <DocumentProvider>
      <div className="size-full flex flex-col bg-gradient-to-br from-violet-50/60 via-white to-sky-50/50">
        <Header />

        {/* Page Title Section */}
        <div className="px-6 pt-6 pb-2">
          <h1 className="text-2xl font-bold text-foreground">向文档提问</h1>
          <p className="text-sm text-muted-foreground mt-1">带引用追溯的智能问答</p>
        </div>

        <main className="flex-1 overflow-hidden">
          <div className="h-full grid grid-cols-1 lg:grid-cols-2 gap-6 px-6 pb-6">
            {/* Left Panel - 文档上传与索引 */}
            <div className="flex flex-col min-h-0 rounded-3xl bg-gradient-to-b from-white/90 to-violet-50/40 p-4 border border-violet-100/60 shadow-sm">
              <UploadPanel />
            </div>

            {/* Right Panel - 交互式问答 */}
            <div className="flex flex-col min-h-0 rounded-3xl bg-gradient-to-b from-white/90 to-sky-50/40 p-4 border border-sky-100/60 shadow-sm">
              <ChatPanel />
            </div>
          </div>
        </main>

        {/* Decorative Elements */}
        <div className="fixed inset-0 pointer-events-none overflow-hidden -z-10">
          <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-violet-400/12 rounded-full blur-[120px]" />
          <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-sky-400/12 rounded-full blur-[120px]" />
        </div>
      </div>
      <Toaster />
    </DocumentProvider>
  );
}
