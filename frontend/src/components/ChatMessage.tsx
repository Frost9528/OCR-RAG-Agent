import { useState } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8100';
import { ChevronDown, ChevronUp, Hash, MapPin } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';

interface Citation {
  id: number;
  source: string;
  page: number;
  snippet: string;
  content?: string;
  type: 'text' | 'table' | 'image' | 'formula';
  block_id?: number;
  bbox?: number[];
  image_path?: string;
  score?: number;
}

interface Message {
  content: string;
  isUser: boolean;
  citations?: Citation[];
}

interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const { content, isUser, citations = [] } = message;
  const [expandedCitation, setExpandedCitation] = useState<number | null>(null);

  // 渲染内容，支持 Markdown 并处理引用标记
  const renderContent = () => {
    // 替换 【数字】 为占位符，稍后用组件替换
    const processedContent = content.replace(/【(\d+)】/g, (match, id) => {
      return `<cite data-id="${id}">[${id}]</cite>`;
    });

    return (
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw]}
        components={{
          // 自定义渲染引用标记
          cite: ({ node, ...props }: any) => {
            // rehype-raw v10 经 hast 管道后 data-id 可能变为 dataId
            const citationId = parseInt(props['data-id'] || props['dataId'] || props.dataId || '0');
            return (
              <sup
                onClick={() => setExpandedCitation(expandedCitation === citationId ? null : citationId)}
                className="inline-flex items-center justify-center min-w-[20px] h-5 px-1.5 ml-0.5 text-xs bg-cyan-500 text-white rounded-full cursor-pointer hover:bg-cyan-600 transition-colors"
              >
                {citationId}
              </sup>
            );
          },
          // 段落样式
          p: ({ node, ...props }) => <p className="mb-2 last:mb-0" {...props} />,
          // 列表样式
          ul: ({ node, ...props }) => <ul className="list-disc list-inside mb-2 space-y-1" {...props} />,
          ol: ({ node, ...props }) => <ol className="list-decimal list-inside mb-2 space-y-1" {...props} />,
          li: ({ node, ...props }) => <li className="ml-2" {...props} />,
          // 代码块样式
          code: ({ node, inline, ...props }: any) =>
            inline ? (
              <code className="bg-muted px-1.5 py-0.5 rounded text-accent text-xs" {...props} />
            ) : (
              <code className="block bg-muted p-3 rounded-lg my-2 text-sm overflow-x-auto" {...props} />
            ),
          // 强调样式
          strong: ({ node, ...props }) => <strong className="font-bold text-primary" {...props} />,
          em: ({ node, ...props }) => <em className="italic text-muted-foreground" {...props} />,
          // 链接样式
          a: ({ node, ...props }) => (
            <a className="text-accent hover:text-accent/80 underline" target="_blank" rel="noopener noreferrer" {...props} />
          ),
        }}
      >
        {processedContent}
      </ReactMarkdown>
    );
  };

  if (isUser) {
    return (
      <div className="flex justify-end mb-4">
        <div className="max-w-[70%] bg-gradient-to-r from-purple-600 to-purple-700 text-white rounded-2xl rounded-tr-sm px-4 py-3 shadow-lg">
          <div className="text-sm leading-relaxed whitespace-pre-wrap">{content}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="mb-6">
      {/* 助手消息气泡 */}
      <div className="flex justify-start mb-2">
        <div className="max-w-[85%] bg-white border border-border text-foreground rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
          <div className="text-sm leading-relaxed">
            {renderContent()}
          </div>
        </div>
      </div>

      {/* 展开的引用卡片 */}
      {expandedCitation !== null && citations.find(c => c.id === expandedCitation) && (
        <div className="ml-4 mt-2 bg-blue-50 border border-blue-200 rounded-xl p-4 max-w-[80%] animate-in fade-in slide-in-from-top-2 duration-200">
          {(() => {
            const citation = citations.find(c => c.id === expandedCitation)!;
            return (
              <>
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1 space-y-2">
                    {/* 来源信息 */}
                    <div className="flex items-center gap-2 text-xs">
                      <span className="text-primary font-medium">
                        {citation.source} - 第 {citation.page} 页
                      </span>
                      <span className="text-muted-foreground">
                        类型: {citation.type === 'text' ? '文本' : citation.type === 'table' ? '表格' : citation.type === 'formula' ? '公式' : '图像'}
                      </span>
                    </div>

                    {/* Block ID 和相关性 */}
                    <div className="flex items-center gap-3 text-xs text-muted-foreground">
                      {citation.block_id !== undefined && (
                        <span className="flex items-center gap-1">
                          <Hash className="h-3 w-3" />
                          Block {citation.block_id}
                        </span>
                      )}
                      {citation.score !== undefined && (
                        <span className="text-accent font-medium">
                          相关性: {(citation.score * 100).toFixed(1)}%
                        </span>
                      )}
                    </div>

                    {/* 位置信息 */}
                    {citation.bbox && citation.bbox.length === 4 && (
                      <div className="flex items-center gap-1 text-xs text-muted-foreground/70">
                        <MapPin className="h-3 w-3" />
                        位置: [{citation.bbox.join(', ')}]
                      </div>
                    )}
                  </div>

                  {/* 关闭按钮 */}
                  <button
                    onClick={() => setExpandedCitation(null)}
                    className="text-muted-foreground hover:text-primary transition-colors ml-2 flex-shrink-0"
                  >
                    <ChevronUp className="h-4 w-4" />
                  </button>
                </div>

                {/* 引用内容 */}
                <div className="bg-white rounded-lg p-3 text-sm text-foreground leading-relaxed border border-border">
                  {/* 如果有图片路径，显示图片 */}
                  {citation.image_path && (
                    <div className="mb-3">
                      <img
                        src={`${API_BASE}${citation.image_path}`}
                        alt={`引用 ${citation.id}`}
                        className="max-w-full h-auto rounded border border-slate-600"
                      />
                    </div>
                  )}

                  {/* 显示内容 */}
                  {citation.type === 'table' ? (
                    <div
                      className="overflow-x-auto"
                      dangerouslySetInnerHTML={{ __html: citation.content || citation.snippet }}
                    />
                  ) : (
                    <div className="whitespace-pre-wrap">
                      {citation.content || citation.snippet}
                    </div>
                  )}
                </div>
              </>
            );
          })()}
        </div>
      )}
    </div>
  );
}
