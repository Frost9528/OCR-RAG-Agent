import { FileText, Table2, Sigma, Image } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8100';
import { useDocument } from '@/contexts/DocumentContext';
import { useState } from 'react';
import { getDocumentBlocks, DocumentBlock } from '@/lib/api';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { ContentRenderer } from './ContentRenderer';

export function StatsCard() {
  const { stats, docId } = useDocument();
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [selectedType, setSelectedType] = useState<string>('');
  const [selectedBlockType, setSelectedBlockType] = useState<'text' | 'table' | 'image' | 'formula'>('text');
  const [blocks, setBlocks] = useState<DocumentBlock[]>([]);
  const [loading, setLoading] = useState(false);

  if (!stats) {
    return null;
  }

  const statsData = [
    {
      label: '文本',
      value: stats.text_blocks,
      icon: FileText,
      color: 'text-blue-700',
      bgColor: 'bg-blue-100/80',
      borderColor: 'hover:border-blue-400',
      type: 'text' as const
    },
    {
      label: '表格',
      value: stats.table_blocks,
      icon: Table2,
      color: 'text-emerald-700',
      bgColor: 'bg-emerald-100/80',
      borderColor: 'hover:border-emerald-400',
      type: 'table' as const
    },
    {
      label: '公式',
      value: stats.formula_blocks,
      icon: Sigma,
      color: 'text-violet-700',
      bgColor: 'bg-violet-100/80',
      borderColor: 'hover:border-violet-400',
      type: 'formula' as const
    },
    {
      label: '图像',
      value: stats.image_blocks,
      icon: Image,
      color: 'text-rose-700',
      bgColor: 'bg-rose-100/80',
      borderColor: 'hover:border-rose-400',
      type: 'image' as const
    },
  ];

  const handleCardClick = async (stat: typeof statsData[0]) => {
    if (stat.value === 0 || !docId) return;

    setSelectedType(stat.label);
    setSelectedBlockType(stat.type);
    setIsDialogOpen(true);
    setLoading(true);

    try {
      const response = await getDocumentBlocks(docId, stat.type);
      setBlocks(response.blocks);
    } catch (error) {
      console.error('Failed to load blocks:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="bg-gradient-to-br from-white to-slate-50 rounded-3xl p-4 border border-border shadow-sm">
        <h3 className="mb-3 text-sm font-semibold text-foreground">提取摘要</h3>
        <div className="grid grid-cols-2 gap-2">
          {statsData.map((stat) => {
            const Icon = stat.icon;
            return (
              <div
                key={stat.label}
                onClick={() => handleCardClick(stat)}
                className={`${stat.bgColor} ${stat.color} rounded-xl p-3 text-left transition-all duration-200 hover:scale-[1.03] hover:shadow-md border border-transparent ${stat.borderColor} ${
                  stat.value > 0 ? 'cursor-pointer' : 'opacity-40 cursor-not-allowed'
                }`}
              >
                <Icon className="h-4 w-4 mb-1" />
                <div className="text-xl mb-0.5">{stat.value}</div>
                <div className="text-xs opacity-80">{stat.label}</div>
              </div>
            );
          })}
        </div>
        <div className="mt-3 pt-3 border-t border-border/50">
          <div className="text-xs text-foreground/70">
            共 <span className="text-primary font-semibold">{stats.total_blocks}</span> 个内容块已索引
          </div>
        </div>
      </div>

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh] bg-background">
          <DialogHeader>
            <DialogTitle className="text-accent">
              {selectedType} - 提取内容
            </DialogTitle>
          </DialogHeader>
          <div className="overflow-y-auto max-h-[60vh] pr-4">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <div className="text-muted-foreground">加载中...</div>
              </div>
            ) : (
              <div className="space-y-4">
                {blocks.map((block, index) => (
                  <div
                    key={block.block_id}
                    className="bg-muted/20 rounded-lg p-4 border border-border/50"
                  >
                    <div className="text-sm text-muted-foreground mb-2 flex items-center justify-between">
                      <span>#{index + 1} - {block.block_label}</span>
                      {block.page_index !== undefined && (
                        <span className="text-xs bg-accent/20 text-accent px-2 py-0.5 rounded">
                          第 {block.page_index + 1} 页
                        </span>
                      )}
                    </div>
                    {block.image_path ? (
                      <div className="mt-2">
                        <img
                          src={`${API_BASE}${block.image_path}`}
                          alt={`Block ${block.block_id}`}
                          className="max-w-full h-auto rounded border border-border"
                        />
                      </div>
                    ) : (
                      <ContentRenderer
                        content={block.block_content}
                        type={selectedBlockType}
                        label={block.block_label}
                      />
                    )}
                  </div>
                ))}
                {blocks.length === 0 && !loading && (
                  <div className="text-center py-8 text-muted-foreground">
                    暂无内容
                  </div>
                )}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
